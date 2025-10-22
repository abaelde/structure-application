# src/io/run_snowflake_adapter.py
from __future__ import annotations
from typing import Optional, Dict, Any, Tuple
import pandas as pd
from src.io.snowflake_db import parse_db_schema, connect as sf_connect


class RunSnowflakeIO:
    """
    Persistance des 3 tables de run dans Snowflake (tables globales).
    DSN attendu: snowflake://DB.SCHEMA
    """

    RUNS = "RUNS"
    POLICIES = "RUN_POLICIES"
    STRUCTURES = "RUN_POLICY_STRUCTURES"

    def _ensure_tables(self, cnx, db: str, schema: str) -> None:
        ddl = f"""
        CREATE SCHEMA IF NOT EXISTS "{db}"."{schema}";
        CREATE TABLE IF NOT EXISTS "{db}"."{schema}"."{self.RUNS}" (
          RUN_ID            STRING PRIMARY KEY,
          PROGRAM_ID        STRING,
          PROGRAM_NAME      STRING,
          UW_DEPT           STRING,
          CALCULATION_DATE  STRING,
          SOURCE_PROGRAM    STRING,
          SOURCE_BORDEREAU  STRING,
          PROGRAM_FINGERPRINT STRING,
          STARTED_AT        STRING,
          ENDED_AT          STRING,
          ROW_COUNT         NUMBER,
          NOTES             STRING
        );
        CREATE TABLE IF NOT EXISTS "{db}"."{schema}"."{self.POLICIES}" (
          POLICY_RUN_ID         STRING PRIMARY KEY,
          RUN_ID                STRING,
          POLICY_ID             STRING,
          INSURED_NAME          STRING,
          INCEPTION_DT          STRING,
          EXPIRE_DT             STRING,
          EXCLUSION_STATUS      STRING,
          EXCLUSION_REASON      STRING,
          EXPOSURE              FLOAT,
          EFFECTIVE_EXPOSURE    FLOAT,
          CESSION_TO_LAYER_100PCT FLOAT,
          CESSION_TO_REINSURER  FLOAT,
          RETAINED_BY_CEDANT    FLOAT,
          RAW_RESULT_JSON       STRING
        );
        CREATE TABLE IF NOT EXISTS "{db}"."{schema}"."{self.STRUCTURES}" (
          STRUCTURE_ROW_ID        STRING PRIMARY KEY,
          POLICY_RUN_ID           STRING,
          STRUCTURE_NAME          STRING,
          TYPE_OF_PARTICIPATION   STRING,
          RP_STRUCTURE_ID_PREDECESSOR       STRING,
          CLAIM_BASIS             STRING,
          PERIOD_START            STRING,
          PERIOD_END              STRING,
          APPLIED                 BOOLEAN,
          REASON                  STRING,
          SCOPE                   STRING,
          INPUT_EXPOSURE          FLOAT,
          CEDED_TO_LAYER_100PCT   FLOAT,
          CEDED_TO_REINSURER      FLOAT,
          RETAINED_AFTER          FLOAT,
          TERMS_JSON              STRING,
          MATCHED_CONDITION_JSON  STRING,
          RESCALING_JSON          STRING,
          MATCHING_DETAILS_JSON   STRING,
          METRICS_JSON            STRING
        );
        """
        cur = cnx.cursor()
        try:
            for stmt in [s.strip() for s in ddl.split(";") if s.strip()]:
                cur.execute(stmt)
        finally:
            cur.close()

    def write(
        self,
        dest_dsn: str,
        runs_df: pd.DataFrame,
        run_policies_df: pd.DataFrame,
        run_policy_structures_df: pd.DataFrame,
        *,
        connection_params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> None:
        from snowflake.connector.pandas_tools import write_pandas

        db, schema, _ = parse_db_schema(dest_dsn)
        cnx = sf_connect(connection_params or {})
        try:
            self._ensure_tables(cnx, db, schema)

            for name, df in [
                (self.RUNS, runs_df),
                (self.POLICIES, run_policies_df),
                (self.STRUCTURES, run_policy_structures_df),
            ]:
                if not df.empty:
                    write_pandas(
                        cnx,
                        df,
                        table_name=name,
                        database=db,
                        schema=schema,
                        auto_create_table=False,
                        quote_identifiers=True,
                    )
        finally:
            cnx.close()

    def read(
        self,
        source_dsn: str,
        *,
        connection_params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        db, schema, _ = parse_db_schema(source_dsn)
        cnx = sf_connect(connection_params or {})
        try:
            self._ensure_tables(cnx, db, schema)

            runs = pd.read_sql(f'SELECT * FROM "{db}"."{schema}"."{self.RUNS}"', cnx)
            pols = pd.read_sql(
                f'SELECT * FROM "{db}"."{schema}"."{self.POLICIES}"', cnx
            )
            strs = pd.read_sql(
                f'SELECT * FROM "{db}"."{schema}"."{self.STRUCTURES}"', cnx
            )
            return runs, pols, strs
        finally:
            cnx.close()