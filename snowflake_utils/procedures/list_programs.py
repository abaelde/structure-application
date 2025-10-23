"""
Procédure Snowpark pour la liste des programmes de réassurance.

Ce module contient la fonction de liste de tous les programmes
disponibles dans Snowflake en utilisant Snowpark.
"""

from typing import Dict, Any
from snowflake.snowpark import Session


def list_programs_simple(session: Session) -> Dict[str, Any]:
    try:
        # Récupérer tous les programmes avec leurs métadonnées
        programs_df = session.sql("""
            SELECT 
                REINSURANCE_PROGRAM_ID,
                TITLE,
                CREATED_AT,
                MODIFIED_AT,
                (SELECT COUNT(*) FROM RP_STRUCTURES s WHERE s.REINSURANCE_PROGRAM_ID = p.REINSURANCE_PROGRAM_ID) as STRUCTURES_COUNT,
                (SELECT COUNT(*) FROM RP_CONDITIONS c WHERE c.REINSURANCE_PROGRAM_ID = p.REINSURANCE_PROGRAM_ID) as CONDITIONS_COUNT
            FROM REINSURANCE_PROGRAM p
            ORDER BY CREATED_AT DESC
        """).to_pandas()
        
        result = {
            "programs": programs_df.to_dict('records'),
            "total_count": len(programs_df)
        }
        
        return result
        
    except Exception as e:
        return {"error": f"Error listing programs: {str(e)}"}


