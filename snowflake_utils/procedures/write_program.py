"""
Procédure Snowpark pour l'écriture d'un programme de réassurance.

Ce module contient une fonction utilitaire simple qui utilise
l'adapter Snowpark existant pour écrire un programme.
"""

from typing import Dict, Any
import pandas as pd
from snowflake.snowpark import Session


def write_program_simple(
    session: Session,
    program_df: pd.DataFrame,
    structures_df: pd.DataFrame,
    conditions_df: pd.DataFrame,
    exclusions_df: pd.DataFrame,
    field_links_df: pd.DataFrame,
) -> Dict[str, Any]:
    """
    Écrit un programme complet dans Snowflake en utilisant l'adapter Snowpark.
    
    Cette fonction utilise simplement l'adapter SnowparkProgramIO existant
    pour écrire le programme, sans redéfinir toute la logique.
    
    Args:
        session: Session Snowpark active
        program_df: DataFrame du programme principal
        structures_df: DataFrame des structures
        conditions_df: DataFrame des conditions
        exclusions_df: DataFrame des exclusions
        field_links_df: DataFrame des field links (overrides)
        
    Returns:
        Dictionnaire contenant le résultat de l'opération :
        - success: bool - Indique si l'opération a réussi
        - program_id: int - ID du programme créé (si succès)
        - metadata: dict - Métadonnées de l'opération
        - error: str - Message d'erreur (si échec)
    """
    try:
        print("🚀 Début de l'écriture du programme via Snowpark...")
        
        # Utiliser l'adapter Snowpark existant
        from src.io.program_snowpark_adapter import SnowparkProgramIO
        
        # Créer l'adapter avec la session
        adapter = SnowparkProgramIO(session)
        
        # Créer une DSN de destination (on utilise la base/schema de la session)
        dest_dsn = "snowflake://database.schema"  # L'adapter n'utilise pas vraiment cette DSN
        
        # Appeler la méthode write de l'adapter
        adapter.write(
            dest=dest_dsn,
            program_df=program_df,
            structures_df=structures_df,
            conditions_df=conditions_df,
            exclusions_df=exclusions_df,
            field_links_df=field_links_df,
            connection_params={},  # Non utilisé avec Snowpark
        )
        
        print("🎉 Écriture du programme terminée avec succès !")
        return {
            "success": True,
            "program_id": None,  # L'adapter ne retourne pas l'ID pour l'instant
            "metadata": {
                "structures_count": len(structures_df),
                "conditions_count": len(conditions_df),
                "field_links_count": len(field_links_df),
                "exclusions_count": len(exclusions_df),
            },
        }
        
    except Exception as e:
        error_msg = f"Erreur lors de l'écriture du programme: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        print(f"Détails de l'erreur: {traceback.format_exc()}")
        return {"success": False, "error": error_msg}
