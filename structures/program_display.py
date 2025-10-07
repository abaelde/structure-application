from typing import Dict, Any
import pandas as pd


def display_program(program: Dict[str, Any]) -> None:
    print("=" * 80)
    print("PROGRAM CONFIGURATION")
    print("=" * 80)
    
    print(f"Program name: {program['name']}")
    print(f"Execution mode: ORDER-BASED")
    print("   → Structures are applied according to their defined order")
    print("   → Quota Share reduces the remaining exposure")
    print("   → Excess of Loss applies on remaining exposure (stacked)")
    
    print(f"Number of structures: {len(program['structures'])}")
    print(f"Matching dimensions: {len(program['dimension_columns'])}")
    
    if program['dimension_columns']:
        print(f"   Dimensions: {', '.join(program['dimension_columns'])}")
    else:
        print("   No dimensions (all policies treated the same way)")
    
    print("\n" + "-" * 80)
    print("STRUCTURE DETAILS")
    print("-" * 80)
    
    for i, structure in enumerate(program['structures'], 1):
        print(f"\nStructure {i}: {structure['structure_name']}")
        print(f"   Type: {structure['type_of_participation']}")
        print(f"   Execution order: {structure['contract_order']}")
        print(f"   Number of sections: {len(structure['sections'])}")
        
        if structure.get('claim_basis') and pd.notna(structure.get('claim_basis')):
            print(f"   Claim basis: {structure['claim_basis']}")
        if structure.get('inception_date') and pd.notna(structure.get('inception_date')):
            print(f"   Inception date: {structure['inception_date']}")
        if structure.get('expiry_date') and pd.notna(structure.get('expiry_date')):
            print(f"   Expiry date: {structure['expiry_date']}")
        
        if len(structure['sections']) == 1:
            section = structure['sections'][0]
            print("   Single section:")
            _display_section(section, program['dimension_columns'], structure['type_of_participation'], indent="      ")
        else:
            print("   Sections:")
            for j, section in enumerate(structure['sections'], 1):
                print(f"      Section {j}:")
                _display_section(section, program['dimension_columns'], structure['type_of_participation'], indent="         ")
    
    print("\n" + "=" * 80)


def _display_section(section: Dict[str, Any], dimension_columns: list, type_of_participation: str, indent: str = "") -> None:
    if type_of_participation == "quota_share":
        if pd.notna(section.get('CESSION_PCT')):
            cession_pct = section['CESSION_PCT']
            print(f"{indent}Cession rate: {cession_pct:.1%} ({cession_pct * 100:.1f}%)")
        
        if pd.notna(section.get('LIMIT_OCCURRENCE_100')):
            print(f"{indent}Limit: {section['LIMIT_OCCURRENCE_100']:,.2f}M")
    
    elif type_of_participation == "excess_of_loss":
        if pd.notna(section.get('ATTACHMENT_POINT_100')) and pd.notna(section.get('LIMIT_OCCURRENCE_100')):
            attachment = section['ATTACHMENT_POINT_100']
            limit = section['LIMIT_OCCURRENCE_100']
            print(f"{indent}Coverage: {limit:,.2f}M xs {attachment:,.2f}M")
            print(f"{indent}Range: {attachment:,.2f}M to {attachment + limit:,.2f}M")
    
    if pd.notna(section.get('SIGNED_SHARE_PCT')):
        reinsurer_share = section['SIGNED_SHARE_PCT']
        print(f"{indent}Reinsurer share: {reinsurer_share:.2%} ({reinsurer_share * 100:.2f}%)")
    
    conditions = []
    for dim in dimension_columns:
        value = section.get(dim)
        if pd.notna(value):
            conditions.append(f"{dim}={value}")
    
    if conditions:
        print(f"{indent}Matching conditions: {', '.join(conditions)}")
    else:
        print(f"{indent}Matching conditions: None (applies to all policies)")


def display_program_summary(program: Dict[str, Any]) -> None:
    print(f"{program['name']} (order-based) - {len(program['structures'])} structures")
    
    for structure in program['structures']:
        type_of_participation = structure['type_of_participation']
        sections_count = len(structure['sections'])
        
        if type_of_participation == 'quota_share':
            rates = []
            for section in structure['sections']:
                if pd.notna(section.get('CESSION_PCT')):
                    rates.append(f"{section['CESSION_PCT']:.1%}")
            rates_str = ", ".join(set(rates)) if rates else "N/A"
            print(f"   {structure['structure_name']}: QS {rates_str}")
            
        elif type_of_participation == 'excess_of_loss':
            xol_params = []
            for section in structure['sections']:
                if pd.notna(section.get('ATTACHMENT_POINT_100')) and pd.notna(section.get('LIMIT_OCCURRENCE_100')):
                    xol_params.append(f"{section['LIMIT_OCCURRENCE_100']:,.0f}xs{section['ATTACHMENT_POINT_100']:,.0f}")
            xol_str = ", ".join(set(xol_params)) if xol_params else "N/A"
            print(f"   {structure['structure_name']}: XOL {xol_str}")


def display_program_comparison(programs: Dict[str, Dict[str, Any]]) -> None:
    print("=" * 80)
    print("PROGRAM COMPARISON")
    print("=" * 80)
    
    for name, program in programs.items():
        print(f"\n{name}:")
        display_program_summary(program)
    
    print("\n" + "=" * 80)
