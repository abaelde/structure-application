-- Script corrigé pour créer les tables Snowflake sans colonnes timestamp problématiques
-- Utilise SNOWFLAKE_LEARNING_DB.MYSCHEMA

-- ========================================
-- TABLES POUR LES PROGRAMMES
-- ========================================

-- Table principale des programmes
CREATE TABLE IF NOT EXISTS SNOWFLAKE_LEARNING_DB.MYSCHEMA.PROGRAMS (
  PROGRAM_ID             STRING          PRIMARY KEY,
  REPROG_TITLE           STRING          NOT NULL,
  REPROG_UW_DEPARTMENT_LOB_CD STRING     NOT NULL,
  CREATED_AT             STRING,         -- Changé en STRING pour éviter les problèmes
  UPDATED_AT             STRING,         -- Changé en STRING pour éviter les problèmes
  PAYLOAD                STRING          -- JSON (texte) pour champs optionnels
);

-- Table des structures de réassurance (avec timestamps compatibles)
CREATE TABLE IF NOT EXISTS SNOWFLAKE_LEARNING_DB.MYSCHEMA.STRUCTURES (
  PROGRAM_ID                 STRING       NOT NULL,
  INSPER_ID_PRE              NUMBER       NOT NULL,     -- ident interne "par programme"
  INSPER_CONTRACT_ORDER      NUMBER,
  TYPE_OF_PARTICIPATION_CD   STRING,
  INSPER_PREDECESSOR_TITLE   STRING,
  INSPER_CLAIM_BASIS_CD      STRING,
  INSPER_EFFECTIVE_DATE      TIMESTAMP_NTZ,  -- Format standard Snowflake/Python
  INSPER_EXPIRY_DATE         TIMESTAMP_NTZ,  -- Format standard Snowflake/Python
  PAYLOAD                    STRING,                   -- JSON (texte) complet de la ligne
  PRIMARY KEY (PROGRAM_ID, INSPER_ID_PRE)
);

-- Table des conditions de réassurance
CREATE TABLE IF NOT EXISTS SNOWFLAKE_LEARNING_DB.MYSCHEMA.CONDITIONS (
  PROGRAM_ID               STRING     NOT NULL,
  INSPER_ID_PRE            NUMBER     NOT NULL,     -- FK vers STRUCTURES
  BUSCL_ID_PRE             NUMBER     NOT NULL,
  SIGNED_SHARE_PCT         FLOAT,
  INCLUDES_HULL            BOOLEAN,
  INCLUDES_LIABILITY       BOOLEAN,
  PAYLOAD                  STRING,                 -- JSON (texte) complet de la ligne
  PRIMARY KEY (PROGRAM_ID, BUSCL_ID_PRE)
);

-- Table des exclusions (sans colonnes timestamp)
CREATE TABLE IF NOT EXISTS SNOWFLAKE_LEARNING_DB.MYSCHEMA.EXCLUSIONS (
  PROGRAM_ID             STRING     NOT NULL,
  EXCL_REASON            STRING,
  PAYLOAD                STRING     -- JSON contient les dates
);

-- ========================================
-- TABLES POUR LES RUNS
-- ========================================

-- Table des exécutions de calculs
CREATE TABLE IF NOT EXISTS SNOWFLAKE_LEARNING_DB.MYSCHEMA.RUNS (
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

-- Table des politiques traitées dans un run
CREATE TABLE IF NOT EXISTS SNOWFLAKE_LEARNING_DB.MYSCHEMA.RUN_POLICIES (
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

-- Table des structures appliquées par politique
CREATE TABLE IF NOT EXISTS SNOWFLAKE_LEARNING_DB.MYSCHEMA.RUN_POLICY_STRUCTURES (
  STRUCTURE_ROW_ID        STRING PRIMARY KEY,
  POLICY_RUN_ID           STRING,
  STRUCTURE_NAME          STRING,
  TYPE_OF_PARTICIPATION   STRING,
  PREDECESSOR_TITLE       STRING,
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
