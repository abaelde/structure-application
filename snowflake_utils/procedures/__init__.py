"""
Module des procédures Snowpark pour la gestion des programmes de réassurance.

Ce module contient toutes les procédures Snowpark organisées par fonctionnalité :
- Lecture de programmes
- Liste des programmes
- Vérification d'existence
- Tests des procédures
"""

from .read_program import read_program_simple
from .list_programs import list_programs_simple
from .program_exists import program_exists_simple

from .test_procedures import (
    test_simple_procedures,
)

__all__ = [
    # Lecture de programmes
    "read_program_simple",
    
    # Liste des programmes
    "list_programs_simple", 
    
    # Vérification d'existence
    "program_exists_simple",
    
    # Tests
    "test_simple_procedures",
]
