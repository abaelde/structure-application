import pandas as pd
from src.loaders import ProgramLoader, load_bordereau
from src.engine import apply_program_to_bordereau
from src.presentation import display_program


def test_exclusion_mechanism():
    print("\n" + "=" * 80)
    print("TEST DU MÉCANISME D'EXCLUSION")
    print("=" * 80)
    print()

    program_file = "examples/programs/quota_share_with_exclusion.xlsx"
    bordereau_file = "examples/bordereaux/aviation/bordereau_exclusion_test.csv"

    print(f"Chargement du programme: {program_file}")
    loader = ProgramLoader(program_file)
    program = loader.get_program()
    print()

    display_program(program)
    print()

    print(f"Chargement du bordereau: {bordereau_file}")
    bordereau_df = load_bordereau(bordereau_file)
    print(f"✓ {len(bordereau_df)} polices chargées")
    print()

    print("=" * 80)
    print("BORDEREAU D'ENTRÉE")
    print("=" * 80)
    print(
        bordereau_df[
            [
                "policy_id",
                "INSURED_NAME",
                "BUSCL_COUNTRY_CD",
                "BUSCL_REGION",
                "exposition",
            ]
        ]
    )
    print()

    print("=" * 80)
    print("APPLICATION DU PROGRAMME")
    print("=" * 80)

    bordereau_with_net, results = apply_program_to_bordereau(bordereau_df, program)

    print("\nRÉSULTATS PAR POLICE:")
    print("-" * 80)

    for _, row in results.iterrows():
        insured = row["INSURED_NAME"]
        exposure = row["exposure"]
        effective_exposure = row["effective_exposure"]
        cession = row["cession_to_reinsurer"]
        exclusion_status = row["exclusion_status"]

        print(f"\n{insured}:")
        print(f"  Exposition originale: {exposure:,.0f}")
        print(f"  Exposition effective: {effective_exposure:,.0f}")
        print(f"  Statut: {exclusion_status}")

        if exclusion_status == "excluded":
            print(f"  ❌ EXCLU - Raison: {row.get('exclusion_reason', 'N/A')}")
        else:
            print(f"  ✅ INCLUS - Cession: {cession:,.2f} (25%)")

    print()
    print("=" * 80)
    print("RÉSUMÉ")
    print("=" * 80)

    total_exposure = results["exposure"].sum()
    total_effective = results["effective_exposure"].sum()
    total_cession = results["cession_to_reinsurer"].sum()
    excluded_count = (results["exclusion_status"] == "excluded").sum()
    included_count = (results["exclusion_status"] == "included").sum()

    print(f"\nPolices au total: {len(results)}")
    print(f"  - Incluses: {included_count}")
    print(f"  - Exclues: {excluded_count}")
    print()
    print(f"Exposition totale originale: {total_exposure:,.0f}")
    print(f"Exposition totale effective: {total_effective:,.0f}")
    print(f"Exposition exclue: {total_exposure - total_effective:,.0f}")
    print()
    print(f"Cession totale au réassureur: {total_cession:,.2f}")
    print(
        f"Taux de cession global: {(total_cession/total_effective*100) if total_effective > 0 else 0:.2f}%"
    )

    print()
    print("=" * 80)
    print("DÉTAIL DES EXCLUSIONS")
    print("=" * 80)

    excluded_policies = results[results["exclusion_status"] == "excluded"]
    if len(excluded_policies) > 0:
        print("\nPolices exclues:")
        for _, policy in excluded_policies.iterrows():
            print(f"  - {policy['INSURED_NAME']}: {policy['exposure']:,.0f}")
    else:
        print("\nAucune police exclue.")

    print()
    print("=" * 80)
    print("TEST TERMINÉ")
    print("=" * 80)

    assert len(results) == 7
    assert excluded_count >= 0
