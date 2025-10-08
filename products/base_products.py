def quota_share(exposure: float, cession_PCT: float, limit: float = None) -> float:
    if not 0 <= cession_PCT <= 1:
        raise ValueError("Cession rate must be between 0 and 1")

    if limit is not None and limit < 0:
        raise ValueError("Limit must be positive if specified")

    ceded_amount = exposure * cession_PCT

    if limit is not None:
        return min(ceded_amount, limit)

    return ceded_amount


def excess_of_loss(
    exposure: float, attachment_point_100: float, limit_100: float
) -> float:
    if attachment_point_100 < 0 or limit_100 < 0:
        raise ValueError(
            "attachment_point_100 and limit_100 must be positive"
        )

    if exposure <= attachment_point_100:
        return 0.0

    amount_above_priority = exposure - attachment_point_100
    return min(amount_above_priority, limit_100)
