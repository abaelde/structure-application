"""
Module pour afficher les programmes de réassurance de manière user-friendly
"""

from typing import Dict, Any
import pandas as pd


def display_program(program: Dict[str, Any]) -> None:
    """
    Affiche un programme de réassurance de manière lisible et user-friendly
    
    Args:
        program: Dictionnaire contenant la configuration du programme
    """
    print("=" * 80)
    print("CONFIGURATION DU PROGRAMME")
    print("=" * 80)
    
    # Informations générales du programme
    print(f"📋 Nom du programme: {program['name']}")
    print(f"🔄 Mode d'exécution: {program['mode'].upper()}")
    
    if program['mode'] == 'sequential':
        print("   → Les structures s'appliquent en séquence (output → input)")
    else:
        print("   → Toutes les structures s'appliquent en parallèle sur l'exposition originale")
    
    print(f"📊 Nombre de structures: {len(program['structures'])}")
    print(f"🎯 Dimensions de matching: {len(program['dimension_columns'])}")
    
    if program['dimension_columns']:
        print(f"   Dimensions: {', '.join(program['dimension_columns'])}")
    else:
        print("   Aucune dimension (toutes les polices traitées de la même façon)")
    
    print("\n" + "-" * 80)
    print("STRUCTURES DÉTAILLÉES")
    print("-" * 80)
    
    # Affichage des structures
    for i, structure in enumerate(program['structures'], 1):
        print(f"\n🔧 Structure {i}: {structure['structure_name']}")
        print(f"   📦 Type de produit: {structure['product_type']}")
        print(f"   📋 Ordre d'exécution: {structure['order']}")
        print(f"   📄 Nombre de sections: {len(structure['sections'])}")
        
        # Affichage des sections
        if len(structure['sections']) == 1:
            section = structure['sections'][0]
            print("   📝 Section unique:")
            _display_section(section, program['dimension_columns'], indent="      ")
        else:
            print("   📝 Sections:")
            for j, section in enumerate(structure['sections'], 1):
                print(f"      Section {j}:")
                _display_section(section, program['dimension_columns'], indent="         ")
    
    print("\n" + "=" * 80)


def _display_section(section: Dict[str, Any], dimension_columns: list, indent: str = "") -> None:
    """
    Affiche une section individuelle
    
    Args:
        section: Dictionnaire contenant les données de la section
        dimension_columns: Liste des colonnes de dimensions
        indent: Indentation pour l'affichage
    """
    # Paramètres du produit
    if pd.notna(section.get('session_rate')):
        print(f"{indent}💰 Taux de cession: {section['session_rate']:.1%}")
    
    if pd.notna(section.get('priority')) and pd.notna(section.get('limit')):
        print(f"{indent}🛡️  Excess of Loss: {section['limit']:,.0f} xs {section['priority']:,.0f}")
    
    # Conditions de matching
    conditions = []
    for dim in dimension_columns:
        value = section.get(dim)
        if pd.notna(value):
            conditions.append(f"{dim}={value}")
    
    if conditions:
        print(f"{indent}🎯 Conditions: {', '.join(conditions)}")
    else:
        print(f"{indent}🎯 Conditions: Aucune (s'applique à toutes les polices)")


def display_program_summary(program: Dict[str, Any]) -> None:
    """
    Affiche un résumé compact du programme
    
    Args:
        program: Dictionnaire contenant la configuration du programme
    """
    print(f"📋 {program['name']} ({program['mode']}) - {len(program['structures'])} structures")
    
    for structure in program['structures']:
        product_type = structure['product_type']
        sections_count = len(structure['sections'])
        
        if product_type == 'quote_share':
            # Afficher les taux de cession
            rates = []
            for section in structure['sections']:
                if pd.notna(section.get('session_rate')):
                    rates.append(f"{section['session_rate']:.1%}")
            rates_str = ", ".join(set(rates)) if rates else "N/A"
            print(f"   🔧 {structure['structure_name']}: QS {rates_str}")
            
        elif product_type == 'excess_of_loss':
            # Afficher les paramètres XOL
            xol_params = []
            for section in structure['sections']:
                if pd.notna(section.get('priority')) and pd.notna(section.get('limit')):
                    xol_params.append(f"{section['limit']:,.0f}xs{section['priority']:,.0f}")
            xol_str = ", ".join(set(xol_params)) if xol_params else "N/A"
            print(f"   🔧 {structure['structure_name']}: XOL {xol_str}")


def display_program_comparison(programs: Dict[str, Dict[str, Any]]) -> None:
    """
    Affiche une comparaison de plusieurs programmes
    
    Args:
        programs: Dictionnaire {nom: programme}
    """
    print("=" * 80)
    print("COMPARAISON DES PROGRAMMES")
    print("=" * 80)
    
    for name, program in programs.items():
        print(f"\n📋 {name}:")
        display_program_summary(program)
    
    print("\n" + "=" * 80)
