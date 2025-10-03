import pandas as pd
from structures import ProgramLoader, apply_program_to_bordereau
from structures.program_display import display_program


def format_section_conditions(section, dimension_columns):
    conditions = []
    for dim in dimension_columns:
        value = section.get(dim)
        if pd.notna(value):
            conditions.append(f"{dim}={value}")
    return ", ".join(conditions) if conditions else "All (no conditions)"


def main():
    print("=== Reinsurance Program Application System ===\n")
    
    bordereau_df = pd.read_csv("bordereau_exemple.csv")
    print("Bordereau loaded:")
    print(bordereau_df)
    print()
    
    loader = ProgramLoader("program_config.xlsx")
    program = loader.get_program()
    dimension_columns = program['dimension_columns']
    
    # Afficher la configuration du programme de manière user-friendly
    display_program(program)
    
    results = apply_program_to_bordereau(bordereau_df, program)
    
    print("\n\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print(results[["policy_number", "exposure", "ceded", "retained"]])
    
    print("\n\n" + "=" * 80)
    print("DETAILED BREAKDOWN BY POLICY")
    print("=" * 80)
    
    for _, row in results.iterrows():
        print(f"\n{'─' * 80}")
        print(f"Policy: {row['policy_number']}")
        print(f"Total exposure: {row['exposure']:,.2f}")
        print(f"Total ceded: {row['ceded']:,.2f}")
        print(f"Total retained: {row['retained']:,.2f}")
        print(f"\nStructures applied:")
        
        for struct in row["structures_detail"]:
            status = "✓ Applied" if struct.get('applied', False) else "✗ Not applied"
            print(f"\n  {status} - {struct['structure_name']} ({struct['type_of_participation']})")
            print(f"    Input exposure: {struct['input_exposure']:,.2f}")
            print(f"    Ceded: {struct['ceded']:,.2f}")
            
            if struct.get('section'):
                section = struct['section']
                conditions_str = format_section_conditions(section, dimension_columns)
                print(f"    Section matched: {conditions_str}")


if __name__ == "__main__":
    main()
