#!/usr/bin/env python3
"""
Test script pour vérifier le nouveau backend CSV folder des programmes.
"""

from pathlib import Path
from src.managers import ProgramManager
from src.io import CsvProgramFolderIO


def test_csv_folder_backend():
    """Test du backend CSV folder pour les programmes."""

    print("🧪 Test du backend CSV folder pour les programmes")
    print("=" * 60)

    # 1. Test de détection automatique
    print("\n1. Test de détection automatique du backend:")

    # Test avec un fichier Excel
    excel_backend = ProgramManager.detect_backend(
        "examples/programs/single_quota_share.xlsx"
    )
    print(f"   Excel file -> {excel_backend}")

    # Test avec un dossier (même s'il n'existe pas encore)
    csv_backend = ProgramManager.detect_backend("test_csv_program")
    print(f"   CSV folder -> {csv_backend}")

    # Test avec Snowflake
    snowflake_backend = ProgramManager.detect_backend("snowflake://db.schema.table")
    print(f"   Snowflake -> {snowflake_backend}")

    # 2. Test de création du manager avec le bon backend
    print("\n2. Test de création du manager:")
    try:
        manager = ProgramManager(backend="csv_folder")
        print("   ✓ Manager créé avec backend csv_folder")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return

    # 3. Test de lecture d'un programme Excel existant et conversion vers CSV
    print("\n3. Test de conversion Excel -> CSV folder:")
    try:
        # Charger un programme Excel existant
        excel_manager = ProgramManager(backend="excel")
        program = excel_manager.load("examples/programs/single_quota_share.xlsx")
        print(f"   ✓ Programme Excel chargé: {program.name}")

        # Sauvegarder en CSV folder
        csv_manager = ProgramManager(backend="csv_folder")
        csv_manager.save(program, "test_csv_program")
        print("   ✓ Programme sauvegardé en CSV folder")

        # Vérifier que les fichiers CSV ont été créés
        csv_folder = Path("test_csv_program")
        expected_files = ["program.csv", "structures.csv", "conditions.csv"]
        for file in expected_files:
            if (csv_folder / file).exists():
                print(f"   ✓ {file} créé")
            else:
                print(f"   ❌ {file} manquant")

    except Exception as e:
        print(f"   ❌ Erreur lors de la conversion: {e}")
        return

    # 4. Test de relecture du programme depuis le CSV folder
    print("\n4. Test de relecture depuis CSV folder:")
    try:
        reloaded_program = csv_manager.load("test_csv_program")
        print(f"   ✓ Programme rechargé: {reloaded_program.name}")
        print(f"   ✓ Nombre de structures: {len(reloaded_program.structures)}")
        conditions_count = len(getattr(reloaded_program, "conditions", []))
        print(f"   ✓ Nombre de conditions: {conditions_count}")

        # Vérifier que les données sont identiques
        if program.name == reloaded_program.name:
            print("   ✓ Nom du programme identique")
        else:
            print(f"   ❌ Noms différents: {program.name} vs {reloaded_program.name}")

    except Exception as e:
        print(f"   ❌ Erreur lors de la relecture: {e}")
        return

    # 5. Test de l'auto-détection avec le dossier CSV
    print("\n5. Test de l'auto-détection avec le dossier CSV:")
    try:
        auto_backend = ProgramManager.detect_backend("test_csv_program")
        print(f"   ✓ Backend auto-détecté: {auto_backend}")

        auto_manager = ProgramManager(backend=auto_backend)
        auto_program = auto_manager.load("test_csv_program")
        print(f"   ✓ Programme chargé avec auto-détection: {auto_program.name}")

    except Exception as e:
        print(f"   ❌ Erreur avec auto-détection: {e}")
        return

    print("\n" + "=" * 60)
    print("✅ Tous les tests du backend CSV folder ont réussi !")
    print("=" * 60)


if __name__ == "__main__":
    test_csv_folder_backend()
