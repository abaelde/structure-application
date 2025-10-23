# src/io/program_snowflake_adapter.py
# IMPORTANT :
# INSPER_ID_PRE / RP_STRUCTURE_ID sont des identifiants "locaux" au programme (1..n).
# Toute lecture/suppression de RP_CONDITIONS DOIT être scopée par REINSURANCE_PROGRAM_ID via un JOIN avec RP_STRUCTURES.
# Ne jamais filtrer RP_CONDITIONS uniquement par INSPER_ID_PRE avec IN (...).
from __future__ import annotations
from typing import Tuple, Optional, Dict, Any, List
import pandas as pd
from src.serialization.program_frames import ProgramFrames, condition_dims_in
from src.io.snowflake_db import parse_db_schema, connect as sf_connect, insert_df


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


    def read(
        self,
        source: str,
        connection_params: Dict[str, Any],
        program_id: Optional[int] = None,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Lit un programme depuis Snowflake par son ID.
        Retourne (program_df, structures_df, conditions_df, exclusions_df, field_links_df)
        """
        if not program_id:
            raise ValueError("program_id is required for Snowflake program loading")
            
        db, schema, params = parse_db_schema(source)
        cnx = sf_connect(connection_params)
        cur = cnx.cursor()
        try:
            # 1. Lire le programme par ID
            cur.execute(
                f'SELECT * FROM "{db}"."{schema}"."{self.PROGRAMS}" WHERE REINSURANCE_PROGRAM_ID=%s',
                (program_id,),
            )

            program_rows = cur.fetchall()
            if not program_rows:
                raise ValueError(f"Program with ID {program_id} not found")

            program_df = pd.DataFrame(
                program_rows, columns=[desc[0] for desc in cur.description]
            )

            # 2. Lire les structures
            program_id = int(program_df.iloc[0]["REINSURANCE_PROGRAM_ID"])
            cur.execute(
                f'''
                SELECT 
                    RP_STRUCTURE_ID,
                    REINSURANCE_PROGRAM_ID,
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
                WHERE REINSURANCE_PROGRAM_ID=%s
                ''',
                (program_id,),
            )
            structures_rows = cur.fetchall()
            structures_df = pd.DataFrame(
                structures_rows, columns=[desc[0] for desc in cur.description]
            )

            # 3. Lire les conditions (scopées par REINSURANCE_PROGRAM_ID)
            cur.execute(
                f'''
                SELECT 
                    c.RP_CONDITION_ID,
                    c.REINSURANCE_PROGRAM_ID,
                    c.COUNTRIES,
                    c.REGIONS,
                    c.PRODUCT_TYPE_LEVEL_1,
                    c.PRODUCT_TYPE_LEVEL_2,
                    c.PRODUCT_TYPE_LEVEL_3,
                    c.CURRENCIES,
                    c.INCLUDES_HULL,
                    c.INCLUDES_LIABILITY
                FROM "{db}"."{schema}"."{self.CONDITIONS}" c
                WHERE c.REINSURANCE_PROGRAM_ID = %s
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
                WHERE c.REINSURANCE_PROGRAM_ID = %s
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
                f'SELECT * FROM "{db}"."{schema}"."{self.EXCLUSIONS}" WHERE REINSURANCE_PROGRAM_ID=%s',
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
    ) -> None:
        db, schema, params = parse_db_schema(dest)

        cnx = sf_connect(connection_params)
        try:
            cur = cnx.cursor()
            try:
                # 1) Insérer le nouveau programme (toujours un nouveau programme)
                # Supprimer l'ID du DataFrame pour laisser Snowflake le générer
                program_df_for_insert = program_df.copy()
                if 'REINSURANCE_PROGRAM_ID' in program_df_for_insert.columns:
                    program_df_for_insert = program_df_for_insert.drop(columns=['REINSURANCE_PROGRAM_ID'])
                
                insert_df(cur, db=db, schema=schema, table=self.PROGRAMS, df=program_df_for_insert)

                # 2) Récupérer l'ID généré par Snowflake
                # Récupérer le dernier ID inséré
                cur.execute(
                    f'SELECT MAX(REINSURANCE_PROGRAM_ID) FROM "{db}"."{schema}"."{self.PROGRAMS}"'
                )
                result = cur.fetchone()
                if result is None or result[0] is None:
                    raise ValueError("No program ID found after insert")
                program_id = result[0]

                # 3) Préparer CONDITIONS/STRUCTURES/EXCLUSIONS via helpers communs
                dims = condition_dims_in(conditions_df)

                # Ne pas compacter les conditions pour préserver INSPER_ID_PRE
                conditions_compact = conditions_df.copy()

                frames = ProgramFrames(
                    program_df, structures_df, conditions_compact, exclusions_df
                )
                exclusions_encoded = frames.for_csv().exclusions

                # c) Injecter REINSURANCE_PROGRAM_ID et mapper les colonnes
                structures_out = frames.structures.copy()
                conditions_out = frames.conditions.copy()  # Garde les listes natives
                exclusions_out = exclusions_encoded.copy()
                
                # Ajouter REINSURANCE_PROGRAM_ID pour les structures
                structures_out["REINSURANCE_PROGRAM_ID"] = program_id
                
                # Les conditions n'ont plus REINSURANCE_PROGRAM_ID, elles sont liées via INSPER_ID_PRE
                exclusions_out["REINSURANCE_PROGRAM_ID"] = program_id

                # e) Écriture en 3 étapes : STRUCTURES -> mapping -> CONDITIONS -> EXCLUSIONS

                # (1) Insérer les STRUCTURES en laissant Snowflake générer RP_STRUCTURE_ID (AUTOINCREMENT)
                if not structures_out.empty:
                    if structures_out["RP_STRUCTURE_NAME"].duplicated().any():
                        raise ValueError(
                            "RP_STRUCTURE_NAME must be unique within a program to remap generated IDs."
                        )
                    # Mapping local_id -> name (avant drop)
                    local_to_name = dict(
                        zip(
                            structures_out.get("RP_STRUCTURE_ID", pd.Series(range(1, len(structures_out)+1))),
                            structures_out["RP_STRUCTURE_NAME"],
                        )
                    )
                    structures_for_insert = structures_out.drop(
                        columns=["RP_STRUCTURE_ID"], errors="ignore"
                    )
                    # INSERT batch
                    insert_df(cur, db=db, schema=schema, table=self.STRUCTURES, df=structures_for_insert)

                    # Récupérer les IDs générés : name -> RP_STRUCTURE_ID pour ce programme
                    cur.execute(
                        f'SELECT RP_STRUCTURE_ID, RP_STRUCTURE_NAME '
                        f'FROM "{db}"."{schema}"."{self.STRUCTURES}" '
                        f'WHERE REINSURANCE_PROGRAM_ID=%s',
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

                    # (2) Insérer les CONDITIONS (REINSURANCE_PROGRAM_ID + réassignation d'un ID global unique)
                    if not conditions_out.empty:
                        conditions_out = conditions_out.copy()
                        # Ajouter REINSURANCE_PROGRAM_ID aux conditions
                        conditions_out["REINSURANCE_PROGRAM_ID"] = program_id
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
                        # INSERT batch
                        if rows_to_insert:
                            conditions_to_insert = pd.DataFrame(rows_to_insert)
                            insert_df(cur, db=db, schema=schema, table=self.CONDITIONS, df=conditions_to_insert)

                        # Remapper les FIELD_LINKS sur les nouveaux RP_CONDITION_ID
                        if not field_links_out.empty:
                            if "RP_CONDITION_ID" not in field_links_out.columns:
                                raise ValueError("FIELD_LINKS must contain RP_CONDITION_ID")
                            field_links_out["RP_CONDITION_ID"] = field_links_out["RP_CONDITION_ID"].map(cond_id_map)
                            if field_links_out["RP_CONDITION_ID"].isna().any():
                                raise ValueError("Some FIELD_LINKS could not be mapped to generated RP_CONDITION_IDs")

                    # (3) Insérer les RP_STRUCTURE_FIELD_LINK pour les overrides
                    if not (field_links_out is None or field_links_out.empty):
                        insert_df(cur, db=db, schema=schema, table="RP_STRUCTURE_FIELD_LINK", df=field_links_out)
                else:
                    # Pas de structure -> pas de condition
                    if not conditions_out.empty:
                        raise ValueError("Conditions provided but no structures to attach to.")

                # (3) Insérer les EXCLUSIONS (liées au REINSURANCE_PROGRAM_ID)
                if not exclusions_out.empty:
                    insert_df(cur, db=db, schema=schema, table=self.EXCLUSIONS, df=exclusions_out)

            finally:
                cur.close()
        finally:
            cnx.close()