from collections import defaultdict
import numpy as np


def quantile(values, probability):
    return float(np.quantile(values, probability)) if values else float("nan")


def metrics(sim):
    components = defaultdict(float)
    roles = defaultdict(float)
    node_rows = []
    for node in sim.nodes:
        values = node.energy.components()
        for component, value in values.items():
            components[component] += value
        roles[node.role] += sum(values.values())
        node_rows.append({"node_id": node.node_id, "role": node.role, **values,
                          "energy_j": sum(values.values()), "relay_updates": sim.relay_load[node.node_id],
                          "radio_state_seconds": sum(node.energy.seconds[k] for k in ("tx", "rx", "scan", "idle", "sleep")),
                          "cpu_assumed_seconds": node.energy.cpu_seconds})
    successes = [r["latency_s"] for r in sim.requests if r["delivered_s"] is not None]
    discovery = [n.first_neighbor for n in sim.nodes if n.first_neighbor is not None]
    first_packet = [n.first_packet for n in sim.nodes if n.first_packet is not None]
    request_count = len(sim.requests)
    result = {"scenario": sim.config["scenario"], "policy": sim.policy, "seed": sim.seed,
              "nodes": len(sim.nodes), "duration_s": sim.config["duration_s"],
              "environment_fingerprint": sim.env["fingerprint"], "events": sum(sim.event_counts.values()),
              "energy_j": sum(components.values()), **components,
              **{role.lower() + "_j": roles[role] for role in ("Donor", "Relay", "Seeker")},
              "requests": request_count, "successes": len(successes),
              "success_rate": len(successes) / request_count if request_count else float("nan"),
              "latency_p50_s": quantile(successes, .5), "latency_p95_s": quantile(successes, .95),
              "penalized_latency_p95_s": quantile([r["latency_s"] if r["latency_s"] is not None else
                                                     sim.config["deadline_s"] for r in sim.requests], .95),
              "discovery_p50_s": quantile(discovery, .5), "discovery_p95_s": quantile(discovery, .95),
              "first_packet_p95_s": quantile(first_packet, .95),
              "neighbor_discovery_failure_rate": 1 - len(discovery) / len(sim.nodes),
              "request_expiration_rate": 1 - len(successes) / request_count if request_count else float("nan"),
              "mean_accepted_hops": float(np.mean(sim.delivery_hops)) if sim.delivery_hops else float("nan"),
              "max_node_relay_load": max(sim.relay_load.values(), default=0), **sim.counters}
    return result, node_rows
