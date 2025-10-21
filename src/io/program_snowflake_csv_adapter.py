# src/io/program_snowflake_csv_adapter.py
from __future__ import annotations
from typing import Tuple, Optional, Dict, Any, List
import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
from src.domain.schema import PROGRAM_TO_BORDEREAU_DIMENSIONS


class SnowflakeProgramCSVIO:
    """
    Adapter Snowflake avec correspondance 1:1 aux colonnes CSV.
    Chaque colonne CSV correspond à une colonne table Snowflake.

    Tables:
      - PROGRAMS: 14 colonnes CSV + 2 colonnes d'audit
      - STRUCTURES: 21 colonnes CSV + 1 clé de liaison
      - CONDITIONS: 38 colonnes CSV + 1 clé de liaison
      - RP_GLOBAL_EXCLUSION: 11 colonnes CSV + 1 clé de liaison

    DSN attendu pour load/save :
      snowflake://DB.SCHEMA?program_title=...

    connection_params: dict pour snowflake.connector.connect(...)
    if_exists (save) :
      - "append"             : ajoute un nouveau programme
      - "replace_program"    : supprime le programme existant puis ré-insère
      - "truncate_all"       : TRUNCATE des 4 tables avant insert
    """

    PROGRAMS = "REINSURANCE_PROGRAM"
    STRUCTURES = "RP_STRUCTURES"
    CONDITIONS = "RP_CONDITIONS"
    EXCLUSIONS = "RP_GLOBAL_EXCLUSION"

    # ────────────────────────────────────────────────────────────────────
    # Utils
    # ────────────────────────────────────────────────────────────────────
    def _get_dimension_columns(self, df: pd.DataFrame) -> List[str]:
        dims = [d for d in PROGRAM_TO_BORDEREAU_DIMENSIONS.keys() if d in df.columns]
        # Explicit boolean flags are not dimensions and must not be compacted
        return [d for d in dims if d not in ("INCLUDES_HULL", "INCLUDES_LIABILITY")]

    def _split_multivalue_tokens(self, value: Any, sep: str = ";") -> List[str]:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return []
        if isinstance(value, list):
            tokens = [str(v).strip() for v in value if v is not None and str(v).strip()]
            return tokens
        s = str(value)
        if not s:
            return []
        parts = [t.strip() for t in s.split(sep)]
        return [t for t in parts if t]

    def _normalize_multivalue_cells(self, df: pd.DataFrame, dims: List[str], sep: str = ";") -> pd.DataFrame:
        if df.empty or not dims:
            return df
        out = df.copy()
        for col in dims:
            if col not in out.columns:
                continue
            def _norm_cell(v: Any) -> Any:
                tokens = self._split_multivalue_tokens(v, sep=sep)
                if not tokens:
                    return pd.NA
                # Deduplicate while preserving order
                seen = set()
                ordered = []
                for t in tokens:
                    if t not in seen:
                        seen.add(t)
                        ordered.append(t)
                return sep.join(ordered)
            out[col] = out[col].map(_norm_cell, na_action="ignore")
        return out

    def _compact_multivalue_conditions(self, df: pd.DataFrame, sep: str = ";") -> pd.DataFrame:
        if df.empty:
            return df
        dims = self._get_dimension_columns(df)
        if not dims:
            return df
        normalized = self._normalize_multivalue_cells(df, dims, sep=sep)
        # Identify grouping columns (non-dimensions). Exclude row-level identifier if present.
        group_cols = [c for c in normalized.columns if c not in dims and c != "BUSCL_ID_PRE"]
        if not group_cols:
            return normalized
        # Group and aggregate dimension columns into semicolon-separated unique tokens
        grouped_rows: List[Dict[str, Any]] = []
        # Use dropna=False to treat NaNs as keys and preserve groups
        for keys, grp in normalized.groupby(group_cols, dropna=False, sort=False):
            if not isinstance(keys, tuple):
                keys = (keys,)
            base: Dict[str, Any] = {col: val for col, val in zip(group_cols, keys)}
            # Choose a stable BUSCL_ID_PRE if exists (min over group)
            if "BUSCL_ID_PRE" in normalized.columns:
                try:
                    base["BUSCL_ID_PRE"] = grp["BUSCL_ID_PRE"].dropna().min()
                except Exception:
                    # Fallback: take first value
                    base["BUSCL_ID_PRE"] = grp["BUSCL_ID_PRE"].iloc[0] if not grp["BUSCL_ID_PRE"].empty else None
            # Aggregate dimensions
            for dim in dims:
                series = grp[dim] if dim in grp.columns else pd.Series([], dtype=object)
                tokens: List[str] = []
                seen: set[str] = set()
                for v in series.tolist():
                    for t in self._split_multivalue_tokens(v, sep=sep):
                        if t not in seen:
                            seen.add(t)
                            tokens.append(t)
                base[dim] = (sep.join(tokens)) if tokens else pd.NA
            grouped_rows.append(base)
        return pd.DataFrame(grouped_rows, columns=list(group_cols) + (["BUSCL_ID_PRE"] if "BUSCL_ID_PRE" in normalized.columns else []) + dims)

    def _compact_multivalue_exclusions(self, df: pd.DataFrame, sep: str = ";") -> pd.DataFrame:
        """Compaction spécifique pour les exclusions utilisant RP_GLOBAL_EXCLUSION_ID"""
        if df.empty:
            return df
        dims = self._get_dimension_columns(df)
        if not dims:
            return df
        normalized = self._normalize_multivalue_cells(df, dims, sep=sep)
        
        # Pour les exclusions, utiliser EXCLUSION_NAME comme identifiant de groupe principal
        # et les dates comme identifiants secondaires
        group_cols = ["EXCLUSION_NAME", "EXCL_EFFECTIVE_DATE", "EXCL_EXPIRY_DATE"]
        
        # S'assurer que les colonnes de groupe existent
        available_group_cols = [col for col in group_cols if col in normalized.columns]
        if not available_group_cols:
            return normalized
            
        grouped_rows: List[Dict[str, Any]] = []
        # Use dropna=False to treat NaNs as keys and preserve groups
        for keys, grp in normalized.groupby(available_group_cols, dropna=False, sort=False):
            if not isinstance(keys, tuple):
                keys = (keys,)
            base: Dict[str, Any] = {col: val for col, val in zip(available_group_cols, keys)}
            
            # Choisir un RP_GLOBAL_EXCLUSION_ID stable si existe (min du groupe)
            if "RP_GLOBAL_EXCLUSION_ID" in normalized.columns:
                try:
                    base["RP_GLOBAL_EXCLUSION_ID"] = grp["RP_GLOBAL_EXCLUSION_ID"].dropna().min()
                except Exception:
                    # Fallback: prendre la première valeur
                    base["RP_GLOBAL_EXCLUSION_ID"] = grp["RP_GLOBAL_EXCLUSION_ID"].iloc[0] if not grp["RP_GLOBAL_EXCLUSION_ID"].empty else None
            
            # Agrégation des dimensions
            for dim in dims:
                series = grp[dim] if dim in grp.columns else pd.Series([], dtype=object)
                tokens: List[str] = []
                seen: set[str] = set()
                for v in series.tolist():
                    for t in self._split_multivalue_tokens(v, sep=sep):
                        if t not in seen:
                            seen.add(t)
                            tokens.append(t)
                base[dim] = (sep.join(tokens)) if tokens else pd.NA
            grouped_rows.append(base)
        
        result_columns = available_group_cols + (["RP_GLOBAL_EXCLUSION_ID"] if "RP_GLOBAL_EXCLUSION_ID" in normalized.columns else []) + dims
        return pd.DataFrame(grouped_rows, columns=result_columns)

    def _clean_values_for_sql(self, values: List[Any]) -> List[Any]:
        """Nettoie les valeurs pour l'insertion SQL en remplaçant pd.NA et NaN par None"""
        cleaned = []
        for v in values:
            if pd.isna(v) or (hasattr(pd, 'NA') and v is pd.NA):
                cleaned.append(None)
            else:
                cleaned.append(v)
        return cleaned
    def _parse_dsn(self, source: str) -> Tuple[str, str, Dict[str, str]]:
        if not source.lower().startswith("snowflake://"):
            raise ValueError(f"Invalid Snowflake DSN: {source}")
        rest = source[len("snowflake://") :]
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

    def _get_program_id_from_title(
        self,
        program_title: str,
        connection_params: Dict[str, Any],
        db: str,
        schema: str,
    ) -> int:
        """Récupère l'ID du programme depuis la base de données basé sur le titre"""
        cnx = self._connect(connection_params)
        cur = cnx.cursor()

        try:
            cur.execute(
                f'SELECT REINSURANCE_PROGRAM_ID FROM "{db}"."{schema}"."{self.PROGRAMS}" WHERE TITLE=%s',
                (program_title,),
            )
            result = cur.fetchone()
            if result:
                return result[0]
            else:
                raise ValueError(
                    f"Programme '{program_title}' non trouvé dans la base de données"
                )
        finally:
            cur.close()
            cnx.close()

    # ────────────────────────────────────────────────────────────────────
    # READ
    # ────────────────────────────────────────────────────────────────────
    def read(
        self, source: str, connection_params: Dict[str, Any]
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        db, schema, params = self._parse_dsn(source)

        # Déterminer l'identifiant du programme
        program_title = params.get("program_title")
        if not program_title:
            raise ValueError("DSN must specify program_title parameter")

        # Récupérer l'ID du programme depuis la base de données
        program_id = self._get_program_id_from_title(
            program_title, connection_params, db, schema
        )

        cnx = self._connect(connection_params)
        cur = cnx.cursor()

        try:
            # PROGRAMS - utiliser TITLE pour trouver le programme
            cur.execute(
                f'SELECT * FROM "{db}"."{schema}"."{self.PROGRAMS}" WHERE TITLE=%s',
                (program_title,),
            )
            prog_rows = cur.fetchall()
            prog_cols = [d[0] for d in cur.description]

            if not prog_rows:
                raise ValueError("Program not found in PROGRAMS")

            program_df = pd.DataFrame([dict(zip(prog_cols, prog_rows[0]))])

            # STRUCTURES - toutes les colonnes CSV
            cur.execute(
                f'SELECT * FROM "{db}"."{schema}"."{self.STRUCTURES}" WHERE PROGRAM_ID=%s ORDER BY INSPER_ID_PRE',
                (program_id,),
            )
            s_rows = cur.fetchall()
            s_cols = [d[0] for d in cur.description]
            structures = []
            for r in s_rows:
                d = dict(zip(s_cols, r))
                structures.append(d)
            structures_df = pd.DataFrame(structures) if structures else pd.DataFrame()

            # CONDITIONS - toutes les colonnes CSV
            cur.execute(
                f'SELECT * FROM "{db}"."{schema}"."{self.CONDITIONS}" WHERE PROGRAM_ID=%s ORDER BY BUSCL_ID_PRE',
                (program_id,),
            )
            c_rows = cur.fetchall()
            c_cols = [d[0] for d in cur.description]
            conditions = []
            for r in c_rows:
                d = dict(zip(c_cols, r))
                conditions.append(d)
            conditions_df = pd.DataFrame(conditions) if conditions else pd.DataFrame()

            # EXCLUSIONS - toutes les colonnes CSV
            cur.execute(
                f'SELECT * FROM "{db}"."{schema}"."{self.EXCLUSIONS}" WHERE RP_ID=%s',
                (program_id,),
            )
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
                cur.execute(
                    f'SELECT REINSURANCE_PROGRAM_ID FROM "{db}"."{schema}"."{self.PROGRAMS}" WHERE TITLE=%s',
                    (program_title,),
                )
                existing_program = cur.fetchone()
                if existing_program:
                    existing_program_id = existing_program[0]
                    cur.execute(
                        f'DELETE FROM "{db}"."{schema}"."{self.EXCLUSIONS}" WHERE RP_ID=%s',
                        (existing_program_id,),
                    )
                    cur.execute(
                        f'DELETE FROM "{db}"."{schema}"."{self.CONDITIONS}" WHERE PROGRAM_ID=%s',
                        (existing_program_id,),
                    )
                    cur.execute(
                        f'DELETE FROM "{db}"."{schema}"."{self.STRUCTURES}" WHERE PROGRAM_ID=%s',
                        (existing_program_id,),
                    )
                    cur.execute(
                        f'DELETE FROM "{db}"."{schema}"."{self.PROGRAMS}" WHERE REINSURANCE_PROGRAM_ID=%s',
                        (existing_program_id,),
                    )

            # PROGRAMS - insérer et récupérer l'ID auto-généré
            program_id = None
            if not program_df.empty:
                p_rows: List[Dict[str, Any]] = []
                for _, r in program_df.iterrows():
                    row_dict = r.to_dict()

                    # Mapping des colonnes CSV vers Snowflake
                    mapped_row = {}
                    for csv_col, value in row_dict.items():
                        if csv_col == "REPROG_TITLE":
                            mapped_row["TITLE"] = value
                        elif csv_col == "REINSURANCE_PROGRAM_ID":
                            # Ne pas inclure REINSURANCE_PROGRAM_ID car c'est auto-increment
                            continue
                        elif csv_col == "ACTIVE_IND":
                            mapped_row["ACTIVE_IND"] = value
                        elif csv_col == "UW_LOB":
                            mapped_row["UW_LOB"] = value
                        elif csv_col == "MAIN_CURRENCY_CD":
                            mapped_row["MAIN_CURRENCY_CD"] = value
                        elif csv_col == "ADDITIONAL_INFO":
                            mapped_row["ADDITIONAL_INFO"] = value
                        elif csv_col == "UW_DEPARTMENT_CODE":
                            mapped_row["UW_DEPARTMENT_CODE"] = value
                        elif csv_col == "BUSPAR_CED_REG_CLASS_CD":
                            mapped_row["BUSPAR_CED_REG_CLASS_CD"] = value
                        elif csv_col == "CED_ID_PRE":
                            mapped_row["CED_ID_PRE"] = value
                        elif csv_col == "CED_NAME_PRE":
                            mapped_row["ID_PRE"] = value
                        # Ignorer les colonnes qui n'existent pas dans la table Snowflake
                        elif csv_col in [
                            "REPROG_UW_DEPARTMENT_NAME",
                            "REPROG_UW_DEPARTMENT_LOB_NAME",
                            "BUSPAR_CED_REG_CLASS_NAME",
                            "REPROG_MANAGEMENT_REPORTING_LOB_CD",
                        ]:
                            continue
                        else:
                            # Garder les autres colonnes telles quelles
                            mapped_row[csv_col] = value

                    # Ajouter les colonnes d'audit
                    mapped_row["CREATED_AT"] = pd.Timestamp.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    mapped_row["UPDATED_AT"] = pd.Timestamp.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    p_rows.append(mapped_row)

                # Insérer le programme et récupérer l'ID auto-généré
                # Utiliser INSERT direct au lieu de write_pandas pour éviter les problèmes de paramètres
                for row in p_rows:
                    columns = list(row.keys())
                    values = list(row.values())
                    # Nettoyer les valeurs pour éviter les erreurs SQL avec pd.NA/NaN
                    cleaned_values = self._clean_values_for_sql(values)
                    placeholders = ", ".join(["%s"] * len(cleaned_values))
                    columns_str = ", ".join([f'"{col}"' for col in columns])
                    insert_sql = f'INSERT INTO "{db}"."{schema}"."{self.PROGRAMS}" ({columns_str}) VALUES ({placeholders})'
                    cur.execute(insert_sql, cleaned_values)

                # Récupérer l'ID du programme qui vient d'être inséré
                cur.execute(
                    f'SELECT REINSURANCE_PROGRAM_ID FROM "{db}"."{schema}"."{self.PROGRAMS}" WHERE TITLE=%s',
                    (program_title,),
                )
                result = cur.fetchone()
                if result:
                    program_id = result[0]
                else:
                    raise ValueError(
                        f"Impossible de récupérer l'ID du programme '{program_title}' après insertion"
                    )

            # STRUCTURES - toutes les colonnes CSV + PROGRAM_ID
            if not structures_df.empty:
                s_rows: List[Dict[str, Any]] = []
                for _, r in structures_df.iterrows():
                    row_dict = r.to_dict()

                    # Mapping des colonnes CSV vers Snowflake
                    mapped_row = {}
                    for csv_col, value in row_dict.items():
                        if csv_col == "INSPER_ID_PRE":
                            # Ne pas inclure INSPER_ID_PRE car c'est auto-increment
                            continue
                        elif csv_col == "REINSURANCE_PROGRAM_ID":
                            # Remplacer par PROGRAM_ID
                            mapped_row["PROGRAM_ID"] = program_id
                        elif csv_col == "BUSINESS_TITLE":
                            mapped_row["BUSINESS_TITLE"] = value
                        else:
                            # Garder les autres colonnes telles quelles
                            mapped_row[csv_col] = value

                    # Convertir les timestamps au format standard pour Snowflake
                    for col in ["INSPER_EFFECTIVE_DATE", "INSPER_EXPIRY_DATE"]:
                        if col in mapped_row and pd.notna(mapped_row[col]):
                            if isinstance(mapped_row[col], pd.Timestamp):
                                mapped_row[col] = mapped_row[col].strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                )

                    s_rows.append(mapped_row)
                write_pandas(
                    cnx,
                    pd.DataFrame(s_rows),
                    table_name=self.STRUCTURES,
                    database=db,
                    schema=schema,
                    auto_create_table=False,
                    quote_identifiers=True,
                )

            # CONDITIONS - toutes les colonnes CSV + PROGRAM_ID
            if not conditions_df.empty:
                # Respect multi-value semantics: compact multiple rows differing only by dimension columns
                compacted_conditions = self._compact_multivalue_conditions(conditions_df)
                c_rows: List[Dict[str, Any]] = []
                for _, r in compacted_conditions.iterrows():
                    row_dict = r.to_dict()

                    # Mapping des colonnes CSV vers Snowflake
                    mapped_row = {}
                    for csv_col, value in row_dict.items():
                        if csv_col == "REINSURANCE_PROGRAM_ID":
                            # Remplacer par PROGRAM_ID
                            mapped_row["PROGRAM_ID"] = program_id
                        else:
                            # Garder les autres colonnes telles quelles
                            mapped_row[csv_col] = value

                    # Convertir les timestamps au format standard pour Snowflake
                    for col in ["INSPER_EFFECTIVE_DATE", "INSPER_EXPIRY_DATE"]:
                        if col in mapped_row and pd.notna(mapped_row[col]):
                            if isinstance(mapped_row[col], pd.Timestamp):
                                mapped_row[col] = mapped_row[col].strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                )

                    c_rows.append(mapped_row)
                write_pandas(
                    cnx,
                    pd.DataFrame(c_rows),
                    table_name=self.CONDITIONS,
                    database=db,
                    schema=schema,
                    auto_create_table=False,
                    quote_identifiers=True,
                )

            # EXCLUSIONS - toutes les colonnes CSV + PROGRAM_ID
            if not exclusions_df.empty:
                if program_id is None:
                    raise ValueError(
                        "program_id is None when trying to insert exclusions"
                    )
                # Respect multi-value semantics: compact multiple rows differing only by dimension columns
                compacted_exclusions = self._compact_multivalue_exclusions(exclusions_df)
                e_rows: List[Dict[str, Any]] = []
                for _, r in compacted_exclusions.iterrows():
                    row_dict = r.to_dict()

                    # Mapping des colonnes CSV vers Snowflake
                    mapped_row = {}
                    # Ajouter RP_ID manuellement car il n'est pas dans le CSV
                    mapped_row["RP_ID"] = program_id

                    for csv_col, value in row_dict.items():
                        if csv_col == "BUSCL_CLASS_OF_BUSINESS_1":
                            mapped_row["PRODUCT_TYPE_LEVEL_1"] = value
                        elif csv_col == "BUSCL_CLASS_OF_BUSINESS_2":
                            mapped_row["PRODUCT_TYPE_LEVEL_2"] = value
                        elif csv_col == "BUSCL_CLASS_OF_BUSINESS_3":
                            mapped_row["PRODUCT_TYPE_LEVEL_3"] = value
                        elif csv_col == "BUSCL_ENTITY_NAME_CED":
                            mapped_row["ENTITY_NAME_CED"] = value
                        elif csv_col == "POL_RISK_NAME_CED":
                            mapped_row["RISK_NAME"] = value
                        else:
                            # Garder les autres colonnes telles quelles
                            mapped_row[csv_col] = value

                    # Convertir les timestamps au format standard pour Snowflake
                    for col in ["EXCL_EFFECTIVE_DATE", "EXCL_EXPIRY_DATE"]:
                        if col in mapped_row and pd.notna(mapped_row[col]):
                            if isinstance(mapped_row[col], pd.Timestamp):
                                mapped_row[col] = mapped_row[col].strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                )

                    e_rows.append(mapped_row)
                # Insertion SQL directe pour les exclusions
                if e_rows:
                    for row in e_rows:
                        columns = list(row.keys())
                        values = list(row.values())
                        # Nettoyer les valeurs pour éviter les erreurs SQL avec pd.NA/NaN
                        cleaned_values = self._clean_values_for_sql(values)
                        placeholders = ", ".join(["%s"] * len(cleaned_values))
                        columns_str = ", ".join([f'"{col}"' for col in columns])

                        insert_sql = f'INSERT INTO "{db}"."{schema}"."{self.EXCLUSIONS}" ({columns_str}) VALUES ({placeholders})'
                        cur.execute(insert_sql, cleaned_values)

        finally:
            cur.close()
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
