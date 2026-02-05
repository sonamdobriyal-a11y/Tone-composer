import numpy as np


def top_p_sampling(probs, top_p: float = 0.9, return_probs: bool = False):
    """Keep only the top tokens whose cumulative probability mass stays within top_p."""
    sorted_indices = np.argsort(probs)[::-1]
    sorted_probs = probs[sorted_indices]
    cumulative = np.cumsum(sorted_probs)
    mask = cumulative <= top_p
    if not np.any(mask):
        mask[0] = True

    selected_indices = sorted_indices[mask]
    selected_probs = sorted_probs[mask]

    if return_probs:
        return selected_probs, selected_indices

    filtered = np.zeros_like(probs)
    filtered[selected_indices] = selected_probs
    return filtered


def temperature_sampling(probs, temperature: float = 1.0):
    """Sample an index after applying optional temperature scaling."""
    if isinstance(probs, tuple):
        selected_probs, selected_indices = probs
        selected_probs = np.array(selected_probs, dtype=float)
        selected_indices = np.array(selected_indices, dtype=int)
    else:
        selected_probs = np.array(probs, dtype=float)
        selected_indices = np.arange(len(selected_probs))

    positive = selected_probs > 0
    if not np.any(positive):
        selected_probs = np.ones_like(selected_probs, dtype=float)
        positive = np.ones_like(selected_probs, dtype=bool)

    selected_probs = selected_probs[positive]
    selected_indices = selected_indices[positive]

    if temperature != 1.0:
        logits = np.log(selected_probs + 1e-12) / temperature
        selected_probs = np.exp(logits)

    selected_probs = selected_probs / selected_probs.sum()
    return np.random.choice(selected_indices, p=selected_probs)
