# src/io/program_snowflake_adapter.py
# IMPORTANT :
# INSPER_ID_PRE / RP_STRUCTURE_ID sont des identifiants "locaux" au programme (1..n).
# Toute lecture/suppression de RP_CONDITIONS DOIT être scopée par RP_ID via un JOIN avec RP_STRUCTURES.
# Ne jamais filtrer RP_CONDITIONS uniquement par INSPER_ID_PRE avec IN (...).
from __future__ import annotations
from typing import Tuple, Optional, Dict, Any, List
import pandas as pd
import snowflake.connector
from src.domain.schema import PROGRAM_TO_BORDEREAU_DIMENSIONS
from src.serialization.program_frames import ProgramFrames, condition_dims_in


class SnowflakeProgramIO:
    PROGRAMS = "REINSURANCE_PROGRAM"
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
        from urllib.parse import urlparse, parse_qsl
        
        p = urlparse(source)
        if p.scheme.lower() != "snowflake":
            raise ValueError("Invalid Snowflake DSN")
        
        # Handle both formats: snowflake://DB.SCHEMA and snowflake://host/DB.SCHEMA
        if p.path and p.path != "/":
            # Format: snowflake://host/DB.SCHEMA
            path_without_slash = p.path.lstrip("/")
            if path_without_slash.count(".") != 1:
                raise ValueError("DSN must be snowflake://DB.SCHEMA?...")
            db, schema = path_without_slash.split(".")
        else:
            # Format: snowflake://DB.SCHEMA
            if not p.netloc or p.netloc.count(".") != 1:
                raise ValueError("DSN must be snowflake://DB.SCHEMA?...")
            db, schema = p.netloc.split(".")
        
        params = dict(parse_qsl(p.query))
        return db, schema, params

    def _connect(self, connection_params: Dict[str, Any]):
        return snowflake.connector.connect(**connection_params)

    def _program_id_by_title(
        self, cnx, db: str, schema: str, title: str
    ) -> Optional[int]:
        cur = cnx.cursor()
        try:
            cur.execute(
                f'SELECT REINSURANCE_PROGRAM_ID FROM "{db}"."{schema}"."{self.PROGRAMS}" WHERE TITLE=%s',
                (title,),
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

    def read(
        self,
        source: str,
        connection_params: Dict[str, Any],
        program_title: Optional[str] = None,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Lit un programme depuis Snowflake.
        Retourne (program_df, structures_df, conditions_df, exclusions_df, field_links_df)
        """
        db, schema, params = self._parse_dsn(source)

        cnx = self._connect(connection_params)
        cur = cnx.cursor()
        try:
            # 1. Lire le programme
            if program_title:
                cur.execute(
                    f'SELECT * FROM "{db}"."{schema}"."{self.PROGRAMS}" WHERE TITLE=%s',
                    (program_title,),
                )
            else:
                cur.execute(f'SELECT * FROM "{db}"."{schema}"."{self.PROGRAMS}"')

            program_rows = cur.fetchall()
            if not program_rows:
                raise ValueError(f"Program '{program_title}' not found")

            program_df = pd.DataFrame(
                program_rows, columns=[desc[0] for desc in cur.description]
            )

            # 2. Lire les structures
            program_id = int(program_df.iloc[0]["REINSURANCE_PROGRAM_ID"])
            cur.execute(
                f'''
                SELECT 
                    RP_STRUCTURE_ID,
                    RP_ID,
                    RP_STRUCTURE_NAME,
                    TYPE_OF_PARTICIPATION,
                    CLAIMS_BASIS,
                    EFFECTIVE_DATE,
                    EXPIRY_DATE,
                    RP_STRUCTURE_ID_PREDECESSOR,
                    T_NUMBER,
                    LAYER_NUMBER,
                    INSURED_PERIOD_TYPE,
                    CLASS_OF_BUSINESS,
                    MAIN_CURRENCY,
                    UW_YEAR,
                    COMMENT,
                    -- Cast des valeurs numériques en FLOAT
                    CAST(LIMIT_100 AS FLOAT) AS LIMIT_100,
                    CAST(ATTACHMENT_POINT_100 AS FLOAT) AS ATTACHMENT_POINT_100,
                    CAST(CESSION_PCT AS FLOAT) AS CESSION_PCT,
                    CAST(RETENTION_PCT AS FLOAT) AS RETENTION_PCT,
                    CAST(SUPI_100 AS FLOAT) AS SUPI_100,
                    BUSCL_PREMIUM_CURRENCY_CD,
                    BUSCL_PREMIUM_GROSS_NET_CD,
                    CAST(PREMIUM_RATE_PCT AS FLOAT) AS PREMIUM_RATE_PCT,
                    CAST(PREMIUM_DEPOSIT_100 AS FLOAT) AS PREMIUM_DEPOSIT_100,
                    CAST(PREMIUM_MIN_100 AS FLOAT) AS PREMIUM_MIN_100,
                    CAST(BUSCL_LIABILITY_1_LINE_100 AS FLOAT) AS BUSCL_LIABILITY_1_LINE_100,
                    CAST(MAX_COVER_PCT AS FLOAT) AS MAX_COVER_PCT,
                    CAST(MIN_EXCESS_PCT AS FLOAT) AS MIN_EXCESS_PCT,
                    CAST(SIGNED_SHARE_PCT AS FLOAT) AS SIGNED_SHARE_PCT,
                    CAST(AVERAGE_LINE_SLAV_CED AS FLOAT) AS AVERAGE_LINE_SLAV_CED,
                    CAST(PML_DEFAULT_PCT AS FLOAT) AS PML_DEFAULT_PCT,
                    CAST(LIMIT_EVENT AS FLOAT) AS LIMIT_EVENT,
                    NO_OF_REINSTATEMENTS
                FROM "{db}"."{schema}"."{self.STRUCTURES}" 
                WHERE RP_ID=%s
                ''',
                (program_id,),
            )
            structures_rows = cur.fetchall()
            structures_df = pd.DataFrame(
                structures_rows, columns=[desc[0] for desc in cur.description]
            )

            # 3. Lire les conditions (scopées par RP_ID)
            cur.execute(
                f'''
                SELECT 
                    c.RP_CONDITION_ID,
                    c.RP_ID,
                    c.COUNTRY_ID,
                    c.REGION_ID,
                    c.PRODUCT_TYPE_LEVEL_1,
                    c.PRODUCT_TYPE_LEVEL_2,
                    c.PRODUCT_TYPE_LEVEL_3,
                    c.CURRENCY_ID,
                    c.INCLUDES_HULL,
                    c.INCLUDES_LIABILITY
                FROM "{db}"."{schema}"."{self.CONDITIONS}" c
                WHERE c.RP_ID = %s
                ORDER BY c.RP_CONDITION_ID
                ''',
                (program_id,),
            )
            conditions_rows = cur.fetchall()
            conditions_df = pd.DataFrame(
                conditions_rows, columns=[desc[0] for desc in cur.description]
            )

            # 4. Lire les RP_STRUCTURE_FIELD_LINK pour les overrides
            cur.execute(
                f'''
                SELECT 
                    fl.RP_STRUCTURE_FIELD_LINK_ID,
                    fl.RP_CONDITION_ID,
                    fl.RP_STRUCTURE_ID,
                    fl.FIELD_NAME,
                    -- Cast NEW_VALUE en FLOAT pour les valeurs numériques
                    CASE 
                        WHEN fl.FIELD_NAME IN ('CESSION_PCT', 'LIMIT_100', 'ATTACHMENT_POINT_100', 'SIGNED_SHARE_PCT') 
                        THEN CAST(fl.NEW_VALUE AS FLOAT)
                        ELSE fl.NEW_VALUE
                    END AS NEW_VALUE
                FROM "{db}"."{schema}"."RP_STRUCTURE_FIELD_LINK" fl
                JOIN "{db}"."{schema}"."{self.CONDITIONS}" c
                  ON fl.RP_CONDITION_ID = c.RP_CONDITION_ID
                WHERE c.RP_ID = %s
                ORDER BY fl.RP_STRUCTURE_FIELD_LINK_ID
                ''',
                (program_id,),
            )
            field_links_rows = cur.fetchall()
            field_links_df = pd.DataFrame(
                field_links_rows, columns=[desc[0] for desc in cur.description]
            )

            # 5. Lire les exclusions
            cur.execute(
                f'SELECT * FROM "{db}"."{schema}"."{self.EXCLUSIONS}" WHERE RP_ID=%s',
                (program_id,),
            )
            exclusions_rows = cur.fetchall()
            exclusions_df = pd.DataFrame(
                exclusions_rows, columns=[desc[0] for desc in cur.description]
            )

            return program_df, structures_df, conditions_df, exclusions_df, field_links_df

        finally:
            cur.close()
            cnx.close()

    def write(
        self,
        dest: str,
        program_df: pd.DataFrame,
        structures_df: pd.DataFrame,
        conditions_df: pd.DataFrame,
        exclusions_df: pd.DataFrame,
        field_links_df: pd.DataFrame,
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
                    for t in [
                        self.EXCLUSIONS,
                        self.CONDITIONS,
                        self.STRUCTURES,
                        self.PROGRAMS,
                    ]:
                        cur.execute(f'TRUNCATE TABLE "{db}"."{schema}"."{t}"')
                elif if_exists == "replace_program":
                    existing = self._program_id_by_title(cnx, db, schema, program_title)
                    if existing is not None:
                        # 0) Supprimer d'abord les FIELD_LINKs (FK sur structures/conditions)
                        cur.execute(
                            f'''
                            DELETE FROM "{db}"."{schema}"."RP_STRUCTURE_FIELD_LINK"
                            WHERE RP_STRUCTURE_ID IN (
                                SELECT RP_STRUCTURE_ID FROM "{db}"."{schema}"."{self.STRUCTURES}" WHERE RP_ID=%s
                            )
                               OR RP_CONDITION_ID IN (
                                SELECT RP_CONDITION_ID FROM "{db}"."{schema}"."{self.CONDITIONS}" WHERE RP_ID=%s
                            )
                            ''',
                            (existing, existing),
                        )
                        cur.execute(
                            f'DELETE FROM "{db}"."{schema}"."{self.EXCLUSIONS}" WHERE RP_ID=%s',
                            (existing,),
                        )
                        # Conditions désormais scopées par RP_ID
                        cur.execute(
                            f'DELETE FROM "{db}"."{schema}"."{self.CONDITIONS}" WHERE RP_ID=%s',
                            (existing,),
                        )
                        cur.execute(
                            f'DELETE FROM "{db}"."{schema}"."{self.STRUCTURES}" WHERE RP_ID=%s',
                            (existing,),
                        )
                        cur.execute(
                            f'DELETE FROM "{db}"."{schema}"."{self.PROGRAMS}"   WHERE REINSURANCE_PROGRAM_ID=%s',
                            (existing,),
                        )

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
                    raise ValueError(
                        f"Program '{program_title}' not found after insert"
                    )

                # 3) Préparer CONDITIONS/STRUCTURES/EXCLUSIONS via helpers communs
                dims = condition_dims_in(conditions_df)

                condition_defining_cols = [
                    "CESSION_PCT",
                    "LIMIT_100",
                    "ATTACHMENT_POINT_100",
                    "SIGNED_SHARE_PCT",
                    "INCLUDES_HULL",
                    "INCLUDES_LIABILITY",
                ]
                # Garder seulement les colonnes qui existent ET qui ont des valeurs non-nulles
                group_cols = []
                for c in condition_defining_cols:
                    if c in conditions_df.columns and not conditions_df[c].isna().all():
                        group_cols.append(c)
                # Ne pas compacter les conditions pour préserver INSPER_ID_PRE
                conditions_compact = conditions_df.copy()

                frames = ProgramFrames(
                    program_df, structures_df, conditions_compact, exclusions_df
                )
                exclusions_encoded = frames.for_csv().exclusions

                # c) Injecter RP_ID et mapper les colonnes
                structures_out = frames.structures.copy()
                conditions_out = frames.conditions.copy()  # Garde les listes natives
                exclusions_out = exclusions_encoded.copy()
                
                # Ajouter RP_ID pour les structures
                structures_out["RP_ID"] = program_id
                
                # Les conditions n'ont plus RP_ID, elles sont liées via INSPER_ID_PRE
                exclusions_out["RP_ID"] = program_id

                # d) Garantir le jeu de colonnes attendu par les tables (ordre inclus)
                structures_cols = [
                    "RP_ID",
                    "RP_STRUCTURE_NAME",
                    "TYPE_OF_PARTICIPATION",
                    "CLAIMS_BASIS",
                    "EFFECTIVE_DATE",
                    "EXPIRY_DATE",
                    "RP_STRUCTURE_ID_PREDECESSOR",
                    "T_NUMBER",
                    "LAYER_NUMBER",
                    "INSURED_PERIOD_TYPE",
                    "CLASS_OF_BUSINESS",
                    "MAIN_CURRENCY",
                    "UW_YEAR",
                    "COMMENT",
                    # Champs financiers par défaut
                    "LIMIT_100",
                    "ATTACHMENT_POINT_100",
                    "CESSION_PCT",
                    "RETENTION_PCT",
                    "SUPI_100",
                    "BUSCL_PREMIUM_CURRENCY_CD",
                    "BUSCL_PREMIUM_GROSS_NET_CD",
                    "PREMIUM_RATE_PCT",
                    "PREMIUM_DEPOSIT_100",
                    "PREMIUM_MIN_100",
                    "BUSCL_LIABILITY_1_LINE_100",
                    "MAX_COVER_PCT",
                    "MIN_EXCESS_PCT",
                    "SIGNED_SHARE_PCT",
                    "AVERAGE_LINE_SLAV_CED",
                    "PML_DEFAULT_PCT",
                    "LIMIT_EVENT",
                    "NO_OF_REINSTATEMENTS",
                ]
                conditions_cols = [
                    "RP_CONDITION_ID",
                    "RP_ID",
                    "COUNTRY_ID",
                    "REGION_ID",
                    "PRODUCT_TYPE_LEVEL_1",
                    "PRODUCT_TYPE_LEVEL_2",
                    "PRODUCT_TYPE_LEVEL_3",
                    "CURRENCY_ID",
                    "INCLUDES_HULL",
                    "INCLUDES_LIABILITY",
                ]
                field_links_cols = [
                    "RP_CONDITION_ID",
                    "RP_STRUCTURE_ID",
                    "FIELD_NAME",
                    "NEW_VALUE",
                ]
                exclusions_cols = [
                    "RP_ID",
                    "EXCLUSION_NAME",
                    "EXCL_EFFECTIVE_DATE",
                    "EXCL_EXPIRY_DATE",
                    *[
                        d
                        for d in PROGRAM_TO_BORDEREAU_DIMENSIONS.keys()
                        if d in exclusions_out.columns
                    ],
                ]

                # Ne pas réorganiser les colonnes - garder l'ordre naturel du DataFrame
                # structures_out = self._ensure_columns(structures_out, structures_cols)
                # conditions_out = self._ensure_columns(conditions_out, conditions_cols)
                # exclusions_out = self._ensure_columns(exclusions_out, exclusions_cols)

                # e) Écriture en 3 étapes : STRUCTURES -> mapping -> CONDITIONS -> EXCLUSIONS

                # (1) Insérer les STRUCTURES en laissant Snowflake générer RP_STRUCTURE_ID (AUTOINCREMENT)
                #     => on N'INSÈRE PAS la colonne "RP_STRUCTURE_ID"
                if not structures_out.empty:
                    # Sanity: on s'appuie sur l'unicité du nom dans un programme pour remapper ensuite
                    if structures_out["RP_STRUCTURE_NAME"].duplicated().any():
                        raise ValueError(
                            "RP_STRUCTURE_NAME must be unique within a program to remap generated IDs."
                        )
                    # On garde un mapping local_id -> name avant drop
                    local_to_name = dict(
                        zip(
                            structures_out.get("RP_STRUCTURE_ID", pd.Series(range(1, len(structures_out)+1))),
                            structures_out["RP_STRUCTURE_NAME"],
                        )
                    )
                    structures_for_insert = structures_out.drop(
                        columns=["RP_STRUCTURE_ID"], errors="ignore"
                    )
                    for _, row in structures_for_insert.iterrows():
                        columns = list(row.index)
                        values = list(row.values)
                        cleaned_values = self._clean_values_for_sql(values)
                        placeholders = ", ".join(["%s"] * len(cleaned_values))
                        columns_str = ", ".join([f'"{col}"' for col in columns])
                        insert_sql = (
                            f'INSERT INTO "{db}"."{schema}"."{self.STRUCTURES}" '
                            f'({columns_str}) VALUES ({placeholders})'
                        )
                        cur.execute(insert_sql, cleaned_values)

                    # Récupérer les IDs générés : name -> RP_STRUCTURE_ID pour ce programme
                    cur.execute(
                        f'SELECT RP_STRUCTURE_ID, RP_STRUCTURE_NAME '
                        f'FROM "{db}"."{schema}"."{self.STRUCTURES}" '
                        f'WHERE RP_ID=%s',
                        (program_id,),
                    )
                    rows = cur.fetchall()
                    name_to_dbid = {r[1]: int(r[0]) for r in rows}
                    # Mapping local -> dbid via le nom
                    local_to_dbid = {loc: name_to_dbid.get(nm) for loc, nm in local_to_name.items()}
                    if any(v is None for v in local_to_dbid.values()):
                        missing = [k for k, v in local_to_dbid.items() if v is None]
                        raise ValueError(
                            f"Cannot map local structure IDs to generated IDs (missing for locals: {missing})."
                        )

                    # (1bis) Remapper les FIELD_LINKS sur les vrais RP_STRUCTURE_ID
                    field_links_out = field_links_df.copy() if field_links_df is not None else pd.DataFrame(columns=[])
                    if not field_links_out.empty:
                        if "RP_STRUCTURE_ID" not in field_links_out.columns:
                            raise ValueError("FIELD_LINKS must contain RP_STRUCTURE_ID")
                        field_links_out["RP_STRUCTURE_ID"] = field_links_out["RP_STRUCTURE_ID"].map(local_to_dbid)
                        if field_links_out["RP_STRUCTURE_ID"].isna().any():
                            raise ValueError("Some FIELD_LINKS could not be mapped to generated RP_STRUCTURE_IDs")

                    # (2) Insérer les CONDITIONS (RP_ID + réassignation d'un ID global unique)
                    if not conditions_out.empty:
                        conditions_out = conditions_out.copy()
                        # Ajouter RP_ID aux conditions
                        conditions_out["RP_ID"] = program_id
                        # Réassigner RP_CONDITION_ID pour éviter toute collision globale
                        cur.execute(
                            f'SELECT COALESCE(MAX(RP_CONDITION_ID), 0) FROM "{db}"."{schema}"."{self.CONDITIONS}"'
                        )
                        start_id = int(cur.fetchone()[0] or 0)
                        cond_id_map = {}
                        rows_to_insert = []
                        for i, row in conditions_out.iterrows():
                            old_id = row.get("RP_CONDITION_ID", None)
                            new_id = start_id + len(cond_id_map) + 1
                            cond_id_map[old_id] = new_id
                            r = row.copy()
                            r["RP_CONDITION_ID"] = new_id
                            rows_to_insert.append(r)
                        # Insert
                        for r in rows_to_insert:
                            columns = list(r.index)
                            values = list(r.values)
                            cleaned_values = self._clean_values_for_sql(values)
                            placeholders = ", ".join(["%s"] * len(cleaned_values))
                            columns_str = ", ".join([f'"{col}"' for col in columns])
                            insert_sql = (
                                f'INSERT INTO "{db}"."{schema}"."{self.CONDITIONS}" '
                                f'({columns_str}) VALUES ({placeholders})'
                            )
                            cur.execute(insert_sql, cleaned_values)

                        # Remapper les FIELD_LINKS sur les nouveaux RP_CONDITION_ID
                        if not field_links_out.empty:
                            if "RP_CONDITION_ID" not in field_links_out.columns:
                                raise ValueError("FIELD_LINKS must contain RP_CONDITION_ID")
                            field_links_out["RP_CONDITION_ID"] = field_links_out["RP_CONDITION_ID"].map(cond_id_map)
                            if field_links_out["RP_CONDITION_ID"].isna().any():
                                raise ValueError("Some FIELD_LINKS could not be mapped to generated RP_CONDITION_IDs")

                    # (3) Insérer les RP_STRUCTURE_FIELD_LINK pour les overrides
                    if not (field_links_out is None or field_links_out.empty):
                        for _, row in field_links_out.iterrows():
                            columns = list(row.index)
                            values = list(row.values)
                            cleaned_values = self._clean_values_for_sql(values)
                            placeholders = ", ".join(["%s"] * len(cleaned_values))
                            columns_str = ", ".join([f'"{col}"' for col in columns])
                            insert_sql = (
                                f'INSERT INTO "{db}"."{schema}"."RP_STRUCTURE_FIELD_LINK" '
                                f'({columns_str}) VALUES ({placeholders})'
                            )
                            cur.execute(insert_sql, cleaned_values)
                else:
                    # Pas de structure -> pas de condition
                    if not conditions_out.empty:
                        raise ValueError("Conditions provided but no structures to attach to.")

                # (3) Insérer les EXCLUSIONS (liées au RP_ID)
                if not exclusions_out.empty:
                    for _, row in exclusions_out.iterrows():
                        columns = list(row.index)
                        values = list(row.values)
                        cleaned_values = self._clean_values_for_sql(values)
                        placeholders = ", ".join(["%s"] * len(cleaned_values))
                        columns_str = ", ".join([f'"{col}"' for col in columns])
                        insert_sql = (
                            f'INSERT INTO "{db}"."{schema}"."{self.EXCLUSIONS}" '
                            f'({columns_str}) VALUES ({placeholders})'
                        )
                        cur.execute(insert_sql, cleaned_values)
            finally:
                cur.close()
        finally:
            cnx.close()
