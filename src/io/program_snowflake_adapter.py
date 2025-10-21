# src/io/program_snowflake_adapter.py
from __future__ import annotations
from typing import Tuple, Optional, Dict, Any, List
import json, uuid
import pandas as pd

class SnowflakeProgramIO:
    """
    Stocke tous les programmes dans des tables globales :
      - PROGRAMS, STRUCTURES, CONDITIONS, EXCLUSIONS
    Les colonnes "stables" sont scalaires ; le reste va dans payload (JSON texte).

    DSN attendu pour load/save :
      snowflake://DB.SCHEMA?program_id=...     OU
      snowflake://DB.SCHEMA?program_title=...

    connection_params: dict pour snowflake.connector.connect(...)
    if_exists (save) :
      - "append"             : ajoute un nouveau PROGRAM_ID
      - "replace_program"    : supprime le programme existant (même title ou id) puis ré-insère
      - "truncate_all"       : TRUNCATE des 4 tables avant insert (mode reset global)
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

    def _connect(self, connection_params: Optional[Dict[str, Any]]):
        import snowflake.connector
        return snowflake.connector.connect(**(connection_params or {}))

    def _ensure_tables(self, cnx, db: str, schema: str) -> None:
        ddl = f"""
        CREATE SCHEMA IF NOT EXISTS "{db}"."{schema}";
        CREATE TABLE IF NOT EXISTS "{db}"."{schema}"."{self.PROGRAMS}" (
          PROGRAM_ID STRING PRIMARY KEY,
          REPROG_TITLE STRING NOT NULL,
          REPROG_UW_DEPARTMENT_LOB_CD STRING NOT NULL,
          CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
          UPDATED_AT TIMESTAMP_NTZ,
          PAYLOAD STRING
        );
        CREATE TABLE IF NOT EXISTS "{db}"."{schema}"."{self.STRUCTURES}" (
          PROGRAM_ID STRING NOT NULL,
          INSPER_ID_PRE NUMBER NOT NULL,
          INSPER_CONTRACT_ORDER NUMBER,
          TYPE_OF_PARTICIPATION_CD STRING,
          INSPER_PREDECESSOR_TITLE STRING,
          INSPER_CLAIM_BASIS_CD STRING,
          INSPER_EFFECTIVE_DATE TIMESTAMP_NTZ,
          INSPER_EXPIRY_DATE TIMESTAMP_NTZ,
          PAYLOAD STRING,
          PRIMARY KEY (PROGRAM_ID, INSPER_ID_PRE)
        );
        CREATE TABLE IF NOT EXISTS "{db}"."{schema}"."{self.CONDITIONS}" (
          PROGRAM_ID STRING NOT NULL,
          INSPER_ID_PRE NUMBER NOT NULL,
          BUSCL_ID_PRE NUMBER NOT NULL,
          SIGNED_SHARE_PCT FLOAT,
          INCLUDES_HULL BOOLEAN,
          INCLUDES_LIABILITY BOOLEAN,
          PAYLOAD STRING,
          PRIMARY KEY (PROGRAM_ID, BUSCL_ID_PRE)
        );
        CREATE TABLE IF NOT EXISTS "{db}"."{schema}"."{self.EXCLUSIONS}" (
          PROGRAM_ID STRING NOT NULL,
          EXCL_REASON STRING,
          EXCL_EFFECTIVE_DATE TIMESTAMP_NTZ,
          EXCL_EXPIRY_DATE TIMESTAMP_NTZ,
          PAYLOAD STRING
        );
        """
        cur = cnx.cursor()
        try:
            for stmt in [s.strip() for s in ddl.split(";") if s.strip()]:
                cur.execute(stmt)
        finally:
            cur.close()

    # ────────────────────────────────────────────────────────────────────
    # API
    # ────────────────────────────────────────────────────────────────────
    def read(
        self,
        source: str,
        *,
        connection_params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        db, schema, params = self._parse_dsn(source)
        prog_id = params.get("program_id")
        prog_title = params.get("program_title")
        if not (prog_id or prog_title):
            raise ValueError("Provide ?program_id=... or ?program_title=... in DSN")

        cnx = self._connect(connection_params)
        try:
            self._ensure_tables(cnx, db, schema)
            cur = cnx.cursor()
            try:
                if prog_id:
                    cur.execute(f'SELECT * FROM "{db}"."{schema}"."{self.PROGRAMS}" WHERE PROGRAM_ID=%s', (prog_id,))
                else:
                    cur.execute(f'SELECT * FROM "{db}"."{schema}"."{self.PROGRAMS}" WHERE REPROG_TITLE=%s ORDER BY CREATED_AT DESC LIMIT 1', (prog_title,))
                row = cur.fetchone()
                if not row:
                    raise ValueError("Program not found in PROGRAMS")
                cols = [d[0] for d in cur.description]
                prog = dict(zip(cols, row))
                program_id = prog["PROGRAM_ID"]

                # DataFrames à reconstruire
                program_df = pd.DataFrame([{
                    "REPROG_ID_PRE": 1,
                    "REPROG_TITLE": prog["REPROG_TITLE"],
                    "REPROG_UW_DEPARTMENT_LOB_CD": prog["REPROG_UW_DEPARTMENT_LOB_CD"],
                }])

                # STRUCTURES (avec les colonnes timestamp)
                cur.execute(f'SELECT PROGRAM_ID, INSPER_ID_PRE, INSPER_CONTRACT_ORDER, TYPE_OF_PARTICIPATION_CD, INSPER_PREDECESSOR_TITLE, INSPER_CLAIM_BASIS_CD, INSPER_EFFECTIVE_DATE, INSPER_EXPIRY_DATE, PAYLOAD FROM "{db}"."{schema}"."{self.STRUCTURES}" WHERE PROGRAM_ID=%s ORDER BY INSPER_CONTRACT_ORDER NULLS LAST, INSPER_ID_PRE', (program_id,))
                s_rows = cur.fetchall()
                s_cols = [d[0] for d in cur.description]
                structures = []
                for r in s_rows:
                    d = dict(zip(s_cols, r))
                    # le payload recontient toutes les colonnes du CSV original
                    payload = json.loads(d["PAYLOAD"]) if d.get("PAYLOAD") else {}
                    # on s'assure des colonnes attendues par le serializer
                    payload.update({
                        "INSPER_ID_PRE": d["INSPER_ID_PRE"],
                        "INSPER_CONTRACT_ORDER": d.get("INSPER_CONTRACT_ORDER"),
                        "TYPE_OF_PARTICIPATION_CD": d.get("TYPE_OF_PARTICIPATION_CD"),
                        "INSPER_PREDECESSOR_TITLE": d.get("INSPER_PREDECESSOR_TITLE"),
                        "INSPER_CLAIM_BASIS_CD": d.get("INSPER_CLAIM_BASIS_CD"),
                        "INSPER_EFFECTIVE_DATE": str(d.get("INSPER_EFFECTIVE_DATE")) if d.get("INSPER_EFFECTIVE_DATE") else None,
                        "INSPER_EXPIRY_DATE": str(d.get("INSPER_EXPIRY_DATE")) if d.get("INSPER_EXPIRY_DATE") else None,
                    })
                    structures.append(payload)
                structures_df = pd.DataFrame(structures) if structures else pd.DataFrame()

                # CONDITIONS
                cur.execute(f'SELECT PROGRAM_ID, INSPER_ID_PRE, BUSCL_ID_PRE, SIGNED_SHARE_PCT, INCLUDES_HULL, INCLUDES_LIABILITY, PAYLOAD FROM "{db}"."{schema}"."{self.CONDITIONS}" WHERE PROGRAM_ID=%s ORDER BY BUSCL_ID_PRE', (program_id,))
                c_rows = cur.fetchall()
                c_cols = [d[0] for d in cur.description]
                conditions = []
                for r in c_rows:
                    d = dict(zip(c_cols, r))
                    payload = json.loads(d["PAYLOAD"]) if d.get("PAYLOAD") else {}
                    payload.update({
                        "BUSCL_ID_PRE": d["BUSCL_ID_PRE"],
                        "INSPER_ID_PRE": d["INSPER_ID_PRE"],
                        "SIGNED_SHARE_PCT": d.get("SIGNED_SHARE_PCT"),
                        "INCLUDES_HULL": d.get("INCLUDES_HULL"),
                        "INCLUDES_LIABILITY": d.get("INCLUDES_LIABILITY"),
                    })
                    conditions.append(payload)
                conditions_df = pd.DataFrame(conditions) if conditions else pd.DataFrame()

                # EXCLUSIONS (sans les colonnes timestamp problématiques)
                cur.execute(f'SELECT PROGRAM_ID, EXCL_REASON, PAYLOAD FROM "{db}"."{schema}"."{self.EXCLUSIONS}" WHERE PROGRAM_ID=%s', (program_id,))
                e_rows = cur.fetchall()
                e_cols = [d[0] for d in cur.description]
                exclusions = []
                for r in e_rows:
                    d = dict(zip(e_cols, r))
                    payload = json.loads(d["PAYLOAD"]) if d.get("PAYLOAD") else {}
                    payload.update({
                        "EXCL_REASON": d.get("EXCL_REASON"),
                        # Les dates sont dans le payload JSON
                    })
                    exclusions.append(payload)
                exclusions_df = pd.DataFrame(exclusions) if exclusions else pd.DataFrame()

                return program_df, structures_df, conditions_df, exclusions_df

            finally:
                cur.close()
        finally:
            cnx.close()

    def write(
        self,
        dest: str,
        program_df: pd.DataFrame,
        structures_df: pd.DataFrame,
        conditions_df: pd.DataFrame,
        exclusions_df: pd.DataFrame,
        *,
        if_exists: str = "replace_program",
        connection_params: Optional[Dict[str, Any]] = None,
    ) -> None:
        from snowflake.connector.pandas_tools import write_pandas

        db, schema, params = self._parse_dsn(dest)
        prog_title = program_df.iloc[0]["REPROG_TITLE"]
        uw_dept = program_df.iloc[0]["REPROG_UW_DEPARTMENT_LOB_CD"]
        program_id = uuid.uuid4().hex

        cnx = self._connect(connection_params)
        try:
            self._ensure_tables(cnx, db, schema)

            cur = cnx.cursor()
            try:
                # Modes de réécriture
                if if_exists == "truncate_all":
                    for t in [self.PROGRAMS, self.STRUCTURES, self.CONDITIONS, self.EXCLUSIONS]:
                        cur.execute(f'TRUNCATE TABLE IF EXISTS "{db}"."{schema}"."{t}"')
                elif if_exists == "replace_program":
                    # supprime anciens enregistrements de ce programme (par titre)
                    cur.execute(
                        f'SELECT PROGRAM_ID FROM "{db}"."{schema}"."{self.PROGRAMS}" WHERE REPROG_TITLE=%s',
                        (prog_title,)
                    )
                    olds = [r[0] for r in cur.fetchall()]
                    if olds:
                        for t in [self.STRUCTURES, self.CONDITIONS, self.EXCLUSIONS]:
                            cur.execute(f'DELETE FROM "{db}"."{schema}"."{t}" WHERE PROGRAM_ID IN ({",".join(["%s"]*len(olds))})', tuple(olds))
                        cur.execute(f'DELETE FROM "{db}"."{schema}"."{self.PROGRAMS}" WHERE PROGRAM_ID IN ({",".join(["%s"]*len(olds))})', tuple(olds))

                # PROGRAM
                prog_df = pd.DataFrame([{
                    "PROGRAM_ID": program_id,
                    "REPROG_TITLE": prog_title,
                    "REPROG_UW_DEPARTMENT_LOB_CD": uw_dept,
                    "PAYLOAD": json.dumps(program_df.to_dict("records")[0], ensure_ascii=False),
                }])
                write_pandas(cnx, prog_df, table_name=self.PROGRAMS, database=db, schema=schema, auto_create_table=False, quote_identifiers=True)

                # STRUCTURES
                if not structures_df.empty:
                    s_rows: List[Dict[str, Any]] = []
                    for _, r in structures_df.iterrows():
                        # Convertir les Timestamps en strings pour la sérialisation JSON
                        row_dict = r.to_dict()
                        for key, value in row_dict.items():
                            if hasattr(value, 'strftime'):  # Timestamp ou datetime
                                row_dict[key] = value.strftime('%Y-%m-%d %H:%M:%S') if value else None
                        payload = json.dumps(row_dict, ensure_ascii=False)
                        # Convertir les timestamps en format string pour Snowflake
                        effective_date = r.get("INSPER_EFFECTIVE_DATE")
                        expiry_date = r.get("INSPER_EXPIRY_DATE")
                        
                        if effective_date and hasattr(effective_date, 'strftime'):
                            effective_date = effective_date.strftime('%Y-%m-%d %H:%M:%S')
                        if expiry_date and hasattr(expiry_date, 'strftime'):
                            expiry_date = expiry_date.strftime('%Y-%m-%d %H:%M:%S')
                        
                        s_rows.append({
                            "PROGRAM_ID": program_id,
                            "INSPER_ID_PRE": r.get("INSPER_ID_PRE"),
                            "INSPER_CONTRACT_ORDER": r.get("INSPER_CONTRACT_ORDER"),
                            "TYPE_OF_PARTICIPATION_CD": r.get("TYPE_OF_PARTICIPATION_CD"),
                            "INSPER_PREDECESSOR_TITLE": r.get("INSPER_PREDECESSOR_TITLE"),
                            "INSPER_CLAIM_BASIS_CD": r.get("INSPER_CLAIM_BASIS_CD"),
                            "INSPER_EFFECTIVE_DATE": effective_date,
                            "INSPER_EXPIRY_DATE": expiry_date,
                            "PAYLOAD": payload,
                        })
                    write_pandas(cnx, pd.DataFrame(s_rows), table_name=self.STRUCTURES, database=db, schema=schema, auto_create_table=False, quote_identifiers=True)

                # CONDITIONS
                if not conditions_df.empty:
                    c_rows: List[Dict[str, Any]] = []
                    for _, r in conditions_df.iterrows():
                        # Convertir les Timestamps en strings pour la sérialisation JSON
                        row_dict = r.to_dict()
                        for key, value in row_dict.items():
                            if hasattr(value, 'strftime'):  # Timestamp ou datetime
                                row_dict[key] = value.strftime('%Y-%m-%d %H:%M:%S') if value else None
                        payload = json.dumps(row_dict, ensure_ascii=False)
                        c_rows.append({
                            "PROGRAM_ID": program_id,
                            "INSPER_ID_PRE": r.get("INSPER_ID_PRE"),
                            "BUSCL_ID_PRE": r.get("BUSCL_ID_PRE"),
                            "SIGNED_SHARE_PCT": r.get("SIGNED_SHARE_PCT"),
                            "INCLUDES_HULL": r.get("INCLUDES_HULL"),
                            "INCLUDES_LIABILITY": r.get("INCLUDES_LIABILITY"),
                            "PAYLOAD": payload,
                        })
                    write_pandas(cnx, pd.DataFrame(c_rows), table_name=self.CONDITIONS, database=db, schema=schema, auto_create_table=False, quote_identifiers=True)

                # EXCLUSIONS
                if exclusions_df is not None and not exclusions_df.empty:
                    e_rows: List[Dict[str, Any]] = []
                    for _, r in exclusions_df.iterrows():
                        # Convertir les Timestamps en strings pour la sérialisation JSON
                        row_dict = r.to_dict()
                        for key, value in row_dict.items():
                            if hasattr(value, 'strftime'):  # Timestamp ou datetime
                                row_dict[key] = value.strftime('%Y-%m-%d %H:%M:%S') if value else None
                        payload = json.dumps(row_dict, ensure_ascii=False)
                        e_rows.append({
                            "PROGRAM_ID": program_id,
                            "EXCL_REASON": r.get("EXCL_REASON"),
                            "EXCL_EFFECTIVE_DATE": r.get("EXCL_EFFECTIVE_DATE"),
                            "EXCL_EXPIRY_DATE": r.get("EXCL_EXPIRY_DATE"),
                            "PAYLOAD": payload,
                        })
                    write_pandas(cnx, pd.DataFrame(e_rows), table_name=self.EXCLUSIONS, database=db, schema=schema, auto_create_table=False, quote_identifiers=True)

            finally:
                cur.close()
        finally:
            cnx.close()

    # Helpers admin
    def drop_all_tables(self, dsn: str, *, connection_params: Optional[Dict[str, Any]] = None) -> None:
        db, schema, _ = self._parse_dsn(dsn)
        cnx = self._connect(connection_params)
        try:
            cur = cnx.cursor()
            try:
                for t in [self.EXCLUSIONS, self.CONDITIONS, self.STRUCTURES, self.PROGRAMS]:
                    cur.execute(f'DROP TABLE IF EXISTS "{db}"."{schema}"."{t}"')
            finally:
                cur.close()
        finally:
            cnx.close()