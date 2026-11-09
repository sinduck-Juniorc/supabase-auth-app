from collections import Counter
from dataclasses import dataclass, field
import math
from .events import EventQueue
from .energy import EnergyLedger
from .packet import make_packet
from .radio import Radio, field_uniform
from .topologies import environment
from policies.combined import Policy, Observation
from policies.chebyshev import QualityModel


@dataclass
class Node:
    node_id: int
    role: str
    energy: EnergyLedger
    policy: Policy
    battery: float
    quality: float
    scan_on: bool = False
    scan_end: float = 0
    channel: int = 37
    scan_sequence: int = 0
    adv_sequence: int = 0
    generate_sequence: int = 0
    sleep_token: int = 0
    current: object = None
    cache: dict = field(default_factory=dict)
    seen: dict = field(default_factory=dict)
    parent: object = None
    first_neighbor: object = None
    first_packet: object = None


@dataclass
class Frame:
    sender: int
    channel: int
    start: float
    end: float
    packet: object
    battery: float
    receivers: set = field(default_factory=set)
    collided: set = field(default_factory=set)


class Simulation:
    def __init__(self, config, policy, seed):
        self.config, self.policy, self.seed = config, policy, seed
        self.env = environment(config, seed)
        self.radio = Radio(config, self.env, seed)
        self.queue = EventQueue()
        self.nodes = []
        model = QualityModel() if policy in ("combined", "cheb_only", "lut") else None
        for i in range(config["nodes"]):
            self.nodes.append(Node(i, self.env["roles"][i], EnergyLedger(config["energy"]),
                                   Policy(policy, seed, i, config, model),
                                   self.env["battery"][i], self.env["quality"][i]))
        self.active = {37: [], 38: [], 39: []}
        self.scanners = {37: set(), 38: set(), 39: set()}
        self.requests = []
        self.pending = {i: [] for i in range(config["nodes"])}
        self.event_counts = Counter()
        self.counters = Counter()
        self.relay_load = Counter()
        self.delivery_hops = []
        self.audit = []

    def fresh(self, node, time):
        return (node.current is not None and node.current.valid(time) and
                time - node.current.created_at <= self.config["max_info_age_s"])

    def candidates(self, node, time):
        return [c for c in node.cache.values() if time - c.last_seen <= self.config["cache_s"] and
                time < c.expires_at and c.hops < self.config["max_hops"]]

    def choose(self, node, time):
        candidates = self.candidates(node, time)
        node.parent = node.policy.choose(candidates, time)
        node.energy.cpu(node.policy.cpu_cost(len(candidates)))
        if node.parent is not None and node.parent not in {c.node_id for c in candidates}:
            raise AssertionError("미발견 후보 선택")
        if not candidates:
            self.counters["exploration_fallbacks"] += 1
        if self.config.get("audit", False):
            self.audit.append({"time": time, "node": node.node_id, "parent": node.parent,
                               "observed": sorted(c.node_id for c in candidates)})

    def schedule(self, node, time):
        return node.policy.schedule(self.fresh(node, time), bool(self.pending[node.node_id]),
                                    bool(self.candidates(node, time)))

    def sleep_later(self, node, time):
        if not node.scan_on and not node.energy.tx and not node.energy.rx:
            node.energy.awake = True
            node.sleep_token += 1
            self.queue.push(time + self.config["wake_guard_s"], "sleep", (node.node_id, node.sleep_token))

    def run(self):
        config = self.config
        for node in self.nodes:
            self.queue.push(self.env["scan_phases"][node.node_id], "scan_start", node.node_id)
            self.queue.push(self.env["adv_phases"][node.node_id], "adv", node.node_id)
            if node.role == "Donor":
                self.queue.push(self.env["gnss_phases"][node.node_id], "generate", node.node_id)
        for time, node_id in self.env["traffic"]:
            self.queue.push(time, "request", node_id)
        duration = config["duration_s"]
        while self.queue:
            event = self.queue.pop()
            if event.time > duration:
                break
            self.event_counts[event.kind] += 1
            getattr(self, "on_" + event.kind)(event.time, event.data)
        for node in self.nodes:
            node.energy.account(duration)
        return self

    def on_scan_start(self, time, node_id):
        node = self.nodes[node_id]
        node.energy.account(time)
        node.energy.scanning = node.scan_on = True
        node.energy.awake = True
        node.sleep_token += 1
        node.channel = 37 + node.scan_sequence % 3
        node.scan_sequence += 1
        window, _ = self.schedule(node, time)
        node.scan_end = time + window
        self.scanners[node.channel].add(node_id)
        self.choose(node, time)
        self.queue.push(node.scan_end, "scan_end", node_id)
        self.queue.push(time + self.config["scan_interval_s"], "scan_start", node_id)

    def on_scan_end(self, time, node_id):
        node = self.nodes[node_id]
        node.energy.account(time)
        node.energy.scanning = node.scan_on = False
        self.scanners[node.channel].discard(node_id)
        self.sleep_later(node, time)

    def on_sleep(self, time, data):
        node_id, token = data
        node = self.nodes[node_id]
        if token == node.sleep_token and not node.scan_on and not node.energy.tx and not node.energy.rx:
            node.energy.account(time)
            node.energy.awake = False

    def on_adv(self, time, node_id):
        node = self.nodes[node_id]
        # 생성 시각이 다른 광고 채널도 동일 packet snapshot을 사용한다.
        packet = node.current if node.current is not None and node.current.valid(time) else None
        for index, channel in enumerate((37, 38, 39)):
            self.queue.push(time + index * self.config["channel_spacing_s"], "tx_start", (node_id, channel, packet))
        _, interval = self.schedule(node, time)
        # BLE advDelay는 환경 키로, random 정책의 추가 backoff는 정책 RNG로 분리.
        delay = .01 * field_uniform(self.seed, 81, node_id, node.adv_sequence)
        node.adv_sequence += 1
        self.queue.push(time + interval + delay, "adv", node_id)

    def on_tx_start(self, time, data):
        sender, channel, packet = data
        node = self.nodes[sender]
        node.energy.account(time)
        node.energy.tx += 1
        node.sleep_token += 1
        end = time + self.config["airtime_s"]
        reported_battery = max(0., node.battery - node.energy.total() / self.config["battery_capacity_j"])
        frame = Frame(sender, channel, time, end, packet, reported_battery)
        for receiver in tuple(self.scanners[channel]):
            target = self.nodes[receiver]
            if receiver == sender or target.energy.tx or target.scan_end < end:
                continue
            if self.radio.detectable(sender, receiver, time):
                target.energy.account(time)
                target.energy.rx += 1
                frame.receivers.add(receiver)
        # 송신 중인 자기 자신은 다른 광고 채널도 수신할 수 없다.
        for active_channel in self.active.values():
            for previous in active_channel:
                if sender in previous.receivers:
                    self.queue.push(time, "collision", (previous, sender))
        for previous in self.active[channel]:
            for receiver in previous.receivers:
                if receiver == sender or self.radio.detectable(sender, receiver, time):
                    self.queue.push(time, "collision", (previous, receiver))
            for receiver in frame.receivers:
                if receiver == previous.sender or self.radio.detectable(previous.sender, receiver, time):
                    self.queue.push(time, "collision", (frame, receiver))
        self.active[channel].append(frame)
        self.counters["tx_frames"] += 1
        self.queue.push(end, "tx_end", frame)

    def on_collision(self, time, data):
        frame, receiver = data
        if receiver not in frame.collided:
            frame.collided.add(receiver)
            self.counters["collided_receptions"] += 1

    def on_tx_end(self, time, frame):
        node = self.nodes[frame.sender]
        node.energy.account(time)
        node.energy.tx -= 1
        self.active[frame.channel].remove(frame)
        self.sleep_later(node, time)
        for receiver in frame.receivers:
            target = self.nodes[receiver]
            target.energy.account(time)
            target.energy.rx -= 1
            self.sleep_later(target, time)
            if receiver not in frame.collided and self.radio.success(frame.sender, receiver, frame.start, frame.channel):
                self.queue.push(time, "receive", (receiver, frame))

    def on_receive(self, time, data):
        receiver, frame = data
        node = self.nodes[receiver]
        self.counters["received_beacons"] += 1
        if node.first_neighbor is None:
            node.first_neighbor = time
        packet = frame.packet
        if packet is None or not packet.valid(time):
            return
        rssi = self.radio.signal(frame.sender, receiver, frame.start)
        # 수신 RSSI에서 만든 보정 전 링크 추정값; 내부 링크 확률 행렬은 사용하지 않는다.
        p_rx = 1 / (1 + math.exp(-max(-30., min(30., (rssi + 91) / 3))))
        node.cache[frame.sender] = Observation(frame.sender, time, rssi, frame.battery,
                                               packet.created_at, packet.expires_at,
                                               packet.hop_count, p_rx, packet.quality_code / 255)
        # 방송 PHY의 수신 비용은 위에서 이미 계상. 데이터 채택만 사전에 고른 parent로 제한.
        if frame.sender != node.parent:
            return
        self.accept(node, packet, time)

    def accept(self, node, packet, time):
        if not packet.valid(time):
            self.counters["invalid_packets"] += 1
            return False
        if packet.packet_id in node.seen:
            self.counters["duplicates_suppressed"] += 1
            return False
        forwarded = packet.forward()
        if forwarded is None:
            self.counters["hop_limited"] += 1
            return False
        node.seen[packet.packet_id] = packet.expires_at
        self.queue.push(packet.expires_at, "expire", (node.node_id, packet.packet_id))
        self.counters["accepted_packets"] += 1
        self.delivery_hops.append(forwarded.hop_count)
        if node.first_packet is None:
            node.first_packet = time
        self.fulfill(node.node_id, forwarded, time)
        # relay budget는 세대별 packet당 1회 채택; 광고 반복은 중복 억제와 별도 집계.
        delay = self.config["relay_backoff_s"] * node.policy.rng.uniform(.5, 1.5)
        self.queue.push(time + delay, "relay", (node.node_id, forwarded))
        return True

    def on_relay(self, time, data):
        node_id, packet = data
        node = self.nodes[node_id]
        if not packet.valid(time):
            return
        if node.role == "Donor":
            return
        if node.current is None or (packet.created_at, -packet.hop_count, packet.packet_id) > (
                node.current.created_at, -node.current.hop_count, node.current.packet_id):
            node.current = packet
            self.relay_load[node_id] += 1
            self.counters["relay_updates"] += 1

    def on_generate(self, time, node_id):
        node = self.nodes[node_id]
        node.energy.account(time)
        node.energy.gnss = True
        node.generate_sequence += 1
        node.current = make_packet(node_id, node.generate_sequence, time, self.config["packet_lifetime_s"],
                                   self.config["max_hops"], node.quality)
        node.seen[node.current.packet_id] = node.current.expires_at
        self.queue.push(node.current.expires_at, "expire", (node_id, node.current.packet_id))
        self.queue.push(time + self.config["gnss_active_s"], "gnss_end", node_id)
        self.queue.push(time + self.config["generation_period_s"], "generate", node_id)

    def on_gnss_end(self, time, node_id):
        node = self.nodes[node_id]
        node.energy.account(time)
        node.energy.gnss = False

    def on_expire(self, time, data):
        node_id, packet_id = data
        node = self.nodes[node_id]
        node.seen.pop(packet_id, None)
        if node.current is not None and node.current.packet_id == packet_id:
            node.current = None
            self.counters["expired_stored_packets"] += 1

    def on_request(self, time, node_id):
        request = {"request_id": len(self.requests), "node_id": node_id, "created_s": time,
                   "deadline_s": time + self.config["deadline_s"], "delivered_s": None,
                   "latency_s": None, "hops": None, "packet_id": None}
        self.requests.append(request)
        self.pending[node_id].append(request)
        self.queue.push(request["deadline_s"], "request_deadline", (node_id, request["request_id"]))
        node = self.nodes[node_id]
        if self.fresh(node, time):
            self.fulfill(node_id, node.current, time)

    def on_request_deadline(self, time, data):
        node_id, request_id = data
        self.pending[node_id] = [r for r in self.pending[node_id] if r["request_id"] != request_id]

    def fulfill(self, node_id, packet, time):
        if time - packet.created_at > self.config["max_info_age_s"] or not packet.valid(time):
            return
        remaining = []
        for request in self.pending[node_id]:
            if time <= request["deadline_s"]:
                request.update(delivered_s=time, latency_s=time - request["created_s"],
                               hops=packet.hop_count, packet_id=packet.packet_id)
            else:
                remaining.append(request)
        self.pending[node_id] = remaining
