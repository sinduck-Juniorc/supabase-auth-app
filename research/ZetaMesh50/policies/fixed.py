from .combined import Policy


def create(seed, node, config):
    return Policy("fixed", seed, node, config)
