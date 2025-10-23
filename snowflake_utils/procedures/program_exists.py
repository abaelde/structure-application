"""
Procédure Snowpark pour la vérification d'existence d'un programme.

Ce module contient la fonction de vérification de l'existence
d'un programme dans Snowflake en utilisant Snowpark.
"""

from snowflake.snowpark import Session
from snowflake.snowpark.functions import col, lit


def program_exists_simple(session: Session, program_id: int) -> bool:
    """
    Vérifie si un programme existe en utilisant Snowpark.
    
    Args:
        session: Session Snowpark active
        program_id: ID du programme à vérifier
        
    Returns:
        True si le programme existe, False sinon
    """
    try:
        count = session.table("REINSURANCE_PROGRAM").filter(
            col("REINSURANCE_PROGRAM_ID") == lit(program_id)
        ).count()
        
        return count > 0
        
    except Exception as e:
        print(f"Error checking program existence: {e}")
        return False


