#!/usr/bin/env python3
"""
Point d'entrée pour l'exécution du module snowflake_utils en tant que CLI.

Usage:
    python -m snowflake_utils <command> [options]
"""

from .cli import main

if __name__ == "__main__":
    main()
