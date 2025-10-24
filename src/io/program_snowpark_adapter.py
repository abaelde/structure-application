"""
Adapter Snowpark pour la lecture des programmes de réassurance.

Cet adapter utilise Snowpark pour lire les données depuis Snowflake
et les convertit en DataFrames pandas compatibles avec le ProgramSerializer existant.
"""

from __future__ import annotations
from typing import Tuple, Optional, Dict, Any
import pandas as pd
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col, lit



class SnowparkProgramIO:
    """
    I/O adapter pour les programmes utilisant Snowpark.
    
    Cet adapter lit les données depuis Snowflake en utilisant Snowpark
    et retourne des DataFrames pandas dans le format attendu par ProgramSerializer.
    """
    
    # Noms de tables hardcodés
    PROGRAMS = "REINSURANCE_PROGRAM"
    STRUCTURES = "RP_STRUCTURES"
    CONDITIONS = "RP_CONDITIONS"
    EXCLUSIONS = "RP_GLOBAL_EXCLUSION"
    FIELD_LINKS = "RP_STRUCTURE_FIELD_LINK"

    def __init__(self, session: Session):
        """
        Initialise l'adapter avec une session Snowpark.
        
        Args:
            session: Session Snowpark active
        """
        self.session = session

    def read(self, program_id: int) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Lit un programme depuis Snowflake par son ID.
        
        Args:
            program_id: ID du programme à lire
            
        Returns:
            Tuple: (program_df, structures_df, conditions_df, exclusions_df, field_links_df)
            
        Raises:
            ValueError: Si le programme n'existe pas
        """
        try:
            # 1. Lire le programme principal
            program_df = self._read_program(program_id)
            
            # 2. Lire les structures
            structures_df = self._read_structures(program_id)
            
            # 3. Lire les conditions
            conditions_df = self._read_conditions(program_id)
            
            # 4. Lire les exclusions
            exclusions_df = self._read_exclusions(program_id)
            
            # 5. Lire les field links (overrides)
            field_links_df = self._read_field_links(program_id)
            
            return program_df, structures_df, conditions_df, exclusions_df, field_links_df
            
        except Exception as e:
            raise RuntimeError(f"Error reading program {program_id} from Snowflake: {e}")

    def _read_program(self, program_id: int) -> pd.DataFrame:
        """Lit les données du programme principal."""
        program_df = self.session.table(self.PROGRAMS).filter(
            col("REINSURANCE_PROGRAM_ID") == lit(program_id)
        ).to_pandas()
        
        if program_df.empty:
            raise ValueError(f"Program with ID {program_id} not found")
        
        return program_df

    def _read_structures(self, program_id: int) -> pd.DataFrame:
        """Lit les structures du programme."""
        structures_df = self.session.table(self.STRUCTURES).filter(
            col("REINSURANCE_PROGRAM_ID") == lit(program_id)
        ).to_pandas()
        
        return structures_df

    def _read_conditions(self, program_id: int) -> pd.DataFrame:
        """Lit les conditions du programme."""
        conditions_df = self.session.table(self.CONDITIONS).filter(
            col("REINSURANCE_PROGRAM_ID") == lit(program_id)
        ).to_pandas()
        
        return conditions_df

    def _read_exclusions(self, program_id: int) -> pd.DataFrame:
        """Lit les exclusions du programme."""
        exclusions_df = self.session.table(self.EXCLUSIONS).filter(
            col("REINSURANCE_PROGRAM_ID") == lit(program_id)
        ).to_pandas()
        
        return exclusions_df

    def _read_field_links(self, program_id: int) -> pd.DataFrame:
        """Lit les field links (overrides) du programme."""
        # Requête SQL pour joindre les field links avec les conditions
        field_links_df = self.session.sql(f"""
            SELECT 
                fl.RP_STRUCTURE_FIELD_LINK_ID,
                fl.RP_CONDITION_ID,
                fl.RP_STRUCTURE_ID,
                fl.FIELD_NAME,
                fl.NEW_VALUE
            FROM {self.FIELD_LINKS} fl
            JOIN {self.CONDITIONS} c 
                ON fl.RP_CONDITION_ID = c.RP_CONDITION_ID
            WHERE c.REINSURANCE_PROGRAM_ID = {program_id}
            ORDER BY fl.RP_STRUCTURE_FIELD_LINK_ID
        """).to_pandas()
        
        return field_links_df

    def write(
        self,
        program_df: pd.DataFrame,
        structures_df: pd.DataFrame,
        conditions_df: pd.DataFrame,
        exclusions_df: pd.DataFrame,
        field_links_df: pd.DataFrame,
        connection_params: Dict[str, Any],
    ) -> None:
        """
        Écrit un programme dans Snowflake en utilisant Snowpark.
        
        Cette méthode implémente la même logique que SnowflakeProgramIO.write()
        mais en utilisant Snowpark au lieu de snowflake.connector.
        La session Snowpark est déjà configurée avec la base de données et le schéma.
        
        Args:
            program_df: DataFrame du programme
            structures_df: DataFrame des structures
            conditions_df: DataFrame des conditions
            exclusions_df: DataFrame des exclusions
            field_links_df: DataFrame des field links
            connection_params: Paramètres de connexion (non utilisés avec Snowpark)
            
        Raises:
            RuntimeError: Si l'écriture échoue
        """
        try:
            print(f"🚀 Début de l'écriture du programme via Snowpark...")
            
            # Utiliser la même logique que l'adapter classique avec ProgramFrames
            from src.serialization.program_frames import ProgramFrames, condition_dims_in
            from src.io.program_snowflake_adapter import insert_df
            
            # 1) Insérer le nouveau programme (toujours un nouveau programme)
            # Supprimer l'ID du DataFrame pour laisser Snowflake le générer
            program_df_for_insert = program_df.copy()
            if 'REINSURANCE_PROGRAM_ID' in program_df_for_insert.columns:
                program_df_for_insert = program_df_for_insert.drop(columns=['REINSURANCE_PROGRAM_ID'])
            
            # Insérer le programme via Snowpark (utiliser la même logique que l'adapter classique)
            self._insert_dataframe_snowpark(program_df_for_insert, self.PROGRAMS)
            
            # 2) Récupérer l'ID généré par Snowflake
            result = self.session.sql("SELECT MAX(REINSURANCE_PROGRAM_ID) FROM REINSURANCE_PROGRAM").collect()
            if not result or result[0][0] is None:
                raise ValueError("No program ID found after insert")
            program_id = int(result[0][0])
            print(f"✅ Programme inséré avec ID: {program_id}")
            
            # 3) Préparer CONDITIONS/STRUCTURES/EXCLUSIONS via helpers communs (même logique que l'adapter classique)
            dims = condition_dims_in(conditions_df)
            
            # Ne pas compacter les conditions pour préserver INSPER_ID_PRE
            conditions_compact = conditions_df.copy()
            
            frames = ProgramFrames(
                program_df, structures_df, conditions_compact, exclusions_df
            )
            exclusions_encoded = frames.for_csv().exclusions
            
            # Injecter REINSURANCE_PROGRAM_ID et mapper les colonnes
            structures_out = frames.structures.copy()
            conditions_out = frames.conditions.copy()  # Garde les listes natives
            exclusions_out = exclusions_encoded.copy()
            
            # Ajouter REINSURANCE_PROGRAM_ID pour les structures
            structures_out["REINSURANCE_PROGRAM_ID"] = program_id
            
            # Les conditions n'ont plus REINSURANCE_PROGRAM_ID, elles sont liées via INSPER_ID_PRE
            exclusions_out["REINSURANCE_PROGRAM_ID"] = program_id
            
            # 4) Écriture en 3 étapes : STRUCTURES -> CONDITIONS -> EXCLUSIONS
            
            # (1) Insérer les STRUCTURES en laissant Snowflake générer RP_STRUCTURE_ID (AUTOINCREMENT)
            if not structures_out.empty:
                if structures_out["RP_STRUCTURE_NAME"].duplicated().any():
                    raise ValueError("RP_STRUCTURE_NAME must be unique within a program")
                
                # Supprimer l'ID local s'il existe
                if 'RP_STRUCTURE_ID' in structures_out.columns:
                    structures_out = structures_out.drop(columns=['RP_STRUCTURE_ID'])
                
                self._insert_dataframe_snowpark(structures_out, self.STRUCTURES)
                print(f"✅ {len(structures_out)} structures insérées")
            
            # (2) Insérer les CONDITIONS
            if not conditions_out.empty:
                # Ajouter REINSURANCE_PROGRAM_ID aux conditions (comme l'adapter classique)
                conditions_out = conditions_out.copy()
                conditions_out["REINSURANCE_PROGRAM_ID"] = program_id
                self._insert_dataframe_snowpark(conditions_out, self.CONDITIONS)
                print(f"✅ {len(conditions_out)} conditions insérées")
            
            # (3) Insérer les EXCLUSIONS
            if not exclusions_out.empty:
                self._insert_dataframe_snowpark(exclusions_out, self.EXCLUSIONS)
                print(f"✅ {len(exclusions_out)} exclusions insérées")
            
            # (4) Insérer les FIELD LINKS (s'ils existent)
            if not field_links_df.empty:
                # Mapper les Field Links avec les vrais IDs générés
                field_links_mapped = self._map_field_links(field_links_df, program_id)
                if not field_links_mapped.empty:
                    # Ajouter les colonnes manquantes pour les Field Links
                    field_links_mapped["REINSURANCE_PROGRAM_ID"] = program_id
                    field_links_mapped["CREATED_AT"] = pd.Timestamp.now()
                    field_links_mapped["CREATED_BY"] = "SNOWPARK_ADAPTER"
                    
                    print(f"🔍 Field links avant insertion: {list(field_links_mapped.columns)}")
                    print(f"🔍 Field links sample: {field_links_mapped.head(1).to_dict('records')}")
                    
                    self._insert_dataframe_snowpark(field_links_mapped, self.FIELD_LINKS)
                    print(f"✅ {len(field_links_mapped)} field links insérés")
                else:
                    print(f"⚠️  Aucun field link mappé avec succès")
            
            print(f"🎉 Programme écrit avec succès via Snowpark (ID: {program_id})")
            
        except Exception as e:
            error_msg = f"Error writing program via Snowpark: {str(e)}"
            print(f"❌ {error_msg}")
            raise RuntimeError(error_msg) from e
    
    def _insert_dataframe_snowpark(self, df: pd.DataFrame, table_name: str) -> None:
        """
        Insère un DataFrame dans une table Snowflake via Snowpark.
        Utilise SQL INSERT pour gérer les colonnes auto-générées.
        
        Args:
            df: DataFrame à insérer
            table_name: Nom de la table cible
        """
        try:
            # Obtenir la structure de la table pour connaître toutes les colonnes requises
            table_structure = self._get_table_structure(table_name)
            required_columns = [row[0] for row in table_structure]
            
            # Créer un DataFrame complet avec toutes les colonnes requises
            complete_df = self._ensure_columns(df, required_columns)
            
            # Exclure les colonnes auto-générées pour l'insertion
            # REINSURANCE_PROGRAM_ID n'est auto-généré que pour la table PROGRAMS
            if table_name == self.PROGRAMS:
                auto_generated_columns = ["REINSURANCE_PROGRAM_ID"]
            elif table_name == self.EXCLUSIONS:
                # Pour les exclusions, exclure les colonnes auto-générées ET les colonnes non stockées
                auto_generated_columns = ["RP_GLOBAL_EXCLUSION_ID", "EXCLUSION_NAME", "EXCL_EFFECTIVE_DATE", "EXCL_EXPIRY_DATE"]
            elif table_name == self.FIELD_LINKS:
                # Pour les field links, exclure seulement l'ID auto-généré, pas les clés étrangères
                auto_generated_columns = ["RP_STRUCTURE_FIELD_LINK_ID"]
            else:
                auto_generated_columns = ["RP_STRUCTURE_ID", "RP_CONDITION_ID"]
            
            columns_to_exclude = [col for col in auto_generated_columns if col in complete_df.columns]
            
            if columns_to_exclude:
                insert_df = complete_df.drop(columns=columns_to_exclude)
            else:
                insert_df = complete_df
            
            # Debug: afficher les colonnes
            print(f"🔍 Colonnes requises ({len(required_columns)}): {required_columns}")
            print(f"🔍 Colonnes pour insertion ({len(insert_df.columns)}): {list(insert_df.columns)}")
            
            # Insérer chaque ligne via SQL INSERT
            for _, row in insert_df.iterrows():
                self._insert_row_sql(row, table_name)
            
        except Exception as e:
            print(f"❌ Erreur lors de l'insertion dans {table_name}: {str(e)}")
            raise
    
    def _insert_row_sql(self, row: pd.Series, table_name: str) -> None:
        """Insère une ligne via SQL INSERT."""
        try:
            # Construire la requête INSERT
            columns = list(row.index)
            values = list(row.values)
            
            # Échapper les valeurs pour SQL
            escaped_values = []
            for value in values:
                if pd.isna(value) or value is None:
                    escaped_values.append("NULL")
                elif isinstance(value, str):
                    escaped_value = value.replace("'", "''")
                    escaped_values.append(f"'{escaped_value}'")
                elif isinstance(value, pd.Timestamp):
                    escaped_values.append(f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'")
                else:
                    escaped_values.append(str(value))
            
            columns_str = ", ".join([f'"{col}"' for col in columns])
            values_str = ", ".join(escaped_values)
            
            insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str})"
            
            # Exécuter la requête
            self.session.sql(insert_sql).collect()
            
        except Exception as e:
            print(f"❌ Erreur lors de l'insertion de la ligne: {str(e)}")
            raise
    
    def _get_table_structure(self, table_name: str) -> list:
        """Obtient la structure d'une table Snowflake."""
        try:
            result = self.session.sql(f"DESCRIBE TABLE {table_name}").collect()
            return [(row[0], row[1]) for row in result]
        except Exception as e:
            print(f"❌ Erreur lors de la récupération de la structure de {table_name}: {str(e)}")
            raise
    
    def _ensure_columns(self, df: pd.DataFrame, required_columns: list) -> pd.DataFrame:
        """
        S'assure que le DataFrame contient toutes les colonnes requises.
        Ajoute les colonnes manquantes avec des valeurs par défaut.
        
        Args:
            df: DataFrame à compléter
            required_columns: Liste des colonnes requises
            
        Returns:
            DataFrame complet avec toutes les colonnes
        """
        out = df.copy()
        
        # Ajouter les colonnes manquantes avec des valeurs par défaut
        for col in required_columns:
            if col not in out.columns:
                # Valeurs par défaut selon le type de colonne
                if col == "REINSURANCE_PROGRAM_ID":
                    # ID auto-généré, utiliser NULL pour que Snowflake l'auto-génère
                    out[col] = None
                elif col == "ID_PRE":
                    # ID_PRE - utiliser le titre du programme comme ID
                    out[col] = out.get("TITLE", "UNKNOWN_PROGRAM")
                elif col in ["CREATED_AT", "MODIFIED_AT"]:
                    # Timestamps - utiliser la date actuelle
                    out[col] = pd.Timestamp.now()
                elif col in ["CREATED_BY", "MODIFIED_BY"]:
                    # Utilisateur - utiliser une valeur par défaut
                    out[col] = "SNOWPARK_ADAPTER"
                elif col == "ACTIVE_IND":
                    # Boolean - True par défaut
                    out[col] = True
                elif col == "REF_CEDENT_ID":
                    # ID du cédant - utiliser une valeur par défaut
                    out[col] = 1
                elif col == "UW_DEPARTMENT_ID":
                    # ID du département - utiliser le même que REF_REF_ID
                    out[col] = out.get("REF_REF_ID", "aviation")
                else:
                    # Autres colonnes - NULL par défaut
                    out[col] = None
        
        # Inclure toutes les colonnes requises (y compris REINSURANCE_PROGRAM_ID avec NULL)
        return out[required_columns]
    
    def _map_field_links(self, field_links_df: pd.DataFrame, program_id: int) -> pd.DataFrame:
        """
        Mappe les Field Links avec les vrais IDs générés par Snowflake.
        
        Args:
            field_links_df: DataFrame des field links avec IDs locaux
            program_id: ID du programme créé
            
        Returns:
            DataFrame des field links avec les vrais IDs mappés
        """
        try:
            if field_links_df.empty:
                return field_links_df
            
            # 1. Récupérer le mapping des structures (nom -> RP_STRUCTURE_ID)
            structures_result = self.session.sql(f"""
                SELECT RP_STRUCTURE_ID, RP_STRUCTURE_NAME 
                FROM {self.STRUCTURES} 
                WHERE REINSURANCE_PROGRAM_ID = {program_id}
                ORDER BY RP_STRUCTURE_ID
            """).collect()
            
            # Créer le mapping local -> nom -> ID généré
            # Les structures sont insérées dans l'ordre, donc on peut mapper par position
            structure_mapping = {}
            for i, (structure_id, structure_name) in enumerate(structures_result, 1):
                structure_mapping[i] = int(structure_id)  # ID local (1,2,3...) -> ID généré
            
            # 2. Récupérer le mapping des conditions (ID local -> RP_CONDITION_ID)
            conditions_result = self.session.sql(f"""
                SELECT RP_CONDITION_ID, CONDITION_NAME 
                FROM {self.CONDITIONS} 
                WHERE REINSURANCE_PROGRAM_ID = {program_id}
                ORDER BY RP_CONDITION_ID
            """).collect()
            
            # Créer le mapping local -> ID généré pour les conditions
            condition_mapping = {}
            for i, (condition_id, condition_name) in enumerate(conditions_result, 1):
                condition_mapping[i] = int(condition_id)  # ID local (1,2,3...) -> ID généré
            
            # 3. Mapper les field links
            field_links_mapped = field_links_df.copy()
            
            # Mapper RP_STRUCTURE_ID
            if 'RP_STRUCTURE_ID' in field_links_mapped.columns:
                field_links_mapped['RP_STRUCTURE_ID'] = field_links_mapped['RP_STRUCTURE_ID'].map(structure_mapping)
                if field_links_mapped['RP_STRUCTURE_ID'].isna().any():
                    print(f"⚠️  Certains RP_STRUCTURE_ID n'ont pas pu être mappés")
                    return pd.DataFrame()  # Retourner vide si mapping échoue
            
            # Mapper RP_CONDITION_ID
            if 'RP_CONDITION_ID' in field_links_mapped.columns:
                field_links_mapped['RP_CONDITION_ID'] = field_links_mapped['RP_CONDITION_ID'].map(condition_mapping)
                if field_links_mapped['RP_CONDITION_ID'].isna().any():
                    print(f"⚠️  Certains RP_CONDITION_ID n'ont pas pu être mappés")
                    return pd.DataFrame()  # Retourner vide si mapping échoue
            
            print(f"🔗 Field links mappés: {len(field_links_mapped)} liens")
            print(f"   Structures mappées: {len(structure_mapping)}")
            print(f"   Conditions mappées: {len(condition_mapping)}")
            
            return field_links_mapped
            
        except Exception as e:
            print(f"❌ Erreur lors du mapping des field links: {str(e)}")
            return pd.DataFrame()  # Retourner un DataFrame vide en cas d'erreur
