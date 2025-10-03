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
    print(f"🔄 Mode d'exécution: ORDRE-BASED (nouvelle logique)")
    print("   → Les structures s'appliquent selon leur ordre défini")
    print("   → Quote Share réduit l'exposition restante")
    print("   → Excess of Loss s'applique sur l'exposition restante (empilés)")
    
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
        print(f"   📦 Type de produit: {structure['type_of_participation']}")
        print(f"   📋 Ordre d'exécution: {structure['contract_order']}")
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
    if pd.notna(section.get('cession_PCT')):
        print(f"{indent}💰 Taux de cession: {section['cession_PCT']:.1%}")
    
    if pd.notna(section.get('attachment_point_100')) and pd.notna(section.get('limit_occurrence_100')):
        print(f"{indent}🛡️  Excess of Loss: {section['limit_occurrence_100']:,.0f} xs {section['attachment_point_100']:,.0f}")
    
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
    print(f"📋 {program['name']} (ordre-based) - {len(program['structures'])} structures")
    
    for structure in program['structures']:
        type_of_participation = structure['type_of_participation']
        sections_count = len(structure['sections'])
        
        if type_of_participation == 'quote_share':
            # Afficher les taux de cession
            rates = []
            for section in structure['sections']:
                if pd.notna(section.get('cession_PCT')):
                    rates.append(f"{section['cession_PCT']:.1%}")
            rates_str = ", ".join(set(rates)) if rates else "N/A"
            print(f"   🔧 {structure['structure_name']}: QS {rates_str}")
            
        elif type_of_participation == 'excess_of_loss':
            # Afficher les paramètres XOL
            xol_params = []
            for section in structure['sections']:
                if pd.notna(section.get('attachment_point_100')) and pd.notna(section.get('limit_occurrence_100')):
                    xol_params.append(f"{section['limit_occurrence_100']:,.0f}xs{section['attachment_point_100']:,.0f}")
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
