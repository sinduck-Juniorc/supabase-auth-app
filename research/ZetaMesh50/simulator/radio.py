import math
import numpy as np


def field_uniform(seed, *keys):
    """호출 횟수와 무관한 난수장. 정수 키와 시각으로 환경을 공통화한다."""
    mask = (1 << 64) - 1
    value = (seed + 0x9E3779B97F4A7C15) & mask
    for key in keys:
        value = (value ^ (int(key) + 0x9E3779B97F4A7C15)) & mask
        value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & mask
        value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & mask
        value ^= value >> 31
    return (value >> 11) / float(1 << 53)


class Radio:
    def __init__(self, config, env, seed):
        self.config, self.seed = config, seed
        positions = env["positions"]
        distance = np.linalg.norm(positions[:, :, None, :] - positions[:, None, :, :], axis=-1)
        rng = np.random.default_rng(np.random.SeedSequence([seed, 9201]))
        shadow = rng.normal(0, config["shadow_sigma_db"], distance.shape)
        self.rssi = (config["tx_power_dbm"] - 44 - 10 * config["pathloss_exponent"] *
                     np.log10(np.maximum(distance, 1)) - env["blocked"][None] *
                     config["nlos_loss_db"] + shadow)
        self.probability = 1 / (1 + np.exp(-np.clip((self.rssi + 91) / 3, -30, 30)))
        self.probability[distance > config["max_range_m"]] = 0

    def signal(self, sender, receiver, time):
        return float(self.rssi[min(int(time), len(self.rssi) - 1), sender, receiver])

    def success(self, sender, receiver, time, channel):
        epoch = min(int(time), len(self.rssi) - 1)
        if field_uniform(self.seed, 71, int(time / .02), channel) < self.config["external_interference"]:
            return False
        return field_uniform(self.seed, 72, sender, receiver, int(round(time * 1e6)), channel) < self.probability[epoch, sender, receiver]

    def detectable(self, sender, receiver, time):
        return self.signal(sender, receiver, time) >= self.config["sensitivity_dbm"]
