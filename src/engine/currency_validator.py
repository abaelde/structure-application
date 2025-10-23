"""
Service de validation de cohérence des devises entre polices et programmes.
"""

from typing import Optional, List
from src.domain.policy import Policy
from src.domain.program import Program
from src.domain.condition import Condition


class CurrencyValidator:
    """Service de validation de cohérence des devises"""
    
    @staticmethod
    def validate_policy_currency(
        policy: Policy, 
        program: Program, 
        matched_condition: Optional[Condition] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Valide la cohérence de devise entre une police et un programme.
        
        Args:
            policy: Police à valider
            program: Programme avec devise principale
            matched_condition: Condition matchée (optionnelle)
        
        Returns:
            (is_valid, error_reason)
        """
        # main_currency est maintenant obligatoire, pas besoin de vérifier
            
        policy_currency = policy.get_dimension_value("CURRENCY")
        
        # Cas 1: Police sans devise → erreur
        if not policy_currency:
            return False, f"Policy has no currency but program requires '{program.main_currency}'"
        
        # Cas 2: Devise de police = devise principale du programme → OK
        if policy_currency == program.main_currency:
            return True, None
            
        # Cas 3: Condition spécifique autorise cette devise → OK
        if matched_condition and CurrencyValidator._condition_allows_currency(
            matched_condition, policy_currency
        ):
            return True, None
            
        # Cas 4: Vérifier si une condition du programme autorise cette devise
        if CurrencyValidator._any_condition_allows_currency(program, policy_currency):
            return True, None
            
        # Cas 5: Mismatch → erreur
        return False, (
            f"Policy currency '{policy_currency}' does not match program main currency "
            f"'{program.main_currency}' and no condition allows this currency"
        )
    
    @staticmethod
    def _condition_allows_currency(condition: Condition, currency: str) -> bool:
        """
        Vérifie si une condition autorise une devise spécifique.
        
        Args:
            condition: Condition à vérifier
            currency: Devise à vérifier
        
        Returns:
            True si la condition autorise cette devise
        """
        condition_currencies = condition.get_values("CURRENCY")
        if not condition_currencies:
            return False  # Condition sans contrainte de devise
        return currency in condition_currencies
    
    @staticmethod
    def _any_condition_allows_currency(program: Program, currency: str) -> bool:
        """
        Vérifie si une condition du programme autorise une devise spécifique.
        
        Args:
            program: Programme à vérifier
            currency: Devise à vérifier
        
        Returns:
            True si une condition autorise cette devise
        """
        for structure in program.structures:
            for condition in structure.conditions:
                if CurrencyValidator._condition_allows_currency(condition, currency):
                    return True
        return False
    