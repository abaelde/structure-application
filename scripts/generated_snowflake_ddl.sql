-- DDL généré automatiquement à partir de la structure des CSV
-- Date: 2025-10-21 13:55:35

-- Table PROGRAMS
CREATE TABLE PROGRAMS (
  REINSURANCE_PROGRAM_ID                  NUMBER(38,0)    NOT NULL,
  TITLE                   STRING          NOT NULL,
  CED_ID_PRE                     FLOAT           NOT NULL,
  CED_NAME_PRE                   FLOAT           NOT NULL,
  ACTIVE_IND              BOOLEAN         NOT NULL,
  ADDITIONAL_INFO                 FLOAT           NOT NULL,
  UW_DEPARTMENT_CODE        FLOAT           NOT NULL,
  REPROG_UW_DEPARTMENT_NAME      FLOAT           NOT NULL,
  UW_LOB    STRING          NOT NULL,
  REPROG_UW_DEPARTMENT_LOB_NAME  STRING          NOT NULL,
  BUSPAR_CED_REG_CLASS_CD        FLOAT           NOT NULL,
  BUSPAR_CED_REG_CLASS_NAME      FLOAT           NOT NULL,
  MAIN_CURRENCY_CD        FLOAT           NOT NULL,
  REPROG_MANAGEMENT_REPORTING_LOB_CD FLOAT           NOT NULL
  CREATED_AT             STRING,
  UPDATED_AT             STRING
  PRIMARY KEY (REINSURANCE_PROGRAM_ID)
);

-- Table STRUCTURES
CREATE TABLE STRUCTURES (
  PROGRAM_ID             STRING       NOT NULL,
  INSPER_ID_PRE                  NUMBER(38,0)    NOT NULL,
  BUSINESS_ID_PRE                FLOAT           NOT NULL,
  TYPE_OF_PARTICIPATION_CD       STRING          NOT NULL,
  TYPE_OF_INSURED_PERIOD_CD      FLOAT           NOT NULL,
  ACTIVE_FLAG_CD                 BOOLEAN         NOT NULL,
  INSPER_EFFECTIVE_DATE          TIMESTAMP_NTZ   NOT NULL,
  INSPER_EXPIRY_DATE             TIMESTAMP_NTZ   NOT NULL,
  REINSURANCE_PROGRAM_ID                  NUMBER(38,0)    NOT NULL,
  BUSINESS_TITLE                 STRING          NOT NULL,
  INSPER_LAYER_NO                FLOAT           NOT NULL,
  INSPER_MAIN_CURRENCY_CD        FLOAT           NOT NULL,
  INSPER_UW_YEAR                 FLOAT           NOT NULL,
  INSPER_CONTRACT_ORDER          FLOAT           NOT NULL,
  INSPER_PREDECESSOR_TITLE       STRING          NOT NULL,
  INSPER_CONTRACT_FORM_CD_SLAV   FLOAT           NOT NULL,
  INSPER_CONTRACT_LODRA_CD_SLAV  FLOAT           NOT NULL,
  INSPER_CONTRACT_COVERAGE_CD_SLAV FLOAT           NOT NULL,
  INSPER_CLAIM_BASIS_CD          STRING          NOT NULL,
  INSPER_LODRA_CD_SLAV           FLOAT           NOT NULL,
  INSPER_LOD_TO_RA_DATE_SLAV     FLOAT           NOT NULL,
  INSPER_COMMENT                 FLOAT           NOT NULL,

  PRIMARY KEY (PROGRAM_ID, INSPER_ID_PRE)
);

-- Table CONDITIONS
CREATE TABLE CONDITIONS (
  PROGRAM_ID             STRING       NOT NULL,
  BUSCL_ID_PRE                   NUMBER(38,0)    NOT NULL,
  REINSURANCE_PROGRAM_ID                  NUMBER(38,0)    NOT NULL,
  CED_ID_PRE                     FLOAT           NOT NULL,
  BUSINESS_ID_PRE                FLOAT           NOT NULL,
  INSPER_ID_PRE                  NUMBER(38,0)    NOT NULL,
  BUSCL_ENTITY_NAME_CED          FLOAT           NOT NULL,
  POL_RISK_NAME_CED              FLOAT           NOT NULL,
  BUSCL_COUNTRY_CD               FLOAT           NOT NULL,
  BUSCL_COUNTRY                  FLOAT           NOT NULL,
  BUSCL_REGION                   FLOAT           NOT NULL,
  BUSCL_CLASS_OF_BUSINESS_1      FLOAT           NOT NULL,
  BUSCL_CLASS_OF_BUSINESS_2      FLOAT           NOT NULL,
  BUSCL_CLASS_OF_BUSINESS_3      FLOAT           NOT NULL,
  BUSCL_LIMIT_CURRENCY_CD        STRING          NOT NULL,
  AAD_100                        FLOAT           NOT NULL,
  LIMIT_100                      NUMBER(38,0)    NOT NULL,
  LIMIT_FLOATER_100              FLOAT           NOT NULL,
  ATTACHMENT_POINT_100           FLOAT           NOT NULL,
  OLW_100                        FLOAT           NOT NULL,
  LIMIT_AGG_100                  FLOAT           NOT NULL,
  CESSION_PCT                    FLOAT           NOT NULL,
  RETENTION_PCT                  FLOAT           NOT NULL,
  SUPI_100                       FLOAT           NOT NULL,
  BUSCL_PREMIUM_CURRENCY_CD      FLOAT           NOT NULL,
  BUSCL_PREMIUM_GROSS_NET_CD     FLOAT           NOT NULL,
  PREMIUM_RATE_PCT               FLOAT           NOT NULL,
  PREMIUM_DEPOSIT_100            FLOAT           NOT NULL,
  PREMIUM_MIN_100                FLOAT           NOT NULL,
  BUSCL_LIABILITY_1_LINE_100     FLOAT           NOT NULL,
  MAX_COVER_PCT                  FLOAT           NOT NULL,
  MIN_EXCESS_PCT                 FLOAT           NOT NULL,
  SIGNED_SHARE_PCT               FLOAT           NOT NULL,
  AVERAGE_LINE_SLAV_CED          FLOAT           NOT NULL,
  PML_DEFAULT_PCT                FLOAT           NOT NULL,
  LIMIT_EVENT                    FLOAT           NOT NULL,
  NO_OF_REINSTATEMENTS           FLOAT           NOT NULL,
  INCLUDES_HULL                  BOOLEAN         NOT NULL,
  INCLUDES_LIABILITY             BOOLEAN         NOT NULL,

  PRIMARY KEY (PROGRAM_ID, BUSCL_ID_PRE)
);

-- Table EXCLUSIONS
CREATE TABLE EXCLUSIONS (
  PROGRAM_ID             STRING       NOT NULL,
  EXCL_REASON                    STRING          ,
  EXCL_EFFECTIVE_DATE            STRING          ,
  EXCL_EXPIRY_DATE               STRING          ,
  BUSCL_COUNTRY_CD               STRING          ,
  BUSCL_REGION                   STRING          ,
  BUSCL_CLASS_OF_BUSINESS_1      STRING          ,
  BUSCL_CLASS_OF_BUSINESS_2      STRING          ,
  BUSCL_CLASS_OF_BUSINESS_3      STRING          ,
  BUSCL_ENTITY_NAME_CED          STRING          ,
  POL_RISK_NAME_CED              STRING          ,
  BUSCL_LIMIT_CURRENCY_CD        STRING          ,

  -- Pas de clé primaire définie (table de référence)
);

