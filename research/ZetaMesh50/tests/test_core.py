from dataclasses import asdict, replace
from pathlib import Path
import math
import numpy as np
import pytest
import yaml
from simulator.events import EventQueue
from simulator.energy import EnergyLedger
from simulator.packet import make_packet, decode_packet
from simulator.radio import field_uniform, Radio
from simulator.network import Simulation
from simulator.metrics import metrics
from simulator.topologies import environment
from policies.zeta import rank_probabilities
from policies.chebyshev import clenshaw, normalize, QualityModel
from policies.combined import Policy, Observation, POLICIES

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def config():
    value = yaml.safe_load((ROOT / "configs/50nodes_dense.yaml").read_text(encoding="utf-8"))
    value.update(nodes=10, duration_s=25., warmup_s=2., request_period_s=4., deadline_s=5.)
    return value


@pytest.mark.parametrize("size", [0, 1, 2, 50, 500])
def test_zeta_normalized_and_exploration(size):
    p = rank_probabilities(size, exponent=8, exploration=.12)
    if size:
        assert p.sum() == pytest.approx(1)
        assert p.min() >= .12 / size
        assert np.all(np.diff(p) <= 0)
    else:
        assert len(p) == 0


def test_zeta_invalid():
    for size, exponent, exploration in [(-1, 1, .1), (3, float("nan"), .1), (3, 1, 0)]:
        with pytest.raises(ValueError):
            rank_probabilities(size, exponent, exploration)


def test_clenshaw_reference():
    rng = np.random.default_rng(123)
    for degree in (3, 5, 7):
        coefficients = rng.normal(size=degree + 1)
        for x in np.linspace(-1, 1, 31):
            assert clenshaw(x, coefficients) == pytest.approx(np.polynomial.chebyshev.chebval(x, coefficients), abs=1e-12)


def test_normalization_missing_and_bounds():
    x = normalize([float("nan"), float("inf"), -100, 1000, None, -.2])
    assert np.all(np.isfinite(x))
    assert np.all(np.abs(x) <= 1)


def test_quality_scalar_vector_agree():
    model = QualityModel()
    features = np.array([[-65., .6, 3., 2., .8, .9], [-90., .2, 20., 4., .1, .5]])
    for degree in (3, 5, 7):
        assert np.array([model.predict(x, degree) for x in features]) == pytest.approx(model.predict(features, degree))


def test_packet_version_checksum_hops_expiry():
    packet = make_packet(0, 0, 1., 10., 2, .8)
    assert packet.valid(1)
    assert not packet.valid(.999)
    assert not packet.valid(11)
    assert packet.forward().forward().hop_count == 2
    assert packet.forward().forward().forward() is None
    assert not replace(packet, version=2).valid(2)
    assert not replace(packet, quality_code=200).valid(2)
    assert decode_packet(asdict(packet), 2) == packet
    for invalid in ({}, {**asdict(packet), "extra": 1}, [], None, {**asdict(packet), "created_at": "bad"}):
        assert decode_packet(invalid, 2) is None


def test_energy_exclusive_states_and_incremental_modules(config):
    ledger = EnergyLedger(config["energy"])
    ledger.account(1)  # sleep
    ledger.scanning = True
    ledger.gnss = True
    ledger.account(3)  # scan 2초
    ledger.rx = 1
    ledger.account(4)  # rx 1초, scan 중복 없음
    ledger.tx = 1
    ledger.account(5)  # tx가 rx에 우선
    ledger.cpu(.002)
    assert sum(ledger.seconds[k] for k in ("tx", "rx", "scan", "idle", "sleep")) == 5
    e = config["energy"]
    expected = e["voltage_v"] * (e["sleep_a"] + 2 * e["scan_a"] + e["rx_a"] + e["tx_a"] +
                                   4 * e["gnss_a"] + .002 * e["cpu_increment_a"])
    assert ledger.total() == pytest.approx(expected)


@pytest.mark.parametrize("policy", POLICIES)
def test_only_observed_candidates_and_fallback(config, policy):
    model = QualityModel() if policy in ("combined", "cheb_only", "lut") else None
    obj = Policy(policy, 2, 0, config, model)
    assert obj.choose([], 2) is None
    c = Observation(7, 1., -60., .8, 0., 20., 1, .9, .9)
    assert obj.choose([c], 2) == 7
    assert obj.choose([c], 10) is None
    assert obj.choose([replace(c, expires_at=1.5)], 2) is None
    assert obj.schedule(True, False, False) == (config["base_scan_window_s"], pytest.approx(config["base_adv_s"], rel=.21))


def test_environment_independent_of_policy_random_calls(config):
    a = environment(config, 345)
    policy = Policy("random", 345, 1, config)
    for _ in range(100):
        policy.rng.random()
    b = environment(config, 345)
    assert a["fingerprint"] == b["fingerprint"]
    assert a["fingerprint"] != environment(config, 346)["fingerprint"]
    before = field_uniform(345, 1, 2, 3)
    for key in range(100):
        field_uniform(345, key)
    assert before == field_uniform(345, 1, 2, 3)


@pytest.mark.parametrize("policy", ["fixed", "random", "combined"])
def test_identical_seed_reproducible_and_energy_conserved(config, policy):
    config["audit"] = True
    a = Simulation(config, policy, 404).run()
    b = Simulation(config, policy, 404).run()
    ma, nodes = metrics(a)
    mb, _ = metrics(b)
    assert ma == mb
    assert a.requests == b.requests
    assert a.audit == b.audit
    assert all(r["parent"] is None or r["parent"] in r["observed"] for r in a.audit)
    assert ma["energy_j"] == pytest.approx(sum(n["energy_j"] for n in nodes))
    assert ma["energy_j"] == pytest.approx(ma["donor_j"] + ma["relay_j"] + ma["seeker_j"])
    assert all(n["radio_state_seconds"] == pytest.approx(config["duration_s"]) for n in nodes)


def test_duplicate_ttl_and_expiry_in_network(config):
    sim = Simulation(config, "fixed", 20)
    node = sim.nodes[0]
    packet = make_packet(8, 0, 0., 10., 1, .9)
    assert sim.accept(node, packet, 1)
    assert not sim.accept(node, packet, 2)
    assert sim.counters["duplicates_suppressed"] == 1
    assert not sim.accept(sim.nodes[1], packet.forward(), 2)
    assert not sim.accept(sim.nodes[1], packet, 10)
    sim.on_relay(2, (node.node_id, packet.forward()))
    sim.on_expire(10, (node.node_id, packet.packet_id))
    assert node.current is None


def test_three_node_relay_and_channel_collisions(config):
    config.update(nodes=3, duration_s=45., deadline_s=8., max_range_m=65., external_interference=0.,
                  nlos_probability=0., shadow_sigma_db=0., generation_period_s=8.)
    sim = Simulation(config, "fixed", 81)
    sim.env["positions"][:] = np.array([[0., 0.], [50., 0.], [100., 0.]])
    sim.env["roles"][:] = ["Donor", "Relay", "Seeker"]
    for node, role in zip(sim.nodes, sim.env["roles"]):
        node.role = role
    sim.env["traffic"] = [(10., 2), (20., 2), (30., 2)]
    sim.radio = Radio(config, sim.env, 81)
    sim.run()
    assert sim.radio.probability[0, 0, 2] == 0
    assert any(r["hops"] == 2 for r in sim.requests)
    assert sim.counters["relay_updates"] > 0
    # 직접 동시 송신을 주입해 동일 채널의 겹침이 충돌 이벤트를 만드는지 확인.
    collision_sim = Simulation(config, "fixed", 82)
    collision_sim.env["positions"][:] = np.array([[0., 0.], [1., 0.], [2., 0.]])
    collision_sim.radio = Radio(config, collision_sim.env, 82)
    receiver = collision_sim.nodes[2]
    receiver.scan_on = True
    receiver.scan_end = 1.
    collision_sim.scanners[37].add(2)
    collision_sim.on_tx_start(0., (0, 37, None))
    collision_sim.on_tx_start(.0001, (1, 37, None))
    while collision_sim.queue:
        event = collision_sim.queue.pop()
        getattr(collision_sim, "on_" + event.kind)(event.time, event.data)
    assert collision_sim.counters["collided_receptions"] == 2
    assert collision_sim.counters["received_beacons"] == 0


def test_channel_and_full_window_required(config):
    sim = Simulation(config, "fixed", 12)
    node = sim.nodes[1]
    node.scan_on, node.scan_end, node.channel = True, .0001, 38
    sim.scanners[38].add(1)
    sim.on_tx_start(0, (0, 37, None))
    sim.on_tx_start(0, (2, 38, None))
    assert all(1 not in frame.receivers for frames in sim.active.values() for frame in frames)
