# src/io/snowflake_db.py
from __future__ import annotations
from urllib.parse import urlparse, parse_qsl
from typing import Dict, Any, Tuple
import pandas as pd
import snowflake.connector


# ── DSN parsing ──────────────────────────────────────────────────────────────
def parse_db_schema(dsn: str) -> Tuple[str, str, Dict[str, str]]:
    """
    Accepte :
      - snowflake://DB.SCHEMA
      - snowflake://host/DB.SCHEMA
      - avec ?param1=a&param2=b
    Retourne (db, schema, params).
    """
    p = urlparse(dsn)
    if p.scheme.lower() != "snowflake":
        raise ValueError("Invalid Snowflake DSN")
    if p.path and p.path != "/":
        path = p.path.lstrip("/")
        if path.count(".") != 1:
            raise ValueError("DSN must be snowflake://DB.SCHEMA?...")
        db, schema = path.split(".")
    else:
        if not p.netloc or p.netloc.count(".") != 1:
            raise ValueError("DSN must be snowflake://DB.SCHEMA?...")
        db, schema = p.netloc.split(".")
    return db, schema, dict(parse_qsl(p.query))


def parse_db_schema_table(dsn: str) -> Tuple[str, str, str, Dict[str, str]]:
    """
    Pour les IO 'table' (bordereau) :
      - snowflake://DB.SCHEMA.TABLE
      - snowflake://host/DB.SCHEMA.TABLE
    Retourne (db, schema, table, params).
    """
    p = urlparse(dsn)
    if p.scheme.lower() != "snowflake":
        raise ValueError("Invalid Snowflake DSN")
    ident = p.path.lstrip("/") if (p.path and p.path != "/") else p.netloc
    parts = [x for x in ident.split(".") if x]
    if len(parts) != 3:
        raise ValueError("Identifier must be snowflake://DB.SCHEMA.TABLE")
    db, schema, table = parts
    return db, schema, table, dict(parse_qsl(p.query))


# ── Connexion ────────────────────────────────────────────────────────────────
def connect(params: Dict[str, Any]):
    return snowflake.connector.connect(**(params or {}))


# ── Normalisation des cellules avant INSERT ──────────────────────────────────
def _clean_cell(v):
    if v is None:
        return None
    # pandas NA / NaT / Timestamp
    if isinstance(v, (float, int)) and pd.isna(v):
        return None
    if hasattr(pd, "NA") and v is pd.NA:
        return None
    if isinstance(v, pd.Timestamp):
        return v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, list):
        return ";".join(str(x) for x in v) if v else None
    # Convertir les types numpy en types Python natifs
    import numpy as np
    if isinstance(v, (np.integer, np.floating)):
        return v.item()  # Convertit np.int64(42) en int(42)
    return v


# ── INSERT générique (batch) ────────────────────────────────────────────────
def insert_df(cur, *, db: str, schema: str, table: str, df) -> None:
    """
    INSERT ... VALUES ... batched via executemany.
    Respecte l'ordre de df.columns et applique _clean_cell sur chaque valeur.
    """
    if df is None or df.empty:
        return
    cols = [f'"{c}"' for c in df.columns]
    placeholders = ", ".join(["%s"] * len(cols))
    sql = f'INSERT INTO "{db}"."{schema}"."{table}" ({", ".join(cols)}) VALUES ({placeholders})'
    rows = [tuple(_clean_cell(v) for v in df.iloc[i].tolist()) for i in range(len(df))]
    cur.executemany(sql, rows)
