"""
Configuration Snowflake centralisée.

Ce module gère la configuration de connexion Snowflake de manière centralisée
et sécurisée.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional


class SnowflakeConfig:
    """
    Configuration centralisée pour Snowflake.

    Gère le chargement de la configuration depuis :
    1. Variables d'environnement (priorité)
    2. Fichier snowflake_config.env
    3. Valeurs par défaut
    """

    # Noms des variables d'environnement
    ENV_VARS = {
        "account": "SNOWFLAKE_ACCOUNT",
        "user": "SNOWFLAKE_USER",
        "password": "SNOWFLAKE_PASSWORD",
        "warehouse": "SNOWFLAKE_WAREHOUSE",
        "database": "SNOWFLAKE_DATABASE",
        "schema": "SNOWFLAKE_SCHEMA",
        "role": "SNOWFLAKE_ROLE",
    }

    # Valeurs par défaut
    DEFAULT_VALUES = {
        "account": "your_account",
        "user": "your_user",
        "password": "your_password",
        "warehouse": "COMPUTE_WH",
        "database": "MYDB",
        "schema": "MYSCHEMA",
        "role": "PUBLIC",
    }

    def __init__(self, **kwargs):
        """Initialise la configuration avec les valeurs fournies."""
        self.account = kwargs.get("account")
        self.user = kwargs.get("user")
        self.password = kwargs.get("password")
        self.warehouse = kwargs.get("warehouse")
        self.database = kwargs.get("database")
        self.schema = kwargs.get("schema")
        self.role = kwargs.get("role")

    @classmethod
    def load(cls, config_file: Optional[Path] = None) -> "SnowflakeConfig":
        """
        Charge la configuration depuis les sources disponibles.

        Args:
            config_file: Chemin vers le fichier de config (optionnel)

        Returns:
            Instance de SnowflakeConfig avec la configuration chargée

        Raises:
            FileNotFoundError: Si aucun fichier de config n'est trouvé
        """
        config = {}

        # 1. Charger depuis les variables d'environnement (priorité)
        for key, env_var in cls.ENV_VARS.items():
            value = os.getenv(env_var)
            if value:
                config[key] = value

        # 2. Charger depuis le fichier de configuration
        if config_file is None:
            # Chercher le fichier à la racine du projet
            project_root = Path(__file__).parent.parent
            config_file = project_root / "snowflake_config.env"

        if config_file.exists():
            with open(config_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        # Mapper les clés du fichier vers les clés internes
                        if key == "SNOWFLAKE_ACCOUNT" and "account" not in config:
                            config["account"] = value
                        elif key == "SNOWFLAKE_USER" and "user" not in config:
                            config["user"] = value
                        elif key == "SNOWFLAKE_PASSWORD" and "password" not in config:
                            config["password"] = value
                        elif key == "SNOWFLAKE_WAREHOUSE" and "warehouse" not in config:
                            config["warehouse"] = value
                        elif key == "SNOWFLAKE_DATABASE" and "database" not in config:
                            config["database"] = value
                        elif key == "SNOWFLAKE_SCHEMA" and "schema" not in config:
                            config["schema"] = value
                        elif key == "SNOWFLAKE_ROLE" and "role" not in config:
                            config["role"] = value

        # 3. Utiliser les valeurs par défaut pour les clés manquantes
        for key, default_value in cls.DEFAULT_VALUES.items():
            if key not in config:
                config[key] = default_value

        return cls(**config)

    def to_dict(self) -> Dict[str, Any]:
        """Retourne la configuration sous forme de dictionnaire."""
        return {
            "account": self.account,
            "user": self.user,
            "password": self.password,
            "warehouse": self.warehouse,
            "database": self.database,
            "schema": self.schema,
            "role": self.role,
        }

    def validate(self) -> bool:
        """
        Valide que la configuration est complète.

        Returns:
            True si la configuration est valide, False sinon
        """
        required_fields = [
            "account",
            "user",
            "password",
            "warehouse",
            "database",
            "schema",
        ]

        # Vérifier que les champs critiques ne sont pas les valeurs par défaut
        critical_defaults = {
            "account": "your_account",
            "user": "your_user",
            "password": "your_password",
        }

        for field in required_fields:
            value = getattr(self, field)
            if not value:
                print(f"❌ Configuration Snowflake invalide: {field} manquant")
                return False

            # Pour les champs critiques, vérifier qu'ils ne sont pas les valeurs par défaut
            if field in critical_defaults and value == critical_defaults[field]:
                print(
                    f"❌ Configuration Snowflake invalide: {field} utilise la valeur par défaut"
                )
                return False

        return True

    def get_connection_string(self) -> str:
        """
        Retourne la chaîne de connexion Snowflake.

        Returns:
            Chaîne de connexion formatée
        """
        return f"snowflake://{self.account}.snowflakecomputing.com"

    def get_dsn(self, program_title: str) -> str:
        """
        Retourne le DSN pour un programme spécifique (legacy).

        Args:
            program_title: Titre du programme

        Returns:
            DSN formaté pour le programme
        """
        return (
            f"snowflake://{self.database}.{self.schema}?program_title={program_title}"
        )

    def get_dsn_by_id(self, program_id: int) -> str:
        """
        Retourne le DSN pour un programme spécifique par ID.

        Args:
            program_id: ID du programme

        Returns:
            DSN formaté pour le programme
        """
        return (
            f"snowflake://{self.database}.{self.schema}?program_id={program_id}"
        )

    def __repr__(self) -> str:
        """Représentation de la configuration (sans le mot de passe)."""
        safe_config = self.to_dict()
        safe_config["password"] = "***"
        return f"SnowflakeConfig({safe_config})"
