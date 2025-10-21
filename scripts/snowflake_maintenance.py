#!/usr/bin/env python3
"""
Script de maintenance Snowflake - Utilitaires pour gérer les tables et données.

Ce script utilise le module snowflake_utils pour fournir des commandes simples
de maintenance des tables Snowflake.
"""

import sys
import os
from pathlib import Path

# Ajouter le chemin du projet
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from snowflake_utils import (
    test_connection, 
    list_programs, 
    delete_program,
    reset_all_tables,
    truncate_all_tables
)

def main():
    """Menu principal pour les opérations de maintenance."""
    
    print("🔧 Maintenance Snowflake")
    print("=" * 50)
    
    while True:
        print("\n📋 Options disponibles:")
        print("1. 🔗 Tester la connexion")
        print("2. 📊 Lister tous les programmes")
        print("3. 🗑️  Supprimer un programme")
        print("4. 🧹 Vider toutes les tables (TRUNCATE)")
        print("5. 🔄 Reset complet (DROP + CREATE)")
        print("6. ❌ Quitter")
        
        choice = input("\n👉 Votre choix (1-6): ").strip()
        
        if choice == "1":
            print("\n🔗 Test de connexion...")
            if test_connection():
                print("✅ Connexion réussie !")
            else:
                print("❌ Échec de la connexion")
                
        elif choice == "2":
            print("\n📊 Liste des programmes...")
            programs = list_programs()
            if programs:
                for program in programs:
                    print(f"   - {program}")
            else:
                print("   Aucun programme trouvé")
                
        elif choice == "3":
            program_title = input("\n📝 Nom du programme à supprimer: ").strip()
            if program_title:
                print(f"\n🗑️  Suppression du programme '{program_title}'...")
                if delete_program(program_title):
                    print("✅ Programme supprimé avec succès")
                else:
                    print("❌ Échec de la suppression")
            else:
                print("❌ Nom de programme requis")
                
        elif choice == "4":
            confirm = input("\n⚠️  Vider toutes les tables ? (oui/non): ").strip().lower()
            if confirm in ["oui", "o", "yes", "y"]:
                print("\n🧹 Vidage de toutes les tables...")
                if truncate_all_tables():
                    print("✅ Tables vidées avec succès")
                else:
                    print("❌ Échec du vidage")
            else:
                print("❌ Opération annulée")
                
        elif choice == "5":
            confirm = input("\n⚠️  Reset complet (suppression + recréation) ? (oui/non): ").strip().lower()
            if confirm in ["oui", "o", "yes", "y"]:
                print("\n🔄 Reset complet des tables...")
                if reset_all_tables():
                    print("✅ Reset terminé avec succès")
                else:
                    print("❌ Échec du reset")
            else:
                print("❌ Opération annulée")
                
        elif choice == "6":
            print("\n👋 Au revoir !")
            break
            
        else:
            print("❌ Choix invalide")

if __name__ == "__main__":
    main()
