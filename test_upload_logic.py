#!/usr/bin/env python3
"""
Test de la logique d'upload de dossier pour l'application Streamlit
"""

import tempfile
from pathlib import Path
from src.managers import ProgramManager


def test_upload_logic():
    """Test de la logique de reconstruction de dossier CSV."""

    print("🧪 Test de la logique d'upload de dossier CSV")
    print("=" * 50)

    # Simuler l'upload d'un dossier avec des fichiers dans un sous-dossier
    simulated_uploaded_files = [
        "aviation_axa_xl_2024/program.csv",
        "aviation_axa_xl_2024/structures.csv",
        "aviation_axa_xl_2024/conditions.csv",
    ]

    # Copier les vrais fichiers pour le test
    source_dir = Path("examples/programs/aviation_axa_xl_2024")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir_path = Path(tmp_dir)

        print(f"📁 Dossier temporaire: {tmp_dir_path}")

        # Simuler la logique de l'app
        uploaded_filenames = []
        for simulated_path in simulated_uploaded_files:
            # Extraire le nom du fichier (sans le chemin du dossier)
            filename = Path(simulated_path).name
            source_file = source_dir / filename
            dest_path = tmp_dir_path / filename

            if source_file.exists():
                dest_path.write_bytes(source_file.read_bytes())
                uploaded_filenames.append(filename)
                print(f"   ✓ Copié: {simulated_path} → {filename}")
            else:
                print(f"   ❌ Fichier source manquant: {source_file}")

        # Vérifier que les fichiers requis sont présents
        required_files = ["program.csv", "structures.csv", "conditions.csv"]
        missing_files = [f for f in required_files if f not in uploaded_filenames]

        if missing_files:
            print(f"   ❌ Fichiers manquants: {missing_files}")
            return False

        print(f"   ✅ Tous les fichiers requis sont présents: {uploaded_filenames}")

        # Tester le chargement avec ProgramManager
        try:
            manager = ProgramManager(backend="csv_folder")
            program = manager.load(str(tmp_dir_path))
            print(f"   ✅ Programme chargé: {program.name}")
            print(f"   ✅ Structures: {len(program.structures)}")
            return True
        except Exception as e:
            print(f"   ❌ Erreur lors du chargement: {e}")
            return False


if __name__ == "__main__":
    success = test_upload_logic()
    if success:
        print("\n✅ Test réussi ! La logique d'upload fonctionne.")
    else:
        print("\n❌ Test échoué ! Il y a un problème avec la logique d'upload.")
