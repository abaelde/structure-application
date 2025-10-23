# Migration vers Snowpark - Plan de Migration

## 🎯 Objectif

Migrer l'application de réassurance du connecteur Snowflake Python classique (`snowflake-connector-python`) vers **Snowpark Python** pour bénéficier de :

- **Exécution côté serveur** : Logique métier exécutée dans Snowflake
- **Procédures stockées Python** : Interface Python native pour les opérations
- **Performance améliorée** : Utilisation optimale des ressources Snowflake
- **Scalabilité** : Traitement distribué des données
- **Sécurité renforcée** : Gestion centralisée des permissions

## 📊 État Actuel

### Architecture existante
```
snowflake_utils/
├── config.py              # Configuration centralisée
├── utils.py               # Utilitaires de sauvegarde
└── cli.py                 # Interface en ligne de commande

src/io/
├── snowflake_db.py        # Connexions et requêtes SQL
├── program_snowflake_adapter.py  # I/O programmes
├── bordereau_snowflake_adapter.py # I/O bordereaux
└── run_snowflake_adapter.py      # I/O résultats
```

### Technologies actuelles
- **Connecteur** : `snowflake-connector-python`
- **Requêtes** : SQL brut avec cursors
- **Opérations** : `executemany()`, `fetch_pandas_all()`
- **Connexions** : Ponctuelles par opération

## 🚀 Architecture Cible

### Nouvelle architecture Snowpark
```
snowflake_utils/
├── config.py              # Configuration (conservé)
├── snowpark_config.py     # 🆕 Gestionnaire de sessions Snowpark
├── procedures.py          # 🆕 Procédures stockées Python
└── utils.py               # Utilitaires (adapté)

src/io/
├── snowpark_db.py         # 🆕 Sessions et DataFrames Snowpark
├── program_snowpark_adapter.py  # 🆕 I/O programmes Snowpark
├── bordereau_snowpark_adapter.py # 🆕 I/O bordereaux Snowpark
└── run_snowpark_adapter.py      # 🆕 I/O résultats Snowpark
```

### Technologies cibles
- **Framework** : `snowflake-snowpark-python` ✅ (déjà installé)
- **API** : DataFrames Snowpark + procédures Python
- **Exécution** : Côté serveur Snowflake
- **Sessions** : Persistantes et réutilisables

## 📋 Plan de Migration

### Phase 1 : Infrastructure (Semaine 1-2)

#### 1.1 Gestionnaire de sessions Snowpark
```python
# snowflake_utils/snowpark_config.py
from snowflake.snowpark import Session
from .config import SnowflakeConfig

class SnowparkSessionManager:
    """Gestionnaire centralisé des sessions Snowpark"""
    
    def __init__(self):
        self._session: Optional[Session] = None
    
    def get_session(self) -> Session:
        if self._session is None:
            config = SnowflakeConfig.load()
            self._session = Session.builder.configs(config.to_dict()).create()
        return self._session
    
    def close(self):
        if self._session:
            self._session.close()
            self._session = None
```

#### 1.2 Adapter hybride pour transition
```python
# src/io/program_hybrid_adapter.py
class HybridProgramIO:
    """Adapter supportant Snowflake classique et Snowpark"""
    
    def __init__(self, use_snowpark: bool = False):
        self.use_snowpark = use_snowpark
        if use_snowpark:
            self.snowpark_io = SnowparkProgramIO(session_manager.get_session())
        else:
            self.snowflake_io = SnowflakeProgramIO()
```

### Phase 2 : Procédures Stockées Python (Semaine 3-4)

#### 2.1 Procédure de lecture de programme
```python
# snowflake_utils/procedures.py
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col, lit

def create_read_program_procedure(session: Session):
    """Crée la procédure de lecture de programme"""
    
    @session.sproc(
        name="READ_PROGRAM",
        packages=["snowflake-snowpark-python", "pandas"],
        is_permanent=True,
        stage_location="@my_stage"
    )
    def read_program(program_id: int) -> str:
        """Lit un programme complet depuis Snowflake"""
        import json
        
        # Lecture avec DataFrames Snowpark
        program_df = session.table("REINSURANCE_PROGRAM").filter(
            col("REINSURANCE_PROGRAM_ID") == lit(program_id)
        ).to_pandas()
        
        structures_df = session.table("RP_STRUCTURES").filter(
            col("REINSURANCE_PROGRAM_ID") == lit(program_id)
        ).to_pandas()
        
        conditions_df = session.table("RP_CONDITIONS").filter(
            col("REINSURANCE_PROGRAM_ID") == lit(program_id)
        ).to_pandas()
        
        exclusions_df = session.table("RP_GLOBAL_EXCLUSION").filter(
            col("REINSURANCE_PROGRAM_ID") == lit(program_id)
        ).to_pandas()
        
        # Retourner les données sérialisées
        return json.dumps({
            "program": program_df.to_dict('records'),
            "structures": structures_df.to_dict('records'),
            "conditions": conditions_df.to_dict('records'),
            "exclusions": exclusions_df.to_dict('records')
        })
    
    return read_program
```

#### 2.2 Procédure d'écriture de programme
```python
def create_write_program_procedure(session: Session):
    """Crée la procédure d'écriture de programme"""
    
    @session.sproc(
        name="WRITE_PROGRAM",
        packages=["snowflake-snowpark-python", "pandas"],
        is_permanent=True,
        stage_location="@my_stage"
    )
    def write_program(program_data: str) -> int:
        """Sauvegarde un programme dans Snowflake"""
        import json
        import pandas as pd
        
        data = json.loads(program_data)
        
        # Insérer le programme principal
        program_df = pd.DataFrame(data["program"])
        program_df = program_df.drop(columns=['REINSURANCE_PROGRAM_ID'], errors='ignore')
        
        session.write_pandas(
            program_df, 
            "REINSURANCE_PROGRAM", 
            auto_create_table=False,
            overwrite=False
        )
        
        # Récupérer l'ID généré
        program_id = session.sql(
            "SELECT MAX(REINSURANCE_PROGRAM_ID) FROM REINSURANCE_PROGRAM"
        ).collect()[0][0]
        
        # Insérer les structures
        if data["structures"]:
            structures_df = pd.DataFrame(data["structures"])
            structures_df["REINSURANCE_PROGRAM_ID"] = program_id
            structures_df = structures_df.drop(columns=['RP_STRUCTURE_ID'], errors='ignore')
            
            session.write_pandas(
                structures_df, 
                "RP_STRUCTURES", 
                auto_create_table=False,
                overwrite=False
            )
        
        # Insérer les conditions
        if data["conditions"]:
            conditions_df = pd.DataFrame(data["conditions"])
            conditions_df["REINSURANCE_PROGRAM_ID"] = program_id
            
            session.write_pandas(
                conditions_df, 
                "RP_CONDITIONS", 
                auto_create_table=False,
                overwrite=False
            )
        
        # Insérer les exclusions
        if data["exclusions"]:
            exclusions_df = pd.DataFrame(data["exclusions"])
            exclusions_df["REINSURANCE_PROGRAM_ID"] = program_id
            
            session.write_pandas(
                exclusions_df, 
                "RP_GLOBAL_EXCLUSION", 
                auto_create_table=False,
                overwrite=False
            )
        
        return program_id
    
    return write_program
```

#### 2.3 Procédure d'application de programme sur bordereau
```python
def create_apply_program_procedure(session: Session):
    """Crée la procédure d'application de programme"""
    
    @session.sproc(
        name="APPLY_PROGRAM_TO_BORDEREAU",
        packages=["snowflake-snowpark-python", "pandas"],
        is_permanent=True,
        stage_location="@my_stage"
    )
    def apply_program_to_bordereau(program_id: int, bordereau_table: str) -> str:
        """Applique un programme de réassurance sur un bordereau"""
        import json
        
        # Charger le programme via la procédure de lecture
        program_data_json = session.call("READ_PROGRAM", program_id)
        program_data = json.loads(program_data_json)
        
        # Charger le bordereau
        bordereau_df = session.table(bordereau_table).to_pandas()
        
        # Logique d'application de la réassurance
        # (Utiliser les DataFrames Snowpark pour les calculs complexes)
        
        # Exemple de calcul avec Snowpark
        results_df = session.table(bordereau_table).select(
            col("*"),
            (col("PREMIUM") * 0.1).alias("REINSURANCE_PREMIUM")
        ).to_pandas()
        
        # Sauvegarder les résultats
        session.write_pandas(
            results_df, 
            "REINSURANCE_RESULTS", 
            auto_create_table=True,
            overwrite=True
        )
        
        return f"SUCCESS: {len(results_df)} policies processed"
    
    return apply_program_to_bordereau
```

### Phase 3 : Migration des Adapters (Semaine 5-6)

#### 3.1 Adapter Snowpark pour les programmes
```python
# src/io/program_snowpark_adapter.py
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col, lit
import pandas as pd

class SnowparkProgramIO:
    """I/O programmes avec Snowpark"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def read(self, program_id: int) -> tuple:
        """Lit un programme via procédure stockée"""
        program_data_json = self.session.call("READ_PROGRAM", program_id)
        
        import json
        data = json.loads(program_data_json)
        
        return (
            pd.DataFrame(data["program"]),
            pd.DataFrame(data["structures"]),
            pd.DataFrame(data["conditions"]),
            pd.DataFrame(data["exclusions"]),
            pd.DataFrame()  # field_links si nécessaire
        )
    
    def write(self, program_data: dict) -> int:
        """Sauvegarde un programme via procédure stockée"""
        import json
        program_data_json = json.dumps(program_data)
        
        program_id = self.session.call("WRITE_PROGRAM", program_data_json)
        return program_id
```

#### 3.2 Adapter Snowpark pour les bordereaux
```python
# src/io/bordereau_snowpark_adapter.py
class SnowparkBordereauIO:
    """I/O bordereaux avec Snowpark"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def read(self, table_name: str) -> pd.DataFrame:
        """Lit un bordereau via DataFrame Snowpark"""
        return self.session.table(table_name).to_pandas()
    
    def write(self, df: pd.DataFrame, table_name: str) -> None:
        """Écrit un bordereau via Snowpark"""
        self.session.write_pandas(
            df, 
            table_name, 
            auto_create_table=True,
            overwrite=True
        )
```

### Phase 4 : Migration du ProgramManager (Semaine 7-8)

#### 4.1 ProgramManager Snowpark
```python
# src/managers/program_snowpark_manager.py
from snowflake_utils.snowpark_config import SnowparkSessionManager
from src.io.program_snowpark_adapter import SnowparkProgramIO

class SnowparkProgramManager:
    """Program Manager utilisant Snowpark"""
    
    def __init__(self):
        self.session_manager = SnowparkSessionManager()
        self.session = self.session_manager.get_session()
        self.io = SnowparkProgramIO(self.session)
    
    def load(self, program_id: int) -> Program:
        """Charge un programme via Snowpark"""
        dfs = self.io.read(program_id)
        return self.serializer.dataframes_to_program(*dfs)
    
    def save(self, program: Program) -> int:
        """Sauvegarde un programme via Snowpark"""
        dfs = self.serializer.program_to_dataframes(program)
        return self.io.write(dfs)
    
    def apply_to_bordereau(self, program_id: int, bordereau_table: str) -> str:
        """Applique un programme sur un bordereau"""
        return self.session.call("APPLY_PROGRAM_TO_BORDEREAU", program_id, bordereau_table)
```

### Phase 5 : Tests et Validation (Semaine 9-10)

#### 5.1 Tests de compatibilité
```python
# tests/integration/test_snowpark_migration.py
def test_snowpark_vs_snowflake_compatibility():
    """Test de compatibilité entre Snowpark et Snowflake classique"""
    
    # Test avec Snowflake classique
    classic_manager = ProgramManager(backend="snowflake")
    classic_program = classic_manager.load("snowflake://db.schema?program_id=1")
    
    # Test avec Snowpark
    snowpark_manager = SnowparkProgramManager()
    snowpark_program = snowpark_manager.load(1)
    
    # Vérifier l'équivalence
    assert classic_program.title == snowpark_program.title
    assert len(classic_program.structures) == len(snowpark_program.structures)
```

#### 5.2 Tests de performance
```python
def test_performance_comparison():
    """Comparaison des performances"""
    import time
    
    # Test Snowflake classique
    start = time.time()
    classic_result = classic_manager.apply_to_bordereau(1, "BORDEREAU_TEST")
    classic_time = time.time() - start
    
    # Test Snowpark
    start = time.time()
    snowpark_result = snowpark_manager.apply_to_bordereau(1, "BORDEREAU_TEST")
    snowpark_time = time.time() - start
    
    print(f"Snowflake classique: {classic_time:.2f}s")
    print(f"Snowpark: {snowpark_time:.2f}s")
```

## 🔧 Configuration et Déploiement

### 1. Variables d'environnement
```bash
# snowflake_config.env
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=MYDB
SNOWFLAKE_SCHEMA=MYSCHEMA
SNOWFLAKE_ROLE=PUBLIC

# Nouveau pour Snowpark
SNOWFLAKE_STAGE_LOCATION=@my_stage
```

### 2. Script de déploiement des procédures
```python
# scripts/deploy_snowpark_procedures.py
from snowflake_utils.snowpark_config import SnowparkSessionManager
from snowflake_utils.procedures import (
    create_read_program_procedure,
    create_write_program_procedure,
    create_apply_program_procedure
)

def deploy_procedures():
    """Déploie toutes les procédures Snowpark"""
    session_manager = SnowparkSessionManager()
    session = session_manager.get_session()
    
    # Créer les procédures
    create_read_program_procedure(session)
    create_write_program_procedure(session)
    create_apply_program_procedure(session)
    
    print("✅ Toutes les procédures Snowpark ont été déployées")
```

### 3. Migration des données existantes
```python
# scripts/migrate_to_snowpark.py
def migrate_existing_programs():
    """Migre les programmes existants vers Snowpark"""
    classic_manager = ProgramManager(backend="snowflake")
    snowpark_manager = SnowparkProgramManager()
    
    # Lister tous les programmes existants
    programs = classic_manager.list_programs()
    
    for program in programs:
        # Charger avec l'ancien système
        classic_program = classic_manager.load(f"snowflake://db.schema?program_id={program['id']}")
        
        # Sauvegarder avec Snowpark
        new_id = snowpark_manager.save(classic_program)
        
        print(f"✅ Programme {program['title']} migré (ID: {program['id']} → {new_id})")
```

## 📈 Avantages Attendus

### Performance
- **Exécution côté serveur** : Réduction de la latence réseau
- **Traitement distribué** : Utilisation optimale des ressources Snowflake
- **Cache intelligent** : Réutilisation des résultats intermédiaires

### Développement
- **API unifiée** : DataFrames Snowpark similaires à pandas
- **Procédures Python** : Logique métier en Python natif
- **Débogage facilité** : Outils de développement intégrés

### Maintenance
- **Code centralisé** : Procédures stockées dans Snowflake
- **Versioning** : Gestion des versions des procédures
- **Monitoring** : Métriques d'exécution intégrées

## 🚨 Points d'Attention

### Limitations
- **Dépendances** : Packages Python limités dans Snowpark
- **Debugging** : Plus complexe pour les procédures stockées
- **Migration** : Transition progressive nécessaire

### Risques
- **Compatibilité** : Tests approfondis requis
- **Performance** : Optimisation nécessaire pour les gros volumes
- **Formation** : Équipe à former sur Snowpark

## 📅 Planning de Migration

| Semaine | Phase | Activités |
|---------|-------|-----------|
| 1-2 | Infrastructure | Configuration Snowpark, gestionnaire de sessions |
| 3-4 | Procédures | Création des procédures stockées Python |
| 5-6 | Adapters | Migration des adapters I/O |
| 7-8 | Managers | Migration du ProgramManager |
| 9-10 | Tests | Tests de compatibilité et performance |
| 11-12 | Déploiement | Migration complète et documentation |

## 🎯 Prochaines Étapes

1. **Validation du plan** avec l'équipe
2. **Création de l'environnement de test** Snowpark
3. **Implémentation de la Phase 1** (Infrastructure)
4. **Tests de validation** des procédures
5. **Migration progressive** par composant

---

*Ce document sera mis à jour au fur et à mesure de l'avancement de la migration.*
