"""
Script maître pour régénérer tous les programmes à partir des scripts Python
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import subprocess
import glob


def regenerate_all_programs():
    print("🔄 Régénération de tous les programmes ...")
    print("=" * 60)

    # Trouver tous les scripts de création
    script_dir = os.path.dirname(__file__)
    creation_scripts = glob.glob(os.path.join(script_dir, "create_*.py"))

    # Exclure le script de régénération lui-même
    creation_scripts = [
        s for s in creation_scripts if not s.endswith("regenerate_all_programs.py")
    ]

    if not creation_scripts:
        print("❌ Aucun script de création trouvé")
        return

    print(f"📁 Dossier: {script_dir}")
    print(f"📄 Scripts trouvés: {len(creation_scripts)}")

    for script_path in creation_scripts:
        script_name = os.path.basename(script_path)
        print(f"\n🔧 Exécution de {script_name}...")

        try:
            # Exécuter le script
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(__file__),
            )

            if result.returncode == 0:
                print(f"   ✅ {script_name} exécuté avec succès")
                # Afficher la sortie si elle contient des informations utiles
                if "✓" in result.stdout:
                    lines = result.stdout.strip().split("\n")
                    for line in lines:
                        if "✓" in line:
                            print(f"   {line}")
            else:
                print(f"   ❌ Erreur dans {script_name}:")
                print(f"   {result.stderr}")

        except Exception as e:
            print(f"   ❌ Exception lors de l'exécution de {script_name}: {e}")

    print(f"\n✅ Régénération des programmes individuels terminée !")

    # Combiner tous les programmes en une base de données simulée
    print("\n" + "=" * 60)
    print("🔗 Combinaison de tous les programmes en all_programs...")
    print("=" * 60)

    combine_script = os.path.join(script_dir, "combine_all_programs.py")
    if os.path.exists(combine_script):
        try:
            result = subprocess.run(
                [sys.executable, combine_script],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(__file__),
            )

            if result.returncode == 0:
                print("   ✅ all_programs créé avec succès")
            else:
                print(f"   ❌ Erreur lors de la combinaison:")
                print(f"   {result.stderr}")

        except Exception as e:
            print(f"   ❌ Exception lors de la combinaison: {e}")
    else:
        print("   ⚠️  Script combine_all_programs.py non trouvé")

    print(f"\n📋 Programmes disponibles dans examples/programs/:")

    programs_dir = os.path.join(os.path.dirname(__file__), "..", "programs")
    if os.path.exists(programs_dir):
        csv_folders = sorted([d for d in os.listdir(programs_dir) 
                             if os.path.isdir(os.path.join(programs_dir, d))])
        for csv_folder in csv_folders:
            if csv_folder == "all_programs":
                print(f"   🗄️  {csv_folder}/ (base de données simulée)")
            else:
                print(f"   📊 {csv_folder}/")


if __name__ == "__main__":
    regenerate_all_programs()
