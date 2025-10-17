# src/io/bordereau_snowflake_adapter.py
from __future__ import annotations
from typing import Optional, Dict, Any, Tuple
import pandas as pd

# Dépendances attendues (à installer côté projet):
#   pip install snowflake-connector-python
#   pip install snowflake-connector-python[pandas]

class SnowflakeBordereauIO:
    """
    Lecture/écriture d'un bordereau en table Snowflake.
    - source "snowflake://DB.SCHEMA.TABLE" => SELECT * FROM DB.SCHEMA.TABLE
    - ou param `sql=...` pour requêtes custom
    - `connection_params` : dict passé à snowflake.connector.connect(...)
    """

    def _parse_table_identifier(self, source: str) -> Tuple[str, str, str]:
        if not source.lower().startswith("snowflake://"):
            raise ValueError(f"Invalid Snowflake DSN: {source}")
        ident = source[len("snowflake://"):]
        parts = ident.split(".")
        if len(parts) != 3:
            raise ValueError("Snowflake identifier must be snowflake://DB.SCHEMA.TABLE")
        return parts[0], parts[1], parts[2]

    def read(
        self,
        source: str,
        *,
        sql: Optional[str] = None,
        connection_params: Optional[Dict[str, Any]] = None,
    ) -> pd.DataFrame:
        import snowflake.connector

        connection_params = connection_params or {}
        cnx = snowflake.connector.connect(**connection_params)
        try:
            if sql is None:
                db, schema, table = self._parse_table_identifier(source)
                sql = f'SELECT * FROM "{db}"."{schema}"."{table}"'
            cur = cnx.cursor()
            try:
                cur.execute(sql)
                df = cur.fetch_pandas_all()
                return df
            finally:
                cur.close()
        finally:
            cnx.close()

    def write(
        self,
        dest: str,
        df: pd.DataFrame,
        *,
        if_exists: str = "replace",  # "replace" | "append" (comportement conseillé à expliciter côté appelant)
        connection_params: Optional[Dict[str, Any]] = None,
        chunk_size: int = 10_000,
    ) -> None:
        import snowflake.connector
        from snowflake.connector.pandas_tools import write_pandas

        db, schema, table = self._parse_table_identifier(dest)
        connection_params = connection_params or {}
        cnx = snowflake.connector.connect(**connection_params)
        try:
            cur = cnx.cursor()
            try:
                cur.execute(f'USE DATABASE "{db}"')
                cur.execute(f'USE SCHEMA "{schema}"')
                if if_exists == "replace":
                    cur.execute(f'DROP TABLE IF EXISTS "{table}"')
                    # création automatique par write_pandas si absent
                # upload
                write_pandas(cnx, df, table_name=table, auto_create_table=True, quote_identifiers=True, chunk_size=chunk_size)
            finally:
                cur.close()
        finally:
            cnx.close()
