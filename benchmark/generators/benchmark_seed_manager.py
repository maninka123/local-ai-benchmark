import hashlib
def task_seed(seed, name):
    return int(hashlib.sha256(f'{seed}:{name}'.encode()).hexdigest()[:8],16)
