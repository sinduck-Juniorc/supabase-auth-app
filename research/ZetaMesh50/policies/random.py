from .combined import Policy


def create(seed, node, config):
    return Policy("random", seed, node, config)
