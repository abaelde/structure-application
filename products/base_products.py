def quote_share(exposure: float, cession_rate: float) -> float:
    if not 0 <= cession_rate <= 1:
        raise ValueError("Cession rate must be between 0 and 1")
    
    return exposure * cession_rate


def excess_of_loss(exposure: float, priority: float, limit: float) -> float:
    if priority < 0 or limit < 0:
        raise ValueError("Priority and limit must be positive")
    
    if exposure <= priority:
        return 0.0
    
    amount_above_priority = exposure - priority
    return min(amount_above_priority, limit)

