import pandas as pd
from structures import ProgramLoader, apply_program_to_bordereau


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
    
    print(f"Program: {program['name']}")
    print(f"Mode: {program['mode']}")
    print(f"Number of structures: {len(program['structures'])}\n")
    
    print("=" * 80)
    print(f"Program structure: {program['name']} ({program['mode']} mode)")
    print("=" * 80)
    
    print("\nStructures and their sections:")
    for i, struct in enumerate(program['structures'], 1):
        print(f"\n{i}. {struct['structure_name']} ({struct['product_type']})")
        print(f"   Sections defined:")
        for j, section in enumerate(struct['sections'], 1):
            conditions_str = format_section_conditions(section, dimension_columns)
            
            params = []
            if pd.notna(section.get('session_rate')):
                params.append(f"rate={section['session_rate']:.0%}")
            if pd.notna(section.get('priority')):
                params.append(f"priority={section['priority']:,.0f}")
            if pd.notna(section.get('limit')):
                params.append(f"limit={section['limit']:,.0f}")
            params_str = ", ".join(params)
            
            print(f"      {j}) {params_str} | Conditions: {conditions_str}")
    
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
            print(f"\n  {status} - {struct['structure_name']} ({struct['product_type']})")
            print(f"    Input exposure: {struct['input_exposure']:,.2f}")
            print(f"    Ceded: {struct['ceded']:,.2f}")
            
            if struct.get('section'):
                section = struct['section']
                conditions_str = format_section_conditions(section, dimension_columns)
                print(f"    Section matched: {conditions_str}")


if __name__ == "__main__":
    main()
