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
        
        # Handle list of currencies (aviation case)
        if isinstance(policy_currency, (list, tuple, set)):
            policy_currencies = set(policy_currency)
        else:
            policy_currencies = {policy_currency}
        
        # Cas 2: Devise principale du programme dans les devises de police → OK
        if program.main_currency in policy_currencies:
            return True, None
            
        # Cas 3: Condition spécifique autorise au moins une devise de police → OK
        if matched_condition and CurrencyValidator._condition_allows_any_currency(
            matched_condition, policy_currencies
        ):
            return True, None
            
        # Cas 4: Vérifier si une condition du programme autorise au moins une devise de police
        if CurrencyValidator._any_condition_allows_any_currency(program, policy_currencies):
            return True, None
            
        # Cas 5: Mismatch → erreur
        return False, (
            f"Policy currencies {list(policy_currencies)} do not match program main currency "
            f"'{program.main_currency}' and no condition allows any of these currencies"
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
    def _condition_allows_any_currency(condition: Condition, currencies: set[str]) -> bool:
        """
        Vérifie si une condition autorise au moins une devise d'un ensemble.
        
        Args:
            condition: Condition à vérifier
            currencies: Ensemble de devises à vérifier
        
        Returns:
            True si la condition autorise au moins une de ces devises
        """
        condition_currencies = condition.get_values("CURRENCY")
        if not condition_currencies:
            return False  # Condition sans contrainte de devise
        return any(currency in condition_currencies for currency in currencies)
    
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
    
    @staticmethod
    def _any_condition_allows_any_currency(program: Program, currencies: set[str]) -> bool:
        """
        Vérifie si une condition du programme autorise au moins une devise d'un ensemble.
        
        Args:
            program: Programme à vérifier
            currencies: Ensemble de devises à vérifier
        
        Returns:
            True si une condition autorise au moins une de ces devises
        """
        for structure in program.structures:
            for condition in structure.conditions:
                if CurrencyValidator._condition_allows_any_currency(condition, currencies):
                    return True
        return False
    