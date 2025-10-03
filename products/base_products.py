def quote_share(exposure: float, cession_rate: float) -> float:
    if not 0 <= cession_rate <= 1:
        raise ValueError("Cession rate must be between 0 and 1")
    
    return exposure * cession_rate


def excess_of_loss(exposure: float, attachment_point_100: float, limit_occurrence_100: float) -> float:
    if attachment_point_100 < 0 or limit_occurrence_100 < 0:
        raise ValueError("attachment_point_100 and limit_occurrence_100 must be positive")
    
    if exposure <= attachment_point_100:
        return 0.0
    
    amount_above_priority = exposure - attachment_point_100
    return min(amount_above_priority, limit_occurrence_100)

