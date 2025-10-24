#!/usr/bin/env python3
"""
Script pour créer le DDL correct avec auto-increment basé sur le DDL généré.
"""

import json
from pathlib import Path


def create_correct_ddl():
    """Crée le DDL correct avec auto-increment"""


    ddl_content = """-- DDL corrigé avec auto-increment
-- Date: 2025-10-21

-- Table REINSURANCE_PROGRAM avec auto-increment
CREATE TABLE REINSURANCE_PROGRAM (
  REINSURANCE_PROGRAM_ID                     NUMBER(38,0)    AUTOINCREMENT PRIMARY KEY,
  ID_PRE                  VARCHAR,
  TITLE                   VARCHAR          NOT NULL,
  REF_CEDENT_ID                     NUMBER(38,0),
  ACTIVE_IND              BOOLEAN         NOT NULL,
  ADDITIONAL_INFO                 VARCHAR,
  UW_DEPARTMENT_ID        VARCHAR,
  REF_REF_ID   VARCHAR          NOT NULL,
  BUSPAR_CED_REG_CLASS_CD        VARCHAR,
  MAIN_CURRENCY_ID        VARCHAR,
  CREATED_AT               TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP(),
  CREATED_BY               VARCHAR,
  MODIFIED_AT               TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP(),
  MODIFIED_BY               VARCHAR
);

-- Table RP_STRUCTURES avec auto-increment pour INSPER_ID_P\-RE
CREATE TABLE RP_STRUCTURES (
  RP_STRUCTURE_ID                  NUMBER(38,0)    AUTOINCREMENT PRIMARY KEY,
  RP_STRUCTURE_NAME                VARCHAR,
  RP_STRUCTURE_ID_PREDECESSOR       VARCHAR,
  REINSURANCE_PROGRAM_ID                     NUMBER(38,0)    NOT NULL,
  T_NUMBER                  VARCHAR,
  LAYER_NUMBER              NUMBER(38,0),
  TYPE_OF_PARTICIPATION    VARCHAR          NOT NULL,
  INSURED_PERIOD_TYPE      VARCHAR,
  CLASS_OF_BUSINESS        VARCHAR,
  CLAIMS_BASIS            VARCHAR,
  MAIN_CURRENCY           NUMBER(38,0),
  EFFECTIVE_DATE          TIMESTAMP_NTZ,
  EXPIRY_DATE             TIMESTAMP_NTZ,
  UW_YEAR                 NUMBER(38,0),
  COMMENT                 VARCHAR,

  -- Défauts financiers (valeurs utilisées si pas d'override côté condition)
  LIMIT_100                      NUMBER(38,0),
  ATTACHMENT_POINT_100           NUMBER(38,0),
  CESSION_PCT                    NUMBER(38,4),
  RETENTION_PCT                  NUMBER(38,4),
  SUPI_100                       NUMBER(38,0),
  BUSCL_PREMIUM_CURRENCY_CD      NUMBER(38,0),
  BUSCL_PREMIUM_GROSS_NET_CD     NUMBER(38,0),
  PREMIUM_RATE_PCT               NUMBER(38,4),
  PREMIUM_DEPOSIT_100            NUMBER(38,0),
  PREMIUM_MIN_100                NUMBER(38,0),
  BUSCL_LIABILITY_1_LINE_100     NUMBER(38,0),
  MAX_COVER_PCT                  NUMBER(38,0),
  MIN_EXCESS_PCT                 NUMBER(38,0),
  SIGNED_SHARE_PCT               NUMBER(38,4),
  AVERAGE_LINE_SLAV_CED          NUMBER(38,0),
  PML_DEFAULT_PCT                NUMBER(38,0),
  LIMIT_EVENT                    NUMBER(38,0),
  NO_OF_REINSTATEMENTS           NUMBER(38,0),
  
  FOREIGN KEY (REINSURANCE_PROGRAM_ID) REFERENCES REINSURANCE_PROGRAM(REINSURANCE_PROGRAM_ID)
);

-- Table RP_CONDITIONS avec clé étrangère vers RP_STRUCTURES
CREATE TABLE RP_CONDITIONS (
  RP_CONDITION_ID                NUMBER(38,0)    AUTOINCREMENT PRIMARY KEY,
  CONDITION_NAME                 VARCHAR,
  CONDITION_DESCRIPTION          VARCHAR,

   -- Scopage programme
  REINSURANCE_PROGRAM_ID                           NUMBER(38,0) NOT NULL,

  -- Dimensions logiques (complète/ajuste selon ton mapping réel)
  COUNTRIES                     VARCHAR,
  REGIONS                      VARCHAR,
  PRODUCT_TYPE_LEVEL_1           VARCHAR,
  PRODUCT_TYPE_LEVEL_2           VARCHAR,
  PRODUCT_TYPE_LEVEL_3           VARCHAR,
  CURRENCIES                    VARCHAR,

  -- Flags d'exposition (logiques)
  INCLUDES_HULL                  BOOLEAN,
  INCLUDES_LIABILITY             BOOLEAN,

  -- Audit
  CREATED_AT                     TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP(),
  CREATED_BY                     VARCHAR,
  MODIFIED_AT                    TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP(),
  MODIFIED_BY                    VARCHAR,
  FOREIGN KEY (REINSURANCE_PROGRAM_ID) REFERENCES REINSURANCE_PROGRAM(REINSURANCE_PROGRAM_ID)
);

-- Table RP_GLOBAL_EXCLUSION avec clé étrangère vers PROGRAMS
CREATE TABLE RP_GLOBAL_EXCLUSION (
  RP_GLOBAL_EXCLUSION_ID         NUMBER(38,0)    AUTOINCREMENT PRIMARY KEY,
  REINSURANCE_PROGRAM_ID                          NUMBER(38,0)    NOT NULL,
  COUNTRIES               VARCHAR,
  REGIONS                   VARCHAR,
  PRODUCT_TYPE_LEVEL_1           VARCHAR,
  PRODUCT_TYPE_LEVEL_2           VARCHAR,
  PRODUCT_TYPE_LEVEL_3           VARCHAR,
  CURRENCIES        VARCHAR,
    MODIFIED_AT                    TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP(),
  MODIFIED_BY                    VARCHAR,
  CREATED_AT                     TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP(),
  CREATED_BY                     VARCHAR,
  FOREIGN KEY (REINSURANCE_PROGRAM_ID) REFERENCES REINSURANCE_PROGRAM(REINSURANCE_PROGRAM_ID)
);

-- Table RP_STRUCTURE_FIELD_LINK
CREATE TABLE RP_STRUCTURE_FIELD_LINK (
  RP_STRUCTURE_FIELD_LINK_ID         NUMBER(38,0)    AUTOINCREMENT PRIMARY KEY,
  RP_CONDITION_ID                 NUMBER(38,0) NOT NULL,
  RP_STRUCTURE_ID                 NUMBER(38,0)    NOT NULL,
  FIELD_NAME            VARCHAR NOT NULL,
  NEW_VALUE               NUMBER(38,4),
  CREATED_AT TIMESTAMP_NTZ(9),
  CREATED_BY VARCHAR,
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
