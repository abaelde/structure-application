#!/usr/bin/env python3
"""
Script pour créer le DDL correct avec auto-increment basé sur le DDL généré.
"""

import json
from pathlib import Path


def create_correct_ddl():
    """Crée le DDL correct avec auto-increment"""

    # Lire l'analyse des CSV
    analysis_file = Path(__file__).parent / "csv_structure_analysis.json"
    with open(analysis_file, "r") as f:
        analysis = json.load(f)

    ddl_content = """-- DDL corrigé avec auto-increment
-- Date: 2025-10-21

-- Table REINSURANCE_PROGRAM avec auto-increment
CREATE TABLE REINSURANCE_PROGRAM (
  REINSURANCE_PROGRAM_ID                     NUMBER(38,0)    AUTOINCREMENT PRIMARY KEY,
  ID_PRE                  VARCHAR,
  TITLE                   VARCHAR          NOT NULL,
  CED_ID_PRE                     NUMBER(38,0),
  ACTIVE_IND              BOOLEAN         NOT NULL,
  ADDITIONAL_INFO                 VARCHAR,
  UW_DEPARTMENT_CODE        VARCHAR,
  UW_LOB   VARCHAR          NOT NULL,
  BUSPAR_CED_REG_CLASS_CD        VARCHAR,
  MAIN_CURRENCY_CD        VARCHAR,
  CREATED_AT               TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP(),
  UPDATED_AT               TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP()
);

-- Table RP_STRUCTURES avec auto-increment pour INSPER_ID_P\-RE
CREATE TABLE RP_STRUCTURES (
  RP_STRUCTURE_ID                  NUMBER(38,0)    AUTOINCREMENT PRIMARY KEY,
  RP_STRUCTURE_NAME                VARCHAR,
  RP_ID                     NUMBER(38,0)    NOT NULL,
  T_NUMBER                VARCHAR,
  LAYER_NUMBER         NUMBER(38,0),
  TYPE_OF_PARTICIPATION_CD       VARCHAR          NOT NULL,
  INSURED_PERIOD_TYPE      VARCHAR,
  CLASS_OF_BUSINESS VARCHAR,
  CLAIMS_BASIS VARCHAR,
  MAIN_CURRENCY NUMBER(38,0),
  EFFECTIVE_DATE          TIMESTAMP_NTZ,
  EXPIRY_DATE             TIMESTAMP_NTZ,
  UW_YEAR                 NUMBER(38,0),
  COMMENT                 VARCHAR,
  PREDECESSOR_TITLE       STRING,
  FOREIGN KEY (RP_ID) REFERENCES REINSURANCE_PROGRAM(REINSURANCE_PROGRAM_ID)
);

-- Table RP_CONDITIONS avec clé étrangère vers RP_STRUCTURES
CREATE TABLE RP_CONDITIONS (
  RP_CONDITION_ID                NUMBER(38,0)    AUTOINCREMENT PRIMARY KEY,
  CED_ID_PRE                     NUMBER(38,0),
  BUSINESS_ID_PRE                NUMBER(38,0),
  INSPER_ID_PRE                  NUMBER(38,0),
  BUSCL_ENTITY_NAME_CED          VARCHAR,
  POL_RISK_NAME_CED              VARCHAR,
  BUSCL_COUNTRY_CD               VARCHAR,
  BUSCL_COUNTRY                  VARCHAR,
  BUSCL_REGION                   VARCHAR,
  PRODUCT_TYPE_LEVEL_1           VARCHAR,
  PRODUCT_TYPE_LEVEL_2           VARCHAR,
  PRODUCT_TYPE_LEVEL_3           VARCHAR,
  BUSCL_LIMIT_CURRENCY_CD        VARCHAR,
  AAD_100                        FLOAT,
  LIMIT_100                      NUMBER(38,0),
  LIMIT_FLOATER_100              FLOAT,
  ATTACHMENT_POINT_100           FLOAT,
  OLW_100                        FLOAT,
  LIMIT_AGG_100                  FLOAT,
  CESSION_PCT                    FLOAT,
  RETENTION_PCT                  FLOAT,
  SUPI_100                       FLOAT,
  BUSCL_PREMIUM_CURRENCY_CD      FLOAT,
  BUSCL_PREMIUM_GROSS_NET_CD     FLOAT,
  PREMIUM_RATE_PCT               FLOAT,
  PREMIUM_DEPOSIT_100            FLOAT,
  PREMIUM_MIN_100                FLOAT,
  BUSCL_LIABILITY_1_LINE_100     FLOAT,
  MAX_COVER_PCT                  FLOAT,
  MIN_EXCESS_PCT                 FLOAT,
  SIGNED_SHARE_PCT               FLOAT,
  AVERAGE_LINE_SLAV_CED          FLOAT,
  PML_DEFAULT_PCT                FLOAT,
  LIMIT_EVENT                    FLOAT,
  NO_OF_REINSTATEMENTS           FLOAT,
  INCLUDES_HULL                  BOOLEAN,
  INCLUDES_LIABILITY             BOOLEAN,
  FOREIGN KEY (INSPER_ID_PRE) REFERENCES RP_STRUCTURES(RP_STRUCTURE_ID)
);

-- Table RP_GLOBAL_EXCLUSION avec clé étrangère vers PROGRAMS
CREATE TABLE RP_GLOBAL_EXCLUSION (
  RP_GLOBAL_EXCLUSION_ID         NUMBER(38,0)    AUTOINCREMENT PRIMARY KEY,
  EXCLUSION_NAME                 VARCHAR,
  RP_ID                          NUMBER(38,0)    NOT NULL,
  EXCL_EFFECTIVE_DATE            STRING,
  EXCL_EXPIRY_DATE               STRING,
  BUSCL_COUNTRY_CD               VARCHAR,
  BUSCL_REGION                   VARCHAR,
  PRODUCT_TYPE_LEVEL_1           VARCHAR,
  PRODUCT_TYPE_LEVEL_2           VARCHAR,
  PRODUCT_TYPE_LEVEL_3           VARCHAR,
  ENTITY_NAME_CED                VARCHAR,
  RISK_NAME                      VARCHAR,
  BUSCL_LIMIT_CURRENCY_CD        VARCHAR,
  FOREIGN KEY (RP_ID) REFERENCES REINSURANCE_PROGRAM(REINSURANCE_PROGRAM_ID)
);

-- Table RP_STRUCTURE_FIELD_LINK
CREATE TABLE RP_STRUCTURE_FIELD_LINK (
  RP_STRUCTURE_FIELD_LINK_ID         NUMBER(38,0)    AUTOINCREMENT PRIMARY KEY,
  RP_CONDITION_ID                 NUMBER(38,0) NOT NULL,
  RP_STRUCTURE_ID                 NUMBER(38,0)    NOT NULL,
  FIELD_NAME            VARCHAR,
  NEW_VALUE               VARCHAR,
  CREATED_AT TIMESTAMP_NTZ(9),
  FOREIGN KEY (RP_CONDITION_ID) REFERENCES RP_CONDITIONS(RP_CONDITION_ID),
  FOREIGN KEY (RP_STRUCTURE_ID) REFERENCES RP_STRUCTURES(RP_STRUCTURE_ID)
);
"""

    # Sauvegarder le DDL corrigé
    output_file = Path(__file__).parent / "correct_snowflake_ddl.sql"
    with open(output_file, "w") as f:
        f.write(ddl_content)

    print(f"✅ DDL corrigé créé: {output_file}")
    return output_file


if __name__ == "__main__":
    create_correct_ddl()
