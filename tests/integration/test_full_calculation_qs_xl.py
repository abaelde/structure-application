import pandas as pd
import pytest
from pathlib import Path
from src.loaders import ProgramLoader
from src.engine import apply_program_to_bordereau


def test_quota_share_then_excess_of_loss_with_rescaling():
    """
    Test complet grandeur réelle : QS → XL avec rescaling
    
    STRUCTURE DU PROGRAMME:
    1. QS_30% : Quota Share 30% (reinsurer share 100%)
    2. XOL_50xs20 : Excess of Loss 50M xs 20M (reinsurer share 100%) - inuring sur QS_30%
    
    POLICES DE TEST:
    - Policy A: 50M  → En dessous de l'attachment XL après QS
    - Policy B: 100M → Partiellement dans la layer XL après QS
    - Policy C: 150M → Complètement dans et au-dessus de la layer XL après QS
    
    CALCULS ATTENDUS:
    
    Policy A (50M):
    ---------------
    QS_30%: 50M * 30% = 15M cédé, 35M retenu
    XOL_50xs20 sur 35M: attachment=20M*(1-30%)=14M, limit=50M*(1-30%)=35M
        → 35M < 14M? Non, 35M > 14M, donc cession = min(35M - 14M, 35M) = 21M
    Total cession: 15M (QS) + 21M (XL) = 36M
    Retained: 50M - 36M = 14M
    
    Policy B (100M):
    ----------------
    QS_30%: 100M * 30% = 30M cédé, 70M retenu
    XOL_50xs20 sur 70M: attachment=14M, limit=35M
        → 70M > 14M, cession = min(70M - 14M, 35M) = min(56M, 35M) = 35M
    Total cession: 30M (QS) + 35M (XL) = 65M
    Retained: 100M - 65M = 35M
    
    Policy C (150M):
    ----------------
    QS_30%: 150M * 30% = 45M cédé, 105M retenu
    XOL_50xs20 sur 105M: attachment=14M, limit=35M
        → 105M > 14M, cession = min(105M - 14M, 35M) = 35M
    Total cession: 45M (QS) + 35M (XL) = 80M
    Retained: 150M - 80M = 70M
    """
    
    print("\n" + "=" * 80)
    print("TEST GRANDEUR RÉELLE : QS 30% → XL 50M xs 20M avec RESCALING")
    print("=" * 80)
    
    # 1. Créer le programme de test
    program_path = Path("tests/integration/fixtures/programs/test_program_qs_xl.xlsx")
    
    if not program_path.exists():
        pytest.skip(f"Programme de test non trouvé: {program_path}")
    
    print(f"\n1. Chargement du programme: {program_path}")
    loader = ProgramLoader(program_path)
    program = loader.get_program()
    print(f"   ✓ Programme chargé: {program.name}")
    print(f"   ✓ Structures: {len(program.structures)}")
    
    # 2. Créer le bordereau de test
    print("\n2. Création du bordereau de test avec 3 polices:")
    
    test_data = {
        "policy_id": ["POL-A", "POL-B", "POL-C"],
        "INSURED_NAME": ["Company A", "Company B", "Company C"],
        "exposition": [50_000_000, 100_000_000, 150_000_000],
        "INCEPTION_DT": ["2024-01-01", "2024-01-01", "2024-01-01"],
        "EXPIRE_DT": ["2025-01-01", "2025-01-01", "2025-01-01"],
        # Toutes les colonnes dimensionnelles requises
        "BUSCL_EXCLUDE_CD": [None, None, None],
        "BUSCL_ENTITY_NAME_CED": [None, None, None],
        "POL_RISK_NAME_CED": [None, None, None],
        "BUSCL_COUNTRY_CD": ["US", "US", "US"],
        "BUSCL_REGION": [None, None, None],
        "BUSCL_CLASS_OF_BUSINESS_1": [None, None, None],
        "BUSCL_CLASS_OF_BUSINESS_2": [None, None, None],
        "BUSCL_CLASS_OF_BUSINESS_3": [None, None, None],
        "BUSCL_LIMIT_CURRENCY_CD": ["USD", "USD", "USD"],
    }
    
    bordereau_df = pd.DataFrame(test_data)
    
    for idx, row in bordereau_df.iterrows():
        print(f"   - {row['policy_id']}: {row['INSURED_NAME']:15} = {row['exposition']:>12,.0f}")
    
    # 3. Application du programme
    print("\n3. Application du programme...")
    calculation_date = "2024-06-01"  # Date de calcul au milieu de la période de couverture
    bordereau_with_net, results_df = apply_program_to_bordereau(
        bordereau_df, program, calculation_date=calculation_date
    )
    print(f"   Date de calcul: {calculation_date}")
    
    # 4. Affichage des résultats
    print("\n" + "=" * 80)
    print("RÉSULTATS DÉTAILLÉS")
    print("=" * 80)
    
    for idx, row in results_df.iterrows():
        policy_id = bordereau_df.loc[idx, "policy_id"]
        insured = row["INSURED_NAME"]
        exposure = row["exposure"]
        cession_layer = row["cession_to_layer_100pct"]
        cession_reinsurer = row["cession_to_reinsurer"]
        retained = row["retained_by_cedant"]
        
        print(f"\n{policy_id} - {insured}")
        print(f"  Exposition brute:      {exposure:>12,.0f}")
        print(f"  Cession (100%):        {cession_layer:>12,.2f}")
        print(f"  Cession réassureur:    {cession_reinsurer:>12,.2f}")
        print(f"  Retenu par cédant:     {retained:>12,.2f}")
        
        # Détail des structures
        structures_detail = row["structures_detail"]
        if structures_detail:
            print(f"  Structures appliquées: {len([s for s in structures_detail if s['applied']])}")
            for structure in structures_detail:
                if structure["applied"]:
                    print(f"    - {structure['structure_name']:12}: "
                          f"Input={structure['input_exposure']:>12,.2f}, "
                          f"Cession={structure['cession_to_reinsurer']:>12,.2f}")
                    
                    # Afficher le rescaling si présent
                    rescaling = structure.get('rescaling_info')
                    if rescaling and rescaling.get('retention_factor'):
                        print(f"      └─ Rescaling factor: {rescaling['retention_factor']:.1%}")
                        if rescaling.get('original_attachment') is not None:
                            print(f"         Attachment: {rescaling['original_attachment']:,.0f} "
                                  f"→ {rescaling['rescaled_attachment']:,.0f}")
                        if rescaling.get('original_limit') is not None:
                            print(f"         Limit: {rescaling['original_limit']:,.0f} "
                                  f"→ {rescaling['rescaled_limit']:,.0f}")
    
    # 5. Résumé global
    print("\n" + "=" * 80)
    print("RÉSUMÉ GLOBAL")
    print("=" * 80)
    
    total_exposure = results_df["exposure"].sum()
    total_cession_layer = results_df["cession_to_layer_100pct"].sum()
    total_cession_reinsurer = results_df["cession_to_reinsurer"].sum()
    total_retained = results_df["retained_by_cedant"].sum()
    
    print(f"\nExposition totale:     {total_exposure:>12,.0f}")
    print(f"Cession totale (100%): {total_cession_layer:>12,.2f}")
    print(f"Cession réassureur:    {total_cession_reinsurer:>12,.2f}")
    print(f"Retenu total:          {total_retained:>12,.2f}")
    print(f"\nVérification: {total_exposure:,.0f} = {total_cession_layer:,.2f} + {total_retained:,.2f}")
    
    # 6. ASSERTIONS PRÉCISES
    print("\n" + "=" * 80)
    print("VÉRIFICATIONS (ASSERTIONS)")
    print("=" * 80)
    
    # Policy A (50M)
    print("\n✓ Policy A (50M):")
    result_a = results_df.iloc[0]
    
    # QS: 50M * 30% = 15M, retenu = 35M
    # XL sur 35M: attachment rescalé = 20M * 70% = 14M, limit = 35M
    # Cession XL = min(35M - 14M, 35M) = 21M
    # Total cession = 15M + 21M = 36M
    
    expected_cession_a = 36_000_000
    tolerance = 100  # 100$ de tolerance pour les arrondis
    
    assert abs(result_a["cession_to_layer_100pct"] - expected_cession_a) < tolerance, \
        f"Policy A: Expected cession {expected_cession_a:,.0f}, got {result_a['cession_to_layer_100pct']:,.2f}"
    print(f"  Cession attendue: {expected_cession_a:>12,.0f} ✓")
    print(f"  Cession calculée: {result_a['cession_to_layer_100pct']:>12,.2f} ✓")
    
    # Policy B (100M)
    print("\n✓ Policy B (100M):")
    result_b = results_df.iloc[1]
    
    # QS: 100M * 30% = 30M, retenu = 70M
    # XL sur 70M: cession = min(70M - 14M, 35M) = 35M
    # Total cession = 30M + 35M = 65M
    
    expected_cession_b = 65_000_000
    
    assert abs(result_b["cession_to_layer_100pct"] - expected_cession_b) < tolerance, \
        f"Policy B: Expected cession {expected_cession_b:,.0f}, got {result_b['cession_to_layer_100pct']:,.2f}"
    print(f"  Cession attendue: {expected_cession_b:>12,.0f} ✓")
    print(f"  Cession calculée: {result_b['cession_to_layer_100pct']:>12,.2f} ✓")
    
    # Policy C (150M)
    print("\n✓ Policy C (150M):")
    result_c = results_df.iloc[2]
    
    # QS: 150M * 30% = 45M, retenu = 105M
    # XL sur 105M: cession = min(105M - 14M, 35M) = 35M
    # Total cession = 45M + 35M = 80M
    
    expected_cession_c = 80_000_000
    
    assert abs(result_c["cession_to_layer_100pct"] - expected_cession_c) < tolerance, \
        f"Policy C: Expected cession {expected_cession_c:,.0f}, got {result_c['cession_to_layer_100pct']:,.2f}"
    print(f"  Cession attendue: {expected_cession_c:>12,.0f} ✓")
    print(f"  Cession calculée: {result_c['cession_to_layer_100pct']:>12,.2f} ✓")
    
    # Vérification du total
    print("\n✓ Total global:")
    expected_total = expected_cession_a + expected_cession_b + expected_cession_c
    assert abs(total_cession_layer - expected_total) < tolerance * 3, \
        f"Total: Expected {expected_total:,.0f}, got {total_cession_layer:,.2f}"
    print(f"  Total attendu: {expected_total:>12,.0f} ✓")
    print(f"  Total calculé: {total_cession_layer:>12,.2f} ✓")
    
    # Vérification de la conservation de l'exposition
    print("\n✓ Conservation de l'exposition:")
    for idx in range(len(results_df)):
        result = results_df.iloc[idx]
        exposure = result["exposure"]
        cession = result["cession_to_layer_100pct"]
        retained = result["retained_by_cedant"]
        
        assert abs(exposure - (cession + retained)) < tolerance, \
            f"Policy {idx}: Exposure {exposure} != Cession {cession} + Retained {retained}"
    print(f"  Toutes les polices: Exposition = Cession + Retenu ✓")
    
    print("\n" + "=" * 80)
    print("✅ TEST RÉUSSI - Tous les calculs sont corrects !")
    print("=" * 80)


if __name__ == "__main__":
    test_quota_share_then_excess_of_loss_with_rescaling()

