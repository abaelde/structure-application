"""
Démonstration consolidée de tous les programmes de réassurance

Ce fichier regroupe tous les programmes définis dans les différents fichiers
de création pour permettre une observation centralisée avec describe().

Programmes inclus:
1. Aviation AXA XL - Programme multi-devises complexe
2. Aviation Hull/Liability Split - Filtrage Hull/Liability
3. Casualty AIG - Programme avec conditions spécifiques
4. Aviation Old Republic - Programme XOL simple
5. Quota Share avec condition France - Programme avec condition pays
6. Single Quota Share - Programme simple
7. New Line - Programme casualty multi-dimensions
8. Quota Share avec exclusions - Programme avec exclusions globales
9. Test Exclusions - Programme de test des exclusions multi-valeurs
"""

# =============================================================================
# CONFIGURATION
# =============================================================================
# Flag pour activer/désactiver la sauvegarde en Snowflake
SAVE_TO_SNOWFLAKE = True  # Changez à True pour sauvegarder en Snowflake

# Ce script peut soit afficher les programmes seulement (SAVE_TO_SNOWFLAKE = False)
# soit permettre de sélectionner et sauvegarder un programme en Snowflake (SAVE_TO_SNOWFLAKE = True)

# =============================================================================
# IMPORTS
# =============================================================================

import sys
import os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.builders import build_quota_share, build_excess_of_loss, build_program
from src.domain.exclusion import ExclusionRule

# Import pour la sauvegarde Snowflake (seulement si activé)
if SAVE_TO_SNOWFLAKE:
    from snowflake_utils import save_program

print("=" * 80)
print("DÉMONSTRATION CONSOLIDÉE DE TOUS LES PROGRAMMES")
print("=" * 80)
if SAVE_TO_SNOWFLAKE:
    print("Mode: Sauvegarde en Snowflake activée")
    print("Vous pourrez sélectionner un programme à sauvegarder après l'affichage des descriptions.")
else:
    print("Mode: Affichage seulement (sauvegarde désactivée)")
    print("Ce script affiche les descriptions des programmes pour vérifier le builder")
print()

# =============================================================================
# 1. AVIATION AXA XL - Programme Multi-Devises Complexe
# =============================================================================

def create_aviation_axa_xl():
    """Programme aviation avec 1 structure Quota Share + 6 layers excess of loss, chacun défini pour 5 devises"""
    
    print("1. Création du programme Aviation AXA XL...")
    
    LAYER_VALUES_COMMON = {
        "XOL_1": (65_000_000, 35_000_000),
        "XOL_2": (50_000_000, 65_000_000),
        "XOL_3": (100_000_000, 115_000_000),
        "XOL_4": (100_000_000, 215_000_000),
        "XOL_5": (100_000_000, 315_000_000),
        "XOL_6": (150_000_000, 415_000_000),
    }

    LAYER_VALUES_GBP = {
        "XOL_1": (43_333_333, 23_333_333),
        "XOL_2": (33_333_333, 43_333_333),
        "XOL_3": (66_666_666, 76_666_666),
        "XOL_4": (66_666_666, 143_333_333),
        "XOL_5": (66_666_666, 210_000_000),
        "XOL_6": (100_000_000, 276_666_666),
    }

    CURRENCIES_COMMON = ["USD", "CAD", "EUR", "AUD"]
    CURRENCIES_GBP = ["GBP"]

    # Construction du Quota Share
    qs = build_quota_share(
        name="QS_1",
        cession_pct=0.25,
        signed_share=0.0165,
        special_conditions=[
            {
                "ORIGINAL_CURRENCY": CURRENCIES_COMMON + CURRENCIES_GBP,
                "INCLUDES_HULL": True,
                "INCLUDES_LIABILITY": True,
            }
        ],
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )

    # Construction des layers XOL
    xol_layers = []
    for i, (layer_name, (limit_common, priority_common)) in enumerate(
        LAYER_VALUES_COMMON.items(), 1
    ):
        limit_gbp, priority_gbp = LAYER_VALUES_GBP[layer_name]

        special_conditions = []

        # Condition pour USD, CAD, EUR, AUD (valeurs communes)
        special_conditions.append(
            {
                "ORIGINAL_CURRENCY": CURRENCIES_COMMON,
                "INCLUDES_HULL": True,
                "INCLUDES_LIABILITY": True,
            }
        )

        # Condition pour GBP (avec valeurs spécifiques)
        special_conditions.append(
            {
                "ORIGINAL_CURRENCY": CURRENCIES_GBP,
                "ATTACHMENT_POINT_100": priority_gbp,
                "LIMIT_100": limit_gbp,
                "INCLUDES_HULL": True,
                "INCLUDES_LIABILITY": True,
            }
        )

        xol = build_excess_of_loss(
            name=layer_name,
            attachment=priority_common,
            limit=limit_common,
            signed_share=0.05,
            special_conditions=special_conditions,
            claim_basis="risk_attaching",
            inception_date="2024-01-01",
            expiry_date="2025-01-01",
            predecessor_title="QS_1",
        )
        xol_layers.append(xol)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    program_name = f"AVIATION_AXA_XL_2024_{timestamp}"

    program = build_program(
        name=program_name,
        structures=[qs] + xol_layers,
        main_currency="EUR", 
        underwriting_department="aviation",
    )
    
    return program

# =============================================================================
# 2. AVIATION HULL/LIABILITY SPLIT - Filtrage Hull/Liability
# =============================================================================

def create_aviation_hull_liability_split():
    """Programme aviation avec séparation Hull/Liability"""
    
    print("2. Création du programme Aviation Hull/Liability Split...")
    
    qs_all = build_quota_share(
        name="QS_ALL",
        cession_pct=0.25,
        signed_share=0.0165,
        special_conditions=[
            {
                "INCLUDES_HULL": True,
                "INCLUDES_LIABILITY": True,
            }
        ],
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )

    xol_hull = build_excess_of_loss(
        name="XOL_HULL",
        attachment=5_000_000,
        limit=10_000_000,
        signed_share=0.05,
        special_conditions=[
            {
                "INCLUDES_HULL": True,
                "INCLUDES_LIABILITY": False,
            }
        ],
        predecessor_title="QS_ALL",
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )

    xol_liability = build_excess_of_loss(
        name="XOL_LIABILITY",
        attachment=10_000_000,
        limit=40_000_000,
        signed_share=0.05,
        special_conditions=[
            {
                "INCLUDES_HULL": False,
                "INCLUDES_LIABILITY": True,
            }
        ],
        predecessor_title="QS_ALL",
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    program_name = f"AVIATION_HULL_LIABILITY_SPLIT_{timestamp}"

    program = build_program(
        name=program_name,
        structures=[qs_all, xol_hull, xol_liability],
        main_currency="EUR", 
        underwriting_department="aviation",
    )
    
    return program

# =============================================================================
# 3. CASUALTY AIG - Programme avec conditions spécifiques
# =============================================================================

def create_casualty_aig():
    """Programme casualty avec 1 structure Quota Share avec 2 conditions"""
    
    print("3. Création du programme Casualty AIG...")
    
    qs = build_quota_share(
        name="QS_1",
        cession_pct=1.0,
        signed_share=0.10,
        special_conditions=[
            {
                "limit": 10_000_000,
                "PRODUCT_TYPE_LEVEL_1": ["Cyber"],
            },
        ],
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    program_name = f"CASUALTY_AIG_2024_{timestamp}"

    program = build_program(
        name=program_name, 
        structures=[qs], 
        main_currency="EUR", 
        underwriting_department="casualty"
    )
    
    return program

# =============================================================================
# 4. AVIATION OLD REPUBLIC - Programme XOL simple
# =============================================================================

def create_aviation_old_republic():
    """Programme aviation avec 3 structures excess of loss"""
    
    print("4. Création du programme Aviation Old Republic...")
    
    REINSURER_SHARE_VALUES = {
        "XOL_1": 0.1,
        "XOL_2": 0.1,
        "XOL_3": 0.0979,
    }

    xol_1 = build_excess_of_loss(
        name="XOL_1",
        attachment=3_000_000,
        limit=8_750_000,
        signed_share=REINSURER_SHARE_VALUES["XOL_1"],
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )

    xol_2 = build_excess_of_loss(
        name="XOL_2",
        attachment=11_750_000,
        limit=10_000_000,
        signed_share=REINSURER_SHARE_VALUES["XOL_2"],
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )

    xol_3 = build_excess_of_loss(
        name="XOL_3",
        attachment=21_750_000,
        limit=23_250_000,
        signed_share=REINSURER_SHARE_VALUES["XOL_3"],
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    program_name = f"AVIATION_OLD_REPUBLIC_2024_{timestamp}"

    program = build_program(
        name=program_name,
        structures=[xol_1, xol_2, xol_3],
        main_currency="EUR", 
        underwriting_department="aviation",
    )
    
    return program

# =============================================================================
# 5. QUOTA SHARE AVEC CONDITION FRANCE - Programme avec condition pays
# =============================================================================

def create_quota_share_with_france_condition():
    """Programme avec quota share et condition spécifique pour la France"""
    
    print("5. Création du programme Quota Share avec condition France...")
    
    qs = build_quota_share(
        name="QS_30_with_France_50",
        cession_pct=0.30,
        signed_share=1.0,
        special_conditions=[
            {
                "COUNTRIES": ["France"],
                "cession_pct": 0.50,
            }
        ],
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    program_name = f"QUOTA_SHARE_WITH_FRANCE_CONDITION_{timestamp}"

    program = build_program(
        name=program_name, 
        structures=[qs], 
        main_currency="EUR", 
        underwriting_department="test"
    )
    
    return program

# =============================================================================
# 6. SINGLE QUOTA SHARE - Programme simple
# =============================================================================

def create_single_quota_share():
    """Programme simple avec quota share"""
    
    print("6. Création du programme Single Quota Share...")
    
    qs = build_quota_share(
        name="QS_30",
        cession_pct=0.30,
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    program_name = f"SINGLE_QUOTA_SHARE_2024_{timestamp}"

    program = build_program(
        name=program_name, 
        structures=[qs], 
        main_currency="EUR",
        underwriting_department="test"
    )
    
    return program

# =============================================================================
# 7. NEW LINE - Programme casualty multi-dimensions
# =============================================================================

def create_new_line():
    """Programme casualty avec 3 layers Excess of Loss et dimensions multiples"""
    
    print("7. Création du programme New Line...")
    
    CURRENCIES = ["GBP", "USD", "EUR", "CAD", "AUD"]
    REINSURER_SHARE = 0.10

    # Layer 1 - Sub-condition A (Financial Institutions, etc.)
    LAYER_1_SUB_A = {
        "GBP": (3_000_000, 1_000_000),
        "USD": (4_500_000, 1_500_000),
        "EUR": (4_500_000, 1_500_000),
        "CAD": (5_250_000, 1_750_000),
        "AUD": (8_000_000, 2_000_000),
    }

    # Layer 1 - Sub-condition B (Employers' Liability, General Liability)
    LAYER_1_SUB_B = {
        "GBP": (2_500_000, 1_500_000),
        "USD": (3_750_000, 2_250_000),
        "EUR": (3_750_000, 2_250_000),
        "CAD": (4_375_000, 2_625_000),
        "AUD": (7_000_000, 3_000_000),
    }

    LAYER_2_VALUES = {
        "GBP": (6_000_000, 4_000_000),
        "USD": (9_000_000, 6_000_000),
        "EUR": (9_000_000, 6_000_000),
        "CAD": (10_500_000, 7_000_000),
        "AUD": (15_000_000, 10_000_000),
    }

    LAYER_3_VALUES = {
        "GBP": (5_000_000, 10_000_000),
        "USD": (10_000_000, 15_000_000),
        "EUR": (10_000_000, 15_000_000),
        "CAD": (8_750_000, 17_500_000),
        "AUD": (5_000_000, 25_000_000),
    }

    # LOB groupées par liste
    LOB_SUB_A = [
        "Financial Institutions",
        "Commercial Crime",
        "Professional Indemnity / Errors and Omissions",
        "Commercial Directors and Officers",
        "Medical Malpractice",
        "Transactional Liability",
    ]

    LOB_SUB_B = [
        "Employers' Liability",
        "General Liability",
    ]

    # Layer 1 - Sub-condition A (LOB groupées)
    layer_1_sub_a_conditions = []
    for currency in CURRENCIES:
        limit_a, attachment_a = LAYER_1_SUB_A[currency]
        layer_1_sub_a_conditions.append(
            {
                "attachment": attachment_a,
                "limit": limit_a,
                "signed_share": REINSURER_SHARE,
                "ORIGINAL_CURRENCY": [currency],
                "PRODUCT_TYPE_LEVEL_1": LOB_SUB_A,
            }
        )

    # Layer 1 - Sub-condition B (LOB groupées)
    layer_1_sub_b_conditions = []
    for currency in CURRENCIES:
        limit_b, attachment_b = LAYER_1_SUB_B[currency]
        layer_1_sub_b_conditions.append(
            {
                "attachment": attachment_b,
                "limit": limit_b,
                "signed_share": REINSURER_SHARE,
                "ORIGINAL_CURRENCY": [currency],
                "PRODUCT_TYPE_LEVEL_1": LOB_SUB_B,
            }
        )

    # Combiner les deux sous-conditions
    layer_1_conditions = layer_1_sub_a_conditions + layer_1_sub_b_conditions

    layer_1 = build_excess_of_loss(
        name="LAYER_1",
        special_conditions=layer_1_conditions,
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )

    # Layer 2
    layer_2_conditions = []
    for currency in CURRENCIES:
        limit, attachment = LAYER_2_VALUES[currency]
        layer_2_conditions.append(
            {
                "attachment": attachment,
                "limit": limit,
                "signed_share": REINSURER_SHARE,
                "ORIGINAL_CURRENCY": [currency],
            }
        )

    layer_2 = build_excess_of_loss(
        name="LAYER_2",
        special_conditions=layer_2_conditions,
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )

    # Layer 3
    layer_3_conditions = []
    for currency in CURRENCIES:
        limit, attachment = LAYER_3_VALUES[currency]
        layer_3_conditions.append(
            {
                "attachment": attachment,
                "limit": limit,
                "signed_share": REINSURER_SHARE,
                "ORIGINAL_CURRENCY": [currency],
            }
        )

    layer_3 = build_excess_of_loss(
        name="LAYER_3",
        special_conditions=layer_3_conditions,
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    program_name = f"NEW_LINE_2024_{timestamp}"

    program = build_program(
        name=program_name,
        structures=[layer_1, layer_2, layer_3],
        main_currency="EUR", 
        underwriting_department="casualty",
    )
    
    return program

# =============================================================================
# 8. QUOTA SHARE AVEC EXCLUSIONS - Programme avec exclusions globales
# =============================================================================

def create_quota_share_with_exclusions():
    """Programme quota share avec exclusions globales"""
    
    print("8. Création du programme Quota Share avec exclusions...")
    
    qs = build_quota_share(
        name="QS Casualty 25%",
        cession_pct=0.25,
        signed_share=1.0,
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2024-12-31",
    )

    # Créer les exclusions
    exclusions = [
        ExclusionRule(
            values_by_dimension={"COUNTRIES": ["Iran", "Russia"]},
            name="Sanctions Countries",
        ),
    ]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    program_name = f"Quota_Share_with_Exclusions_Test_{timestamp}"

    program = build_program(
        name=program_name,
        structures=[qs],
        main_currency="EUR", 
        underwriting_department="casualty",
        exclusions=exclusions,
    )
    
    return program

# =============================================================================
# 9. TEST EXCLUSIONS - Programme de test des exclusions multi-valeurs
# =============================================================================

def create_test_exclusions():
    """Programme de test avec des exclusions multi-valeurs"""
    
    print("9. Création du programme Test Exclusions...")
    
    qs = build_quota_share(
        name="QS_TEST",
        cession_pct=0.30,
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )

    # Construction des exclusions avec multi-valeurs
    exclusions = [
        # Exclusion 1: Multi-pays
        ExclusionRule(
            name="Cyber_Exclusion",
            values_by_dimension={
                "COUNTRIES": ["US", "CA", "UK", "DE"],
                "PRODUCT_TYPE_LEVEL_1": ["Cyber", "Technology"],
            },
            effective_date="2024-01-01",
            expiry_date="2025-01-01",
        ),
        # Exclusion 2: Multi-régions et multi-produits
        ExclusionRule(
            name="War_Exclusion",
            values_by_dimension={
                "REGION": ["Middle East", "Africa", "Asia"],
                "PRODUCT_TYPE_LEVEL_1": ["War", "Terrorism"],
                "PRODUCT_TYPE_LEVEL_2": ["Marine", "Aviation"],
            },
            effective_date="2024-01-01",
            expiry_date="2025-01-01",
        ),
        # Exclusion 3: Multi-entités
        ExclusionRule(
            name="Entity_Exclusion",
            values_by_dimension={
                "BUSCL_ENTITY_NAME_CED": ["Entity_A", "Entity_B", "Entity_C"],
                "POL_RISK_NAME_CED": ["Risk_1", "Risk_2"],
            },
            effective_date="2024-01-01",
            expiry_date="2025-01-01",
        ),
    ]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    program_name = f"TEST_EXCLUSIONS_2024_{timestamp}"

    program = build_program(
        name=program_name,
        structures=[qs],
        main_currency="EUR", 
        underwriting_department="casualty",
        exclusions=exclusions,
    )
    
    return program

# =============================================================================
# EXÉCUTION PRINCIPALE
# =============================================================================

def main():
    """Fonction principale qui crée tous les programmes et affiche leurs descriptions"""
    
    programs = []
    
    # Créer tous les programmes
    try:
        programs.append(("Aviation AXA XL", create_aviation_axa_xl()))
        programs.append(("Aviation Hull/Liability Split", create_aviation_hull_liability_split()))
        programs.append(("Casualty AIG", create_casualty_aig()))
        programs.append(("Aviation Old Republic", create_aviation_old_republic()))
        programs.append(("Quota Share avec condition France", create_quota_share_with_france_condition()))
        programs.append(("Single Quota Share", create_single_quota_share()))
        programs.append(("New Line", create_new_line()))
        programs.append(("Quota Share avec exclusions", create_quota_share_with_exclusions()))
        programs.append(("Test Exclusions", create_test_exclusions()))
        
        print(f"\n✓ {len(programs)} programmes créés avec succès !")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des programmes: {e}")
        return
    
    # Afficher les descriptions de tous les programmes
    print("\n" + "=" * 80)
    print("DESCRIPTIONS DE TOUS LES PROGRAMMES")
    print("=" * 80)
    
    for i, (name, program) in enumerate(programs, 1):
        print(f"\n{'='*20} PROGRAMME {i}: {name.upper()} {'='*20}")
        print(f"Nom: {program.name}")
        print(f"Département: {program.underwriting_department}")
        print(f"Devise principale: {program.main_currency}")
        print(f"Nombre de structures: {len(program.structures)}")
        if hasattr(program, 'exclusions') and program.exclusions:
            print(f"Nombre d'exclusions: {len(program.exclusions)}")
        print()
        
        # Afficher la description détaillée
        program.describe()
        
        print("\n" + "-" * 80)
    
    # Résumé final
    print(f"\n{'='*20} RÉSUMÉ FINAL {'='*20}")
    print(f"✓ {len(programs)} programmes créés et décrits avec succès !")
    print("\nTous les programmes ont été créés en mémoire et leurs descriptions")
    print("ont été affichées pour vérifier que le builder fonctionne correctement.")
    
    if SAVE_TO_SNOWFLAKE:
        print("\n" + "="*80)
        print("SÉLECTION ET SAUVEGARDE EN SNOWFLAKE")
        print("="*80)
        save_program_to_snowflake(programs)
    else:
        print("\nAucune sauvegarde n'a été effectuée - ce script est uniquement")
        print("destiné à la démonstration et à la vérification des fonctionnalités.")
    
    return programs


def save_program_to_snowflake(programs):
    """Permet de sélectionner et sauvegarder un programme en Snowflake"""
    
    print("\nProgrammes disponibles pour la sauvegarde :")
    print("-" * 50)
    
    for i, (name, program) in enumerate(programs, 1):
        print(f"{i:2d}. {name}")
        print(f"    Nom: {program.name}")
        print(f"    Département: {program.underwriting_department}")
        print(f"    Structures: {len(program.structures)}")
        if hasattr(program, 'exclusions') and program.exclusions:
            print(f"    Exclusions: {len(program.exclusions)}")
        print()
    
    while True:
        try:
            choice = input("Entrez le numéro du programme à sauvegarder (ou 'q' pour quitter): ").strip()
            
            if choice.lower() == 'q':
                print("Sauvegarde annulée.")
                return
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(programs):
                selected_name, selected_program = programs[choice_num - 1]
                break
            else:
                print(f"❌ Veuillez entrer un numéro entre 1 et {len(programs)}")
                
        except ValueError:
            print("❌ Veuillez entrer un numéro valide ou 'q' pour quitter")
    
    print(f"\n✓ Programme sélectionné: {selected_name}")
    print(f"  Nom: {selected_program.name}")
    print(f"  Département: {selected_program.underwriting_department}")
    
    # Confirmation
    confirm = input(f"\nConfirmez-vous la sauvegarde de '{selected_program.name}' en Snowflake ? (y/N): ").strip().lower()
    
    if confirm in ['y', 'yes', 'oui', 'o']:
        try:
            print(f"\n💾 Sauvegarde de '{selected_program.name}' en Snowflake...")
            output_path = save_program(selected_program, "snowflake", selected_program.name)
            print(f"✅ Programme sauvegardé avec succès: {output_path}")
            print(f"✅ Le programme '{selected_program.name}' est maintenant disponible en Snowflake !")
            
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
            print("Le programme a été créé correctement mais la sauvegarde a échoué.")
    else:
        print("Sauvegarde annulée.")





if __name__ == "__main__":
    main()
