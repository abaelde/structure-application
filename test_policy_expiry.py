import pandas as pd
from pathlib import Path
from src.loaders import ProgramLoader, BordereauLoader
from src.engine import apply_program_to_bordereau


def test_policy_expiry_mechanism():
    print("=" * 80)
    print("TEST: Mécanisme de vérification d'expiration des polices")
    print("=" * 80)
    
    program_path = Path("examples/programs/single_quota_share.xlsx")
    print(f"\n1. Chargement du programme: {program_path}")
    loader = ProgramLoader(program_path)
    program = loader.get_program()
    print(f"   ✓ Programme chargé: {program['name']}")
    
    test_data = {
        "INSURED_NAME": ["COMPANY A", "COMPANY B", "COMPANY C", "COMPANY D"],
        "exposition": [1000000, 2000000, 500000, 750000],
        "INCEPTION_DT": ["2024-01-01", "2024-06-01", "2023-01-01", "2025-01-01"],
        "EXPIRE_DT": ["2025-01-01", "2025-06-01", "2024-01-01", "2026-01-01"],
        "line_of_business": ["Aviation", "Aviation", "Aviation", "Aviation"],
        "BUSCL_COUNTRY_CD": ["France", "Germany", "UK", "Spain"],
    }
    
    bordereau_df = pd.DataFrame(test_data)
    
    print("\n2. Bordereau de test créé:")
    print(bordereau_df.to_string(index=False))
    
    calculation_dates = [
        "2024-06-01",
        "2024-12-31",
        "2025-01-01",
        "2025-07-01",
    ]
    
    for calc_date in calculation_dates:
        print(f"\n{'=' * 80}")
        print(f"Date de calcul: {calc_date}")
        print(f"{'=' * 80}")
        
        _, results_df = apply_program_to_bordereau(
            bordereau_df, program, calculation_date=calc_date
        )
        
        print("\nRésultats:")
        print("-" * 80)
        
        for idx, row in results_df.iterrows():
            policy_name = row["INSURED_NAME"]
            expiry = bordereau_df.loc[idx, "EXPIRE_DT"]
            exposure = row["exposure"]
            effective_exposure = row["effective_exposure"]
            cession = row["cession_to_reinsurer"]
            status = row["exclusion_status"]
            
            status_symbol = "✓" if status == "included" else "✗"
            
            print(f"{status_symbol} {policy_name:15} | Expiry: {expiry} | ", end="")
            print(f"Exposure: {exposure:>10,.0f} | ", end="")
            print(f"Effective: {effective_exposure:>10,.0f} | ", end="")
            print(f"Cession: {cession:>10,.0f} | ", end="")
            print(f"Status: {status}")
            
            if status == "inactive":
                print(f"  └─ Raison: {row.get('exclusion_reason', 'N/A')}")
        
        active_count = (results_df["exclusion_status"] == "included").sum()
        inactive_count = (results_df["exclusion_status"] == "inactive").sum()
        total_cession = results_df["cession_to_reinsurer"].sum()
        
        print("\n" + "-" * 80)
        print(f"Résumé: {active_count} polices actives, {inactive_count} polices expirées")
        print(f"Cession totale au réassureur: {total_cession:,.2f}")
    
    print("\n" + "=" * 80)
    print("TEST TERMINÉ")
    print("=" * 80)


if __name__ == "__main__":
    test_policy_expiry_mechanism()

