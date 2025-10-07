from typing import Dict, Any
import pandas as pd
import sys


def write_program_config(program: Dict[str, Any], file=None) -> None:
    if file is None:
        file = sys.stdout
    
    file.write("=" * 80 + "\n")
    file.write("PROGRAM CONFIGURATION\n")
    file.write("=" * 80 + "\n")
    
    file.write(f"Program name: {program['name']}\n")
    file.write(f"Number of structures: {len(program['structures'])}\n")
    file.write(f"Matching dimensions: {len(program['dimension_columns'])}\n")
    
    if program['dimension_columns']:
        file.write(f"   Dimensions: {', '.join(program['dimension_columns'])}\n")
    else:
        file.write("   No dimensions (all policies treated the same way)\n")
    
    file.write("\n" + "-" * 80 + "\n")
    file.write("STRUCTURE DETAILS\n")
    file.write("-" * 80 + "\n")
    
    for i, structure in enumerate(program['structures'], 1):
        file.write(f"\nStructure {i}: {structure['structure_name']}\n")
        file.write(f"   Type: {structure['type_of_participation']}\n")
        file.write(f"   Execution order: {structure['contract_order']}\n")
        file.write(f"   Number of sections: {len(structure['sections'])}\n")
        
        if structure.get('claim_basis') and pd.notna(structure.get('claim_basis')):
            file.write(f"   Claim basis: {structure['claim_basis']}\n")
        if structure.get('inception_date') and pd.notna(structure.get('inception_date')):
            file.write(f"   Inception date: {structure['inception_date']}\n")
        if structure.get('expiry_date') and pd.notna(structure.get('expiry_date')):
            file.write(f"   Expiry date: {structure['expiry_date']}\n")
        
        if len(structure['sections']) == 1:
            section = structure['sections'][0]
            file.write("   Single section:\n")
            _write_section(section, program['dimension_columns'], structure['type_of_participation'], indent="      ", file=file)
        else:
            file.write("   Sections:\n")
            for j, section in enumerate(structure['sections'], 1):
                file.write(f"      Section {j}:\n")
                _write_section(section, program['dimension_columns'], structure['type_of_participation'], indent="         ", file=file)
    
    file.write("\n" + "=" * 80 + "\n")


def display_program(program: Dict[str, Any]) -> None:
    write_program_config(program, file=sys.stdout)


def _write_section(section: Dict[str, Any], dimension_columns: list, type_of_participation: str, indent: str = "", file=None) -> None:
    if file is None:
        file = sys.stdout
    
    if type_of_participation == "quota_share":
        if pd.notna(section.get('CESSION_PCT')):
            cession_pct = section['CESSION_PCT']
            file.write(f"{indent}Cession rate: {cession_pct:.1%} ({cession_pct * 100:.1f}%)\n")
        
        if pd.notna(section.get('LIMIT_OCCURRENCE_100')):
            file.write(f"{indent}Limit: {section['LIMIT_OCCURRENCE_100']:,.2f}M\n")
    
    elif type_of_participation == "excess_of_loss":
        if pd.notna(section.get('ATTACHMENT_POINT_100')) and pd.notna(section.get('LIMIT_OCCURRENCE_100')):
            attachment = section['ATTACHMENT_POINT_100']
            limit = section['LIMIT_OCCURRENCE_100']
            file.write(f"{indent}Coverage: {limit:,.2f}M xs {attachment:,.2f}M\n")
            file.write(f"{indent}Range: {attachment:,.2f}M to {attachment + limit:,.2f}M\n")
    
    if pd.notna(section.get('SIGNED_SHARE_PCT')):
        reinsurer_share = section['SIGNED_SHARE_PCT']
        file.write(f"{indent}Reinsurer share: {reinsurer_share:.2%} ({reinsurer_share * 100:.2f}%)\n")
    
    conditions = []
    for dim in dimension_columns:
        value = section.get(dim)
        if pd.notna(value):
            conditions.append(f"{dim}={value}")
    
    if conditions:
        file.write(f"{indent}Matching conditions: {', '.join(conditions)}\n")
    else:
        file.write(f"{indent}Matching conditions: None (applies to all policies)\n")


def display_program_summary(program: Dict[str, Any]) -> None:
    print(f"{program['name']} - {len(program['structures'])} structures")
    
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
