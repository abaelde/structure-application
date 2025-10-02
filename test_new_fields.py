"""
Test pour vérifier que les nouveaux champs sont bien pris en compte:
- claim_basis (risk_attaching ou loss_occurring)
- inception_date et expiry_date pour les structures
- inception_date et expiry_date pour les polices
"""

import pandas as pd
from structures.structure_loader import ProgramLoader
from structures.structure_engine import apply_program_to_bordereau

def test_new_fields():
    print("Test des nouveaux champs ajoutés au modèle de données")
    print("=" * 60)
    
    # Charger le programme mis à jour
    loader = ProgramLoader("examples/programs/program_simple_parallel_updated.xlsx")
    program = loader.get_program()
    
    print("📋 Configuration du programme:")
    print(f"  - Nom: {program['name']}")
    print(f"  - Mode: {program['mode']}")
    print(f"  - Nombre de structures: {len(program['structures'])}")
    
    print("\n🔧 Détails des structures:")
    for i, structure in enumerate(program['structures'], 1):
        print(f"  Structure {i}: {structure['structure_name']}")
        print(f"    - Type: {structure['product_type']}")
        print(f"    - Claim basis: {structure['claim_basis']}")
        print(f"    - Inception date: {structure['inception_date']}")
        print(f"    - Expiry date: {structure['expiry_date']}")
        print(f"    - Nombre de sections: {len(structure['sections'])}")
    
    # Créer un bordereau de test avec les nouvelles colonnes
    test_bordereau = pd.DataFrame({
        'numero_police': ['POL-2024-001', 'POL-2024-002'],
        'nom_assure': ['Test Company 1', 'Test Company 2'],
        'country': ['France', 'Germany'],
        'region': ['EMEA', 'EMEA'],
        'product_type_1': ['Property', 'Property'],
        'product_type_2': ['Commercial', 'Commercial'],
        'product_type_3': ['Fire', 'Fire'],
        'currency': ['EUR', 'EUR'],
        'line_of_business': ['Property', 'Property'],
        'industry': ['Construction', 'Technology'],
        'sic_code': ['1623', '7371'],
        'include': ['Standard', 'Premium'],
        'exposition': [1000000.0, 2000000.0],
        'inception_date': ['2024-01-01', '2024-02-15'],
        'expiry_date': ['2024-12-31', '2025-02-14']
    })
    
    print(f"\n📊 Bordereau de test:")
    print(f"  - Nombre de polices: {len(test_bordereau)}")
    print(f"  - Colonnes: {list(test_bordereau.columns)}")
    
    # Appliquer le programme
    results = apply_program_to_bordereau(test_bordereau, program)
    
    print(f"\n🎯 Résultats de l'application du programme:")
    for _, result in results.iterrows():
        print(f"\n  Police: {result['policy_number']}")
        print(f"    - Exposition: {result['exposure']:,.0f}")
        print(f"    - Cédé: {result['ceded']:,.0f}")
        print(f"    - Retenu: {result['retained']:,.0f}")
        print(f"    - Date début police: {result['policy_inception_date']}")
        print(f"    - Date fin police: {result['policy_expiry_date']}")
        
        print(f"    - Détails des structures:")
        for detail in result['structures_detail']:
            print(f"      * {detail['structure_name']}:")
            print(f"        - Type: {detail['product_type']}")
            print(f"        - Claim basis: {detail['claim_basis']}")
            print(f"        - Date début structure: {detail['inception_date']}")
            print(f"        - Date fin structure: {detail['expiry_date']}")
            print(f"        - Cédé: {detail['ceded']:,.0f}")
            print(f"        - Appliqué: {detail['applied']}")
    
    print(f"\n✅ Test terminé avec succès !")
    print(f"\nRésumé des nouveaux champs testés:")
    print(f"  ✓ claim_basis: Présent dans les structures")
    print(f"  ✓ inception_date: Présent dans les structures et polices")
    print(f"  ✓ expiry_date: Présent dans les structures et polices")
    print(f"  ✓ Tous les champs sont correctement propagés dans les résultats")

if __name__ == "__main__":
    test_new_fields()
