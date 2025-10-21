# src/io/program_snowflake_csv_adapter.py
from __future__ import annotations
from typing import Tuple, Optional, Dict, Any, List
import json, uuid
import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

class SnowflakeProgramCSVIO:
    """
    Adapter Snowflake avec correspondance 1:1 aux colonnes CSV.
    Chaque colonne CSV correspond à une colonne table Snowflake.
    
    Tables:
      - PROGRAMS: 14 colonnes CSV + 2 colonnes d'audit
      - STRUCTURES: 21 colonnes CSV + 1 clé de liaison
      - CONDITIONS: 38 colonnes CSV + 1 clé de liaison  
      - EXCLUSIONS: 11 colonnes CSV + 1 clé de liaison

    DSN attendu pour load/save :
      snowflake://DB.SCHEMA?program_title=...

    connection_params: dict pour snowflake.connector.connect(...)
    if_exists (save) :
      - "append"             : ajoute un nouveau programme
      - "replace_program"    : supprime le programme existant puis ré-insère
      - "truncate_all"       : TRUNCATE des 4 tables avant insert
    """

    PROGRAMS = "PROGRAMS"
    STRUCTURES = "STRUCTURES"
    CONDITIONS = "CONDITIONS"
    EXCLUSIONS = "EXCLUSIONS"

    # ────────────────────────────────────────────────────────────────────
    # Utils
    # ────────────────────────────────────────────────────────────────────
    def _parse_dsn(self, source: str) -> Tuple[str, str, Dict[str, str]]:
        if not source.lower().startswith("snowflake://"):
            raise ValueError(f"Invalid Snowflake DSN: {source}")
        rest = source[len("snowflake://"):]
        if "?" in rest:
            coord, qs = rest.split("?", 1)
        else:
            coord, qs = rest, ""
        parts = coord.split(".")
        if len(parts) != 2:
            raise ValueError("DSN must be snowflake://DB.SCHEMA?...")
        db, schema = parts[0], parts[1]
        params = {}
        if qs:
            for tok in qs.split("&"):
                if not tok:
                    continue
                k, _, v = tok.partition("=")
                params[k] = v
        return db, schema, params

    def _connect(self, connection_params: Dict[str, Any]):
        return snowflake.connector.connect(**connection_params)

    def _get_program_id_from_title(self, program_title: str, connection_params: Dict[str, Any], db: str, schema: str) -> int:
        """Récupère l'ID du programme depuis la base de données basé sur le titre"""
        cnx = self._connect(connection_params)
        cur = cnx.cursor()
        
        try:
            cur.execute(f'SELECT REINSURANCE_PROGRAM_ID FROM "{db}"."{schema}"."{self.PROGRAMS}" WHERE TITLE=%s', (program_title,))
            result = cur.fetchone()
            if result:
                return result[0]
            else:
                raise ValueError(f"Programme '{program_title}' non trouvé dans la base de données")
        finally:
            cur.close()
            cnx.close()

    # ────────────────────────────────────────────────────────────────────
    # READ
    # ────────────────────────────────────────────────────────────────────
    def read(self, source: str, connection_params: Dict[str, Any]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        db, schema, params = self._parse_dsn(source)
        
        # Déterminer l'identifiant du programme
        program_title = params.get("program_title")
        if not program_title:
            raise ValueError("DSN must specify program_title parameter")
        
        # Récupérer l'ID du programme depuis la base de données
        program_id = self._get_program_id_from_title(program_title, connection_params, db, schema)

        cnx = self._connect(connection_params)
        cur = cnx.cursor()

        try:
            # PROGRAMS - utiliser TITLE pour trouver le programme
            cur.execute(f'SELECT * FROM "{db}"."{schema}"."{self.PROGRAMS}" WHERE TITLE=%s', (program_title,))
            prog_rows = cur.fetchall()
            prog_cols = [d[0] for d in cur.description]
            
            if not prog_rows:
                raise ValueError("Program not found in PROGRAMS")
            
            program_df = pd.DataFrame([dict(zip(prog_cols, prog_rows[0]))])

            # STRUCTURES - toutes les colonnes CSV
            cur.execute(f'SELECT * FROM "{db}"."{schema}"."{self.STRUCTURES}" WHERE PROGRAM_ID=%s ORDER BY INSPER_CONTRACT_ORDER NULLS LAST, INSPER_ID_PRE', (program_id,))
            s_rows = cur.fetchall()
            s_cols = [d[0] for d in cur.description]
            structures = []
            for r in s_rows:
                d = dict(zip(s_cols, r))
                structures.append(d)
            structures_df = pd.DataFrame(structures) if structures else pd.DataFrame()

            # CONDITIONS - toutes les colonnes CSV
            cur.execute(f'SELECT * FROM "{db}"."{schema}"."{self.CONDITIONS}" WHERE PROGRAM_ID=%s ORDER BY BUSCL_ID_PRE', (program_id,))
            c_rows = cur.fetchall()
            c_cols = [d[0] for d in cur.description]
            conditions = []
            for r in c_rows:
                d = dict(zip(c_cols, r))
                conditions.append(d)
            conditions_df = pd.DataFrame(conditions) if conditions else pd.DataFrame()

            # EXCLUSIONS - toutes les colonnes CSV
            cur.execute(f'SELECT * FROM "{db}"."{schema}"."{self.EXCLUSIONS}" WHERE PROGRAM_ID=%s', (program_id,))
            e_rows = cur.fetchall()
            e_cols = [d[0] for d in cur.description]
            exclusions = []
            for r in e_rows:
                d = dict(zip(e_cols, r))
                exclusions.append(d)
            exclusions_df = pd.DataFrame(exclusions) if exclusions else pd.DataFrame()

            return program_df, structures_df, conditions_df, exclusions_df

        finally:
            cur.close()
            cnx.close()

    # ────────────────────────────────────────────────────────────────────
    # WRITE
    # ────────────────────────────────────────────────────────────────────
    def write(
        self,
        dest: str,
        program_df: pd.DataFrame,
        structures_df: pd.DataFrame,
        conditions_df: pd.DataFrame,
        exclusions_df: pd.DataFrame,
        connection_params: Dict[str, Any],
        if_exists: str = "append",
    ) -> None:
        db, schema, params = self._parse_dsn(dest)
        
        # Déterminer l'identifiant du programme
        program_title = params.get("program_title")
        if not program_title:
            raise ValueError("DSN must specify program_title parameter")
        
        # Pour la sauvegarde, on va d'abord insérer le programme et récupérer son ID auto-généré
        # ou récupérer l'ID existant si le programme existe déjà

        cnx = self._connect(connection_params)
        cur = cnx.cursor()

        try:
            # Gérer les modes de remplacement
            if if_exists == "truncate_all":
                cur.execute(f'TRUNCATE TABLE "{db}"."{schema}"."{self.PROGRAMS}"')
                cur.execute(f'TRUNCATE TABLE "{db}"."{schema}"."{self.STRUCTURES}"')
                cur.execute(f'TRUNCATE TABLE "{db}"."{schema}"."{self.CONDITIONS}"')
                cur.execute(f'TRUNCATE TABLE "{db}"."{schema}"."{self.EXCLUSIONS}"')
            elif if_exists == "replace_program":
                # Supprimer le programme existant et ses données liées
                cur.execute(f'SELECT REINSURANCE_PROGRAM_ID FROM "{db}"."{schema}"."{self.PROGRAMS}" WHERE TITLE=%s', (program_title,))
                existing_program = cur.fetchone()
                if existing_program:
                    existing_program_id = existing_program[0]
                    cur.execute(f'DELETE FROM "{db}"."{schema}"."{self.EXCLUSIONS}" WHERE PROGRAM_ID=%s', (existing_program_id,))
                    cur.execute(f'DELETE FROM "{db}"."{schema}"."{self.CONDITIONS}" WHERE PROGRAM_ID=%s', (existing_program_id,))
                    cur.execute(f'DELETE FROM "{db}"."{schema}"."{self.STRUCTURES}" WHERE PROGRAM_ID=%s', (existing_program_id,))
                    cur.execute(f'DELETE FROM "{db}"."{schema}"."{self.PROGRAMS}" WHERE REINSURANCE_PROGRAM_ID=%s', (existing_program_id,))

            # PROGRAMS - insérer et récupérer l'ID auto-généré
            program_id = None
            if not program_df.empty:
                p_rows: List[Dict[str, Any]] = []
                for _, r in program_df.iterrows():
                    row_dict = r.to_dict()
                    
                    # Mapping des colonnes CSV vers Snowflake
                    mapped_row = {}
                    for csv_col, value in row_dict.items():
                        if csv_col == 'REPROG_TITLE':
                            mapped_row['TITLE'] = value
                        elif csv_col == 'REPROG_ID_PRE':
                            # Ne pas inclure REPROG_ID_PRE car c'est auto-increment
                            continue
                        elif csv_col == 'REPROG_ACTIVE_IND':
                            mapped_row['ACTIVE_IND'] = value
                        elif csv_col == 'REPROG_UW_DEPARTMENT_LOB_CD':
                            mapped_row['UW_LOB'] = value
                        elif csv_col == 'REPROG_MAIN_CURRENCY_CD':
                            mapped_row['MAIN_CURRENCY_CD'] = value
                        elif csv_col == 'REPROG_COMMENT':
                            mapped_row['ADDITIONAL_INFO'] = value
                        elif csv_col == 'REPROG_UW_DEPARTMENT_CD':
                            mapped_row['UW_DEPARTMENT_CODE'] = value
                        elif csv_col == 'BUSPAR_CED_REG_CLASS_CD':
                            mapped_row['BUSPAR_CED_REG_CLASS_CD'] = value
                        elif csv_col == 'CED_ID_PRE':
                            mapped_row['CED_ID_PRE'] = value
                        elif csv_col == 'CED_NAME_PRE':
                            mapped_row['ID_PRE'] = value
                        # Ignorer les colonnes qui n'existent pas dans la table Snowflake
                        elif csv_col in ['REPROG_UW_DEPARTMENT_NAME', 'REPROG_UW_DEPARTMENT_LOB_NAME', 
                                       'BUSPAR_CED_REG_CLASS_NAME', 'REPROG_MANAGEMENT_REPORTING_LOB_CD']:
                            continue
                        else:
                            # Garder les autres colonnes telles quelles
                            mapped_row[csv_col] = value
                    
                    # Ajouter les colonnes d'audit
                    mapped_row['CREATED_AT'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                    mapped_row['UPDATED_AT'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                    p_rows.append(mapped_row)
                
                # Insérer le programme et récupérer l'ID auto-généré
                write_pandas(cnx, pd.DataFrame(p_rows), table_name=self.PROGRAMS, database=db, schema=schema, auto_create_table=False, quote_identifiers=True)
                
                # Récupérer l'ID du programme qui vient d'être inséré
                cur.execute(f'SELECT REINSURANCE_PROGRAM_ID FROM "{db}"."{schema}"."{self.PROGRAMS}" WHERE TITLE=%s', (program_title,))
                result = cur.fetchone()
                if result:
                    program_id = result[0]
                else:
                    raise ValueError(f"Impossible de récupérer l'ID du programme '{program_title}' après insertion")

            # STRUCTURES - toutes les colonnes CSV + PROGRAM_ID
            if not structures_df.empty:
                s_rows: List[Dict[str, Any]] = []
                for _, r in structures_df.iterrows():
                    row_dict = r.to_dict()
                    
                    # Mapping des colonnes CSV vers Snowflake
                    mapped_row = {}
                    for csv_col, value in row_dict.items():
                        if csv_col == 'INSPER_ID_PRE':
                            # Ne pas inclure INSPER_ID_PRE car c'est auto-increment
                            continue
                        elif csv_col == 'REPROG_ID_PRE':
                            # Remplacer par PROGRAM_ID
                            mapped_row['PROGRAM_ID'] = program_id
                        elif csv_col == 'BUSINESS_TITLE':
                            mapped_row['BUSINESS_TITLE'] = value
                        else:
                            # Garder les autres colonnes telles quelles
                            mapped_row[csv_col] = value
                    
                    # Convertir les timestamps au format standard pour Snowflake
                    for col in ['INSPER_EFFECTIVE_DATE', 'INSPER_EXPIRY_DATE']:
                        if col in mapped_row and pd.notna(mapped_row[col]):
                            if isinstance(mapped_row[col], pd.Timestamp):
                                mapped_row[col] = mapped_row[col].strftime('%Y-%m-%d %H:%M:%S')
                    
                    s_rows.append(mapped_row)
                write_pandas(cnx, pd.DataFrame(s_rows), table_name=self.STRUCTURES, database=db, schema=schema, auto_create_table=False, quote_identifiers=True)

            # CONDITIONS - toutes les colonnes CSV + PROGRAM_ID
            if not conditions_df.empty:
                c_rows: List[Dict[str, Any]] = []
                for _, r in conditions_df.iterrows():
                    row_dict = r.to_dict()
                    
                    # Mapping des colonnes CSV vers Snowflake
                    mapped_row = {}
                    for csv_col, value in row_dict.items():
                        if csv_col == 'REPROG_ID_PRE':
                            # Remplacer par PROGRAM_ID
                            mapped_row['PROGRAM_ID'] = program_id
                        else:
                            # Garder les autres colonnes telles quelles
                            mapped_row[csv_col] = value
                    
                    # Convertir les timestamps au format standard pour Snowflake
                    for col in ['INSPER_EFFECTIVE_DATE', 'INSPER_EXPIRY_DATE']:
                        if col in mapped_row and pd.notna(mapped_row[col]):
                            if isinstance(mapped_row[col], pd.Timestamp):
                                mapped_row[col] = mapped_row[col].strftime('%Y-%m-%d %H:%M:%S')
                    
                    c_rows.append(mapped_row)
                write_pandas(cnx, pd.DataFrame(c_rows), table_name=self.CONDITIONS, database=db, schema=schema, auto_create_table=False, quote_identifiers=True)

            # EXCLUSIONS - toutes les colonnes CSV + PROGRAM_ID
            if not exclusions_df.empty:
                e_rows: List[Dict[str, Any]] = []
                for _, r in exclusions_df.iterrows():
                    row_dict = r.to_dict()
                    
                    # Mapping des colonnes CSV vers Snowflake
                    mapped_row = {}
                    for csv_col, value in row_dict.items():
                        if csv_col == 'REPROG_ID_PRE':
                            # Remplacer par PROGRAM_ID
                            mapped_row['PROGRAM_ID'] = program_id
                        else:
                            # Garder les autres colonnes telles quelles
                            mapped_row[csv_col] = value
                    
                    # Convertir les timestamps au format standard pour Snowflake
                    for col in ['INSPER_EFFECTIVE_DATE', 'INSPER_EXPIRY_DATE']:
                        if col in mapped_row and pd.notna(mapped_row[col]):
                            if isinstance(mapped_row[col], pd.Timestamp):
                                mapped_row[col] = mapped_row[col].strftime('%Y-%m-%d %H:%M:%S')
                    
                    e_rows.append(mapped_row)
                write_pandas(cnx, pd.DataFrame(e_rows), table_name=self.EXCLUSIONS, database=db, schema=schema, auto_create_table=False, quote_identifiers=True)

        finally:
            cur.close()
            cnx.close()

    # ────────────────────────────────────────────────────────────────────
    # UTILS
    # ────────────────────────────────────────────────────────────────────
    def drop_all_tables(self, connection_params: Dict[str, Any], db: str, schema: str) -> None:
        """Supprime toutes les tables (utile pour les tests)"""
        cnx = self._connect(connection_params)
        cur = cnx.cursor()
        try:
            for table in [self.EXCLUSIONS, self.CONDITIONS, self.STRUCTURES, self.PROGRAMS]:
                cur.execute(f'DROP TABLE IF EXISTS "{db}"."{schema}"."{table}"')
        finally:
            cur.close()
            cnx.close()
