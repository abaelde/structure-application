"""
Exceptions spécifiques au domaine de la réassurance.
"""


class CurrencyMismatchError(Exception):
    """Exception levée quand la devise de la police ne correspond pas à la devise principale du programme"""
    
    def __init__(self, policy_currency: str, program_currency: str, policy_id: str = None):
        self.policy_currency = policy_currency
        self.program_currency = program_currency
        self.policy_id = policy_id
        super().__init__(
            f"Currency mismatch: Policy currency '{policy_currency}' "
            f"does not match program main currency '{program_currency}'"
            + (f" (Policy: {policy_id})" if policy_id else "")
        )


class ExposureCalculationError(Exception):
    """Exception levée lors d'erreurs de calcul d'exposition"""
    pass
