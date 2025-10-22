#!/usr/bin/env python3
"""
Script d'installation pour créer un alias global 'snowflake-cli'.

Ce script crée un lien symbolique ou un script wrapper pour rendre
la CLI snowflake_utils accessible globalement.
"""

import os
import sys
import shutil
from pathlib import Path


def install_cli():
    """Installe la CLI snowflake_utils."""

    # Chemin vers le script CLI
    project_root = Path(__file__).parent.parent
    cli_script = project_root / "snowflake_utils" / "cli.py"

    if not cli_script.exists():
        print("❌ Script CLI non trouvé")
        return False

    # Créer un script wrapper dans le projet
    wrapper_script = project_root / "snowflake-cli"

    wrapper_content = f"""#!/usr/bin/env python3
import sys
from pathlib import Path

# Ajouter le chemin du projet
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Importer et exécuter la CLI
from snowflake_utils.cli import main

if __name__ == '__main__':
    sys.exit(main())
"""

    try:
        with open(wrapper_script, "w") as f:
            f.write(wrapper_content)

        # Rendre le script exécutable
        os.chmod(wrapper_script, 0o755)

        print("✅ CLI installée avec succès !")
        print(f"📁 Script créé: {wrapper_script}")
        print()
        print("🚀 Utilisation:")
        print(f"   {wrapper_script} <command> [options]")
        print("   ou")
        print(f"   python -m snowflake_utils <command> [options]")
        print()
        print("📋 Commandes disponibles:")
        print("   test                    # Tester la connexion")
        print("   status                  # Statut complet du système")
        print("   list-programs           # Lister tous les programmes")
        print("   reset-tables --force    # Reset complet des tables")
        print("   truncate-tables         # Vider les tables")
        print('   sql "SELECT ..."        # Requête SQL')

        return True

    except Exception as e:
        print(f"❌ Erreur lors de l'installation: {e}")
        return False


if __name__ == "__main__":
    install_cli()
