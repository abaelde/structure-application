"""
Procédure Snowpark pour la lecture d'un programme de réassurance.

Ce module contient la fonction de lecture d'un programme complet
depuis Snowflake en utilisant Snowpark.
"""

from typing import Dict, Any
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col, lit


def read_program_simple(session: Session, program_id: int) -> Dict[str, Any]:
    """
    Lit un programme complet depuis Snowflake en utilisant Snowpark.
    
    Args:
        session: Session Snowpark active
        program_id: ID du programme à lire
        
    Returns:
        Dictionnaire contenant toutes les données du programme
    """
    try:
        # Lecture du programme principal
        program_df = session.table("REINSURANCE_PROGRAM").filter(
            col("REINSURANCE_PROGRAM_ID") == lit(program_id)
        ).to_pandas()
        
        if program_df.empty:
            return {"error": f"Program with ID {program_id} not found"}
        
        # Lecture des structures
        structures_df = session.table("RP_STRUCTURES").filter(
            col("REINSURANCE_PROGRAM_ID") == lit(program_id)
        ).to_pandas()
        
        # Lecture des conditions
        conditions_df = session.table("RP_CONDITIONS").filter(
            col("REINSURANCE_PROGRAM_ID") == lit(program_id)
        ).to_pandas()
        
        # Lecture des exclusions
        exclusions_df = session.table("RP_GLOBAL_EXCLUSION").filter(
            col("REINSURANCE_PROGRAM_ID") == lit(program_id)
        ).to_pandas()
        
        # Lecture des field links (overrides)
        field_links_df = session.sql(f"""
            SELECT 
                fl.RP_STRUCTURE_FIELD_LINK_ID,
                fl.RP_CONDITION_ID,
                fl.RP_STRUCTURE_ID,
                fl.FIELD_NAME,
                fl.NEW_VALUE
            FROM RP_STRUCTURE_FIELD_LINK fl
            JOIN RP_CONDITIONS c ON fl.RP_CONDITION_ID = c.RP_CONDITION_ID
            WHERE c.REINSURANCE_PROGRAM_ID = {program_id}
        """).to_pandas()
        
        # Préparer les données de retour
        result = {
            "program": program_df.to_dict('records'),
            "structures": structures_df.to_dict('records'),
            "conditions": conditions_df.to_dict('records'),
            "exclusions": exclusions_df.to_dict('records'),
            "field_links": field_links_df.to_dict('records'),
            "metadata": {
                "program_id": program_id,
                "structures_count": len(structures_df),
                "conditions_count": len(conditions_df),
                "exclusions_count": len(exclusions_df),
                "field_links_count": len(field_links_df)
            }
        }
        
        return result
        
    except Exception as e:
        return {"error": f"Error reading program {program_id}: {str(e)}"}


