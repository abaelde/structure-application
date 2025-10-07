"""
Exemple d'utilisation pratique de la logique claim_basis
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

import pandas as pd
from structures.treaty_manager import TreatyManager
from structures.structure_engine import apply_treaty_manager_to_bordereau


def example_claim_basis_usage():
    print("Exemple d'utilisation de la logique claim_basis")
    print("=" * 60)

    # 1. Charger les traités multi-années
    print("1. Chargement des traités...")
    treaty_paths = {
        "2023": "examples/treaties/treaty_2023.xlsx",
        "2024": "examples/treaties/treaty_2024.xlsx",
        "2025": "examples/treaties/treaty_2025.xlsx",
    }

    treaty_manager = TreatyManager(treaty_paths)
    print(f"   ✓ {len(treaty_manager.get_available_years())} traités chargés")

    # 2. Charger le bordereau
    print("\n2. Chargement du bordereau...")
    bordereau_df = pd.read_csv("examples/bordereaux/bordereau_multi_year_test.csv")
    print(f"   ✓ {len(bordereau_df)} polices chargées")

    # 3. Calcul "as of now" en mi-2025
    print("\n3. Calcul 'as of now' en mi-2025...")
    calculation_date = "2025-06-15"
    results = apply_treaty_manager_to_bordereau(
        bordereau_df, treaty_manager, calculation_date
    )

    # 4. Afficher les résultats
    print(f"\n4. Résultats du calcul en {calculation_date}:")
    print("-" * 60)

    for _, result in results.iterrows():
        print(f"\n📋 Police: {result['policy_number']}")
        print(f"   Souscription: {result['policy_inception_date']}")
        print(f"   Traité appliqué: {result['selected_treaty_year']}")
        print(f"   Claim basis: {result['claim_basis']}")
        print(f"   Statut: {result['coverage_status']}")
        print(f"   Exposition: {result['exposure']:,.0f}")
        print(f"   Cédé: {result['ceded']:,.0f}")
        print(f"   Retenu: {result['retained']:,.0f}")

        if result["structures_detail"]:
            print(f"   Structures appliquées:")
            for detail in result["structures_detail"]:
                print(f"     - {detail['structure_name']}: {detail['ceded']:,.0f}")

    # 5. Résumé par traité
    print(f"\n5. Résumé par traité appliqué:")
    print("-" * 60)

    treaty_summary = (
        results.groupby("selected_treaty_year")
        .agg(
            {
                "policy_number": "count",
                "exposure": "sum",
                "ceded": "sum",
                "retained": "sum",
            }
        )
        .round(0)
    )

    treaty_summary.columns = [
        "Nb_Polices",
        "Exposition_Totale",
        "Cédé_Total",
        "Retenu_Total",
    ]
    print(treaty_summary.to_string())

    # 6. Analyse des cas sans couverture
    print(f"\n6. Analyse des cas sans couverture:")
    print("-" * 60)

    no_coverage = results[results["coverage_status"] == "no_treaty_found"]
    if len(no_coverage) > 0:
        print(f"   ⚠️  {len(no_coverage)} polices sans couverture:")
        for _, policy in no_coverage.iterrows():
            print(
                f"     - {policy['policy_number']} (souscription: {policy['policy_inception_date']})"
            )
    else:
        print("   ✅ Toutes les polices sont couvertes")

    print(f"\n✅ Exemple terminé avec succès !")
    print(f"\nPoints clés de la logique claim_basis:")
    print(f"  • Risk Attaching: Traité de l'année de souscription")
    print(f"  • Loss Occurring: Traité de l'année de calcul")
    print(f"  • Pas de traité: Aucune couverture")


if __name__ == "__main__":
    example_claim_basis_usage()
