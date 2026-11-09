from .combined import Policy


def create(seed, node, config):
    return Policy("greedy", seed, node, config)
