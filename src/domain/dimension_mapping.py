# src/domain/dimension_mapping.py
"""
Configuration-driven dimension mapping between programs and bordereaux.

This module provides a flexible mapping system that allows:
- Easy maintenance when column names change in databases
- Support for optional dimensions (missing dimensions use default regime)
- Special handling for currency mapping by line of business
- Aviation currency consistency validation
"""

from typing import Dict, Any, Optional, List


# Mapping des noms de colonnes : Programme → Bordereau
DIMENSION_COLUMN_MAPPING = {
    # Dimensions universelles (même nom dans tous les cas)
    "BUSCL_COUNTRY_CD": "BUSCL_COUNTRY_CD",
    "BUSCL_REGION": "BUSCL_REGION", 
    "BUSCL_CLASS_OF_BUSINESS_1": "BUSCL_CLASS_OF_BUSINESS_1",
    "BUSCL_CLASS_OF_BUSINESS_2": "BUSCL_CLASS_OF_BUSINESS_2",
    "BUSCL_CLASS_OF_BUSINESS_3": "BUSCL_CLASS_OF_BUSINESS_3",
    "BUSCL_ENTITY_NAME_CED": "BUSCL_ENTITY_NAME_CED",
    "POL_RISK_NAME_CED": "POL_RISK_NAME_CED",
    "BUSCL_EXCLUDE_CD": "BUSCL_EXCLUDE_CD",
    
    # Dimension spéciale : currency (un seul concept, mais noms différents)
    "BUSCL_LIMIT_CURRENCY_CD": {
        "aviation": "HULL_CURRENCY",  # Aviation : on prend HULL_CURRENCY (HULL et LIABILITY doivent être identiques)
        "casualty": "CURRENCY"  # Casualty : 1 seule colonne
    }
}

# Dimensions optionnelles (peuvent être absentes du bordereau)
OPTIONAL_DIMENSIONS = {
    "BUSCL_ENTITY_NAME_CED",
    "POL_RISK_NAME_CED", 
    "BUSCL_EXCLUDE_CD"
}

# Toutes les dimensions sont optionnelles - si absentes, on applique le régime par défaut
# Pas de REQUIRED_DIMENSIONS car cela serait trop limitatif pour les bordereaux


def get_policy_value(policy_data: Dict[str, Any], dimension: str, line_of_business: Optional[str] = None) -> Optional[Any]:
    """
    Récupère la valeur d'une dimension depuis les données de police.
    Gère les dimensions optionnelles et les mappings spéciaux.
    
    Args:
        policy_data: Données de la police depuis le bordereau
        dimension: Nom de la dimension dans le programme (ex: "BUSCL_LIMIT_CURRENCY_CD")
        line_of_business: Type de ligne de business ("aviation" ou "casualty")
    
    Returns:
        Valeur de la dimension ou None si non trouvée/optionnelle
    """
    
    # 1. Mapping direct (cas le plus simple)
    if dimension in DIMENSION_COLUMN_MAPPING:
        mapping = DIMENSION_COLUMN_MAPPING[dimension]
        
        # Mapping simple (string)
        if isinstance(mapping, str):
            return policy_data.get(mapping)
        
        # Mapping complexe (dict avec line_of_business)
        if isinstance(mapping, dict):
            if line_of_business in mapping:
                candidate = mapping[line_of_business]
                if isinstance(candidate, str):
                    return policy_data.get(candidate)
    
    # 2. Fallback : essayer le nom direct
    return policy_data.get(dimension)


def is_dimension_optional(dimension: str) -> bool:
    """Toutes les dimensions sont optionnelles - retourne toujours True"""
    return True


def validate_program_bordereau_compatibility(
    program_dimensions: List[str], 
    bordereau_columns: List[str], 
    line_of_business: Optional[str]
) -> tuple[List[str], List[str]]:
    """
    Valide la compatibilité entre programme et bordereau.
    Toutes les dimensions sont optionnelles - si absentes, on applique le régime par défaut.
    
    Args:
        program_dimensions: Liste des dimensions utilisées dans le programme
        bordereau_columns: Liste des colonnes disponibles dans le bordereau
        line_of_business: Type de ligne de business
        
    Returns:
        Tuple (errors, warnings) - errors sera toujours vide, warnings contient les infos
    """
    warnings = []
    errors = []  # Toujours vide - pas de dimensions obligatoires
    
    for dimension in program_dimensions:
        # Avertissement informatif si dimension non trouvée
        if not can_map_dimension(dimension, bordereau_columns, line_of_business):
            warnings.append(f"Dimension '{dimension}' non trouvée dans le bordereau - régime par défaut appliqué")
    
    return errors, warnings


def can_map_dimension(dimension: str, bordereau_columns: List[str], line_of_business: Optional[str]) -> bool:
    """Vérifie si une dimension peut être mappée depuis les colonnes du bordereau"""
    if dimension in DIMENSION_COLUMN_MAPPING:
        mapping = DIMENSION_COLUMN_MAPPING[dimension]
        
        if isinstance(mapping, str):
            return mapping in bordereau_columns
        elif isinstance(mapping, dict):
            if line_of_business in mapping:
                candidate = mapping[line_of_business]
                if isinstance(candidate, str):
                    return candidate in bordereau_columns
    
    # Fallback : nom direct
    return dimension in bordereau_columns


def validate_aviation_currency_consistency(bordereau_columns: List[str], line_of_business: Optional[str]) -> List[str]:
    """
    Validation spécifique pour l'aviation : HULL_CURRENCY et LIABILITY_CURRENCY doivent être identiques.
    
    Args:
        bordereau_columns: Liste des colonnes disponibles dans le bordereau
        line_of_business: Type de ligne de business
        
    Returns:
        Liste des avertissements
    """
    if line_of_business != "aviation":
        return []
    
    warnings = []
    
    # Vérifier si les deux colonnes sont présentes
    has_hull = "HULL_CURRENCY" in bordereau_columns
    has_liability = "LIABILITY_CURRENCY" in bordereau_columns
    
    if has_hull and has_liability:
        warnings.append("⚠️  Aviation : Vérifiez que HULL_CURRENCY et LIABILITY_CURRENCY sont identiques dans vos données")
        warnings.append("   Si elles diffèrent, le système prendra HULL_CURRENCY par défaut")
    
    return warnings


def get_all_mappable_dimensions(bordereau_columns: List[str], line_of_business: Optional[str]) -> Dict[str, str]:
    """
    Retourne toutes les dimensions qui peuvent être mappées depuis le bordereau.
    Utile pour la validation et le debugging.
    
    Args:
        bordereau_columns: Liste des colonnes disponibles dans le bordereau
        line_of_business: Type de ligne de business
        
    Returns:
        Dict {dimension_program: colonne_bordereau}
    """
    mappable = {}
    
    for dimension, mapping in DIMENSION_COLUMN_MAPPING.items():
        if isinstance(mapping, str):
            if mapping in bordereau_columns:
                mappable[dimension] = mapping
        elif isinstance(mapping, dict):
            if line_of_business in mapping:
                candidate = mapping[line_of_business]
                if isinstance(candidate, str) and candidate in bordereau_columns:
                    mappable[dimension] = candidate
    
    return mappable
