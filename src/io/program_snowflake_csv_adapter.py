# src/io/program_snowflake_csv_adapter.py
from __future__ import annotations
from typing import Tuple, Optional, Dict, Any, List
import pandas as pd
import snowflake.connector
from src.domain.schema import PROGRAM_TO_BORDEREAU_DIMENSIONS
from src.serialization.program_frames import ProgramFrames, condition_dims_in
from src.serialization.compact import compact_multivalue

class SnowflakeProgramCSVIO:
    PROGRAMS   = "REINSURANCE_PROGRAM"
    STRUCTURES = "RP_STRUCTURES"
    CONDITIONS = "RP_CONDITIONS"
    EXCLUSIONS = "RP_GLOBAL_EXCLUSION"

    # ---------------- utils colonne
    @staticmethod
    def _ensure_columns(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
        out = df.copy()
        for c in cols:
            if c not in out.columns:
                out[c] = None
        return out[cols]

    def _parse_dsn(self, source: str) -> Tuple[str, str, Dict[str, str]]:
        if not source.lower().startswith("snowflake://"):
            raise ValueError(f"Invalid Snowflake DSN: {source}")
        rest = source[len("snowflake://") :]
        coord, qs = (rest.split("?",1)+[""])[:2]
        parts = coord.split(".")
        if len(parts) != 2:
            raise ValueError("DSN must be snowflake://DB.SCHEMA?...")
        db, schema = parts
        params = {}
        if qs:
            for tok in qs.split("&"):
                if tok:
                    k, _, v = tok.partition("="); params[k] = v
        return db, schema, params

    def _connect(self, connection_params: Dict[str, Any]):
        return snowflake.connector.connect(**connection_params)

    def _program_id_by_title(self, cnx, db: str, schema: str, title: str) -> Optional[int]:
        cur = cnx.cursor()
        try:
            cur.execute(
                f'SELECT REINSURANCE_PROGRAM_ID FROM "{db}"."{schema}"."{self.PROGRAMS}" WHERE TITLE=%s',
                (title,)
            )
            row = cur.fetchone()
            return None if not row else row[0]
        finally:
            cur.close()

    def _clean_values_for_sql(self, values: List[Any]) -> List[Any]:
        """Nettoie les valeurs pour l'insertion SQL (conversion des timestamps, listes, etc.)"""
        cleaned = []
        for v in values:
            if pd.isna(v):
                cleaned.append(None)
            elif isinstance(v, pd.Timestamp):
                cleaned.append(v.strftime("%Y-%m-%d %H:%M:%S"))
            elif isinstance(v, list):
                # Convertir les listes en strings avec séparateur
                cleaned.append(";".join(str(item) for item in v) if v else None)
            else:
                cleaned.append(v)
        return cleaned

    # ---------------- READ inchangé (logique actuelle OK) ----------------
    def read(
        self,
        source: str,
        connection_params: Dict[str, Any],
        program_title: Optional[str] = None,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Lit un programme depuis Snowflake.
        Retourne (program_df, structures_df, conditions_df, exclusions_df)
        """
        db, schema, params = self._parse_dsn(source)
        
        cnx = self._connect(connection_params)
        cur = cnx.cursor()
        try:
            # 1. Lire le programme
            if program_title:
                cur.execute(
                    f'SELECT * FROM "{db}"."{schema}"."{self.PROGRAMS}" WHERE TITLE=%s',
                    (program_title,)
                )
            else:
                cur.execute(f'SELECT * FROM "{db}"."{schema}"."{self.PROGRAMS}"')
            
            program_rows = cur.fetchall()
            if not program_rows:
                raise ValueError(f"Program '{program_title}' not found")
            
            program_df = pd.DataFrame(program_rows, columns=[desc[0] for desc in cur.description])
            
            # 2. Lire les structures
            program_id = int(program_df.iloc[0]['REINSURANCE_PROGRAM_ID'])
            cur.execute(
                f'SELECT * FROM "{db}"."{schema}"."{self.STRUCTURES}" WHERE PROGRAM_ID=%s',
                (program_id,)
            )
            structures_rows = cur.fetchall()
            structures_df = pd.DataFrame(structures_rows, columns=[desc[0] for desc in cur.description])
            
            # 3. Lire les conditions
            cur.execute(
                f'SELECT * FROM "{db}"."{schema}"."{self.CONDITIONS}" WHERE PROGRAM_ID=%s',
                (program_id,)
            )
            conditions_rows = cur.fetchall()
            conditions_df = pd.DataFrame(conditions_rows, columns=[desc[0] for desc in cur.description])
            
            # 4. Lire les exclusions
            cur.execute(
                f'SELECT * FROM "{db}"."{schema}"."{self.EXCLUSIONS}" WHERE RP_ID=%s',
                (program_id,)
            )
            exclusions_rows = cur.fetchall()
            exclusions_df = pd.DataFrame(exclusions_rows, columns=[desc[0] for desc in cur.description])
            
            return program_df, structures_df, conditions_df, exclusions_df
            
        finally:
            cur.close()
            cnx.close()

    # ---------------- WRITE simplifié & mutualisé ----------------
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
        program_title = params.get("program_title")
        if not program_title:
            raise ValueError("DSN must specify program_title parameter")

        cnx = self._connect(connection_params)
        try:
            cur = cnx.cursor()
            try:
                if if_exists == "truncate_all":
                    for t in [self.EXCLUSIONS, self.CONDITIONS, self.STRUCTURES, self.PROGRAMS]:
                        cur.execute(f'TRUNCATE TABLE "{db}"."{schema}"."{t}"')
                elif if_exists == "replace_program":
                    existing = self._program_id_by_title(cnx, db, schema, program_title)
                    if existing is not None:
                        cur.execute(f'DELETE FROM "{db}"."{schema}"."{self.EXCLUSIONS}" WHERE RP_ID=%s', (existing,))
                        cur.execute(f'DELETE FROM "{db}"."{schema}"."{self.CONDITIONS}" WHERE PROGRAM_ID=%s', (existing,))
                        cur.execute(f'DELETE FROM "{db}"."{schema}"."{self.STRUCTURES}" WHERE PROGRAM_ID=%s', (existing,))
                        cur.execute(f'DELETE FROM "{db}"."{schema}"."{self.PROGRAMS}"   WHERE REINSURANCE_PROGRAM_ID=%s', (existing,))

                # 1) Insert/ensure PROGRAMS row (SQL direct pour éviter les problèmes write_pandas)
                for _, row in program_df.iterrows():
                    columns = list(row.index)
                    values = list(row.values)
                    cleaned_values = self._clean_values_for_sql(values)
                    placeholders = ", ".join(["%s"] * len(cleaned_values))
                    columns_str = ", ".join([f'"{col}"' for col in columns])
                    insert_sql = f'INSERT INTO "{db}"."{schema}"."{self.PROGRAMS}" ({columns_str}) VALUES ({placeholders})'
                    cur.execute(insert_sql, cleaned_values)

                # 2) Récupérer PROGRAM_ID
                program_id = self._program_id_by_title(cnx, db, schema, program_title)
                if program_id is None:
                    raise ValueError(f"Program '{program_title}' not found after insert")

                # 3) Préparer CONDITIONS/STRUCTURES/EXCLUSIONS via helpers communs

                # a) Compacter les dimensions multi-valeurs côté conditions
                # Regrouper par les colonnes qui définissent la condition + INSPER_ID_PRE
                dims = condition_dims_in(conditions_df)
                # Colonnes qui définissent la condition + l'ID de structure
                # Mais seulement celles qui ont des valeurs non-nulles dans le DataFrame
                condition_defining_cols = [
                    'INSPER_ID_PRE', 'CESSION_PCT', 'LIMIT_100', 'ATTACHMENT_POINT_100', 
                    'SIGNED_SHARE_PCT', 'INCLUDES_HULL', 'INCLUDES_LIABILITY'
                ]
                # Garder seulement les colonnes qui existent ET qui ont des valeurs non-nulles
                group_cols = []
                for c in condition_defining_cols:
                    if c in conditions_df.columns and not conditions_df[c].isna().all():
                        group_cols.append(c)
                conditions_compact = compact_multivalue(conditions_df, dims=dims, group_cols=group_cols)
                
                # b) Encoder seulement les exclusions pour stockage (list → "a;b")
                # Les conditions gardent leurs listes natives
                frames = ProgramFrames(program_df, structures_df, conditions_compact, exclusions_df)
                exclusions_encoded = frames.for_csv().exclusions

                # c) Injecter PROGRAM_ID
                structures_out = frames.structures.copy()
                conditions_out = frames.conditions.copy()  # Garde les listes natives
                exclusions_out = exclusions_encoded.copy()
                if "REINSURANCE_PROGRAM_ID" in structures_out.columns:
                    structures_out["PROGRAM_ID"] = program_id
                    structures_out.drop(columns=["REINSURANCE_PROGRAM_ID"], inplace=True, errors="ignore")
                else:
                    structures_out["PROGRAM_ID"] = program_id
                conditions_out["PROGRAM_ID"] = program_id
                exclusions_out["RP_ID"] = program_id

                # d) Garantir le jeu de colonnes attendu par les tables (ordre inclus)
                structures_cols = [
                    "PROGRAM_ID","BUSINESS_TITLE","TYPE_OF_PARTICIPATION_CD",
                    "INSPER_PREDECESSOR_TITLE","INSPER_CLAIM_BASIS_CD",
                    "INSPER_EFFECTIVE_DATE","INSPER_EXPIRY_DATE","INSPER_LAYER_NO",
                    "INSPER_MAIN_CURRENCY_CD","INSPER_UW_YEAR","INSPER_COMMENT"
                ]
                conditions_cols = [
                    "PROGRAM_ID","INSPER_ID_PRE","SIGNED_SHARE_PCT","CESSION_PCT",
                    "LIMIT_100","ATTACHMENT_POINT_100","INCLUDES_HULL","INCLUDES_LIABILITY",
                    # ajoute ici les dimensions présentes côté table
                    *[d for d in PROGRAM_TO_BORDEREAU_DIMENSIONS.keys() if d in conditions_out.columns],
                ]
                exclusions_cols = [
                    "RP_ID","EXCLUSION_NAME","EXCL_EFFECTIVE_DATE","EXCL_EXPIRY_DATE",
                    *[d for d in PROGRAM_TO_BORDEREAU_DIMENSIONS.keys() if d in exclusions_out.columns],
                ]

                structures_out = self._ensure_columns(structures_out, structures_cols)
                conditions_out = self._ensure_columns(conditions_out, conditions_cols)
                exclusions_out = self._ensure_columns(exclusions_out, exclusions_cols)

                # e) Ecriture (SQL direct pour éviter les problèmes write_pandas)
                for name, df in [
                    (self.STRUCTURES, structures_out),
                    (self.CONDITIONS, conditions_out),
                    (self.EXCLUSIONS, exclusions_out),
                ]:
                    if not df.empty:
                        for _, row in df.iterrows():
                            columns = list(row.index)
                            values = list(row.values)
                            cleaned_values = self._clean_values_for_sql(values)
                            placeholders = ", ".join(["%s"] * len(cleaned_values))
                            columns_str = ", ".join([f'"{col}"' for col in columns])
                            insert_sql = f'INSERT INTO "{db}"."{schema}"."{name}" ({columns_str}) VALUES ({placeholders})'
                            cur.execute(insert_sql, cleaned_values)
            finally:
                cur.close()
        finally:
            cnx.close()

    # ────────────────────────────────────────────────────────────────────
    # UTILS
    # ────────────────────────────────────────────────────────────────────
    def drop_all_tables(
        self, connection_params: Dict[str, Any], db: str, schema: str
    ) -> None:
        """Supprime toutes les tables (utile pour les tests)"""
        cnx = self._connect(connection_params)
        cur = cnx.cursor()
        try:
            for table in [
                self.EXCLUSIONS,
                self.CONDITIONS,
                self.STRUCTURES,
                self.PROGRAMS,
            ]:
                cur.execute(f'DROP TABLE IF EXISTS "{db}"."{schema}"."{table}"')
        finally:
            cur.close()
            cnx.close()