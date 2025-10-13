def quota_share(exposure: float, cession_PCT: float, limit: float = None) -> float:
    if not 0 <= cession_PCT <= 1:
        raise ValueError("Cession rate must be between 0 and 1")

    if limit is not None and limit < 0:
        raise ValueError("Limit must be positive if specified")

    ceded_amount = exposure * cession_PCT

    if limit is not None:
        return min(ceded_amount, limit)

    return ceded_amount
