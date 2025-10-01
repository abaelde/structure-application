import pandas as pd
from structures import ProgramLoader, apply_program_to_bordereau


def main():
    print("=== Reinsurance Program Application System ===\n")
    
    bordereau_df = pd.read_csv("bordereau_exemple.csv")
    print("Bordereau loaded:")
    print(bordereau_df)
    print()
    
    loader = ProgramLoader("program_config.xlsx")
    program = loader.get_program()
    
    print(f"Program: {program['name']}")
    print(f"Mode: {program['mode']}")
    print(f"Number of structures: {len(program['structures'])}\n")
    
    print("=" * 80)
    print(f"Applying program: {program['name']} ({program['mode']} mode)")
    print("=" * 80)
    
    print("\nStructures in program:")
    for i, struct in enumerate(program['structures'], 1):
        print(f"  {i}. {struct['structure_name']} ({struct['product_type']})")
        if struct['conditions']:
            conditions_str = ', '.join([f"{c['dimension']}={c['value']}" for c in struct['conditions']])
            print(f"     Conditions: {conditions_str}")
        else:
            print(f"     Conditions: None (applies to all)")
    
    results = apply_program_to_bordereau(bordereau_df, program)
    
    print("\n\nResults Summary:")
    print(results[["policy_number", "exposure", "ceded", "retained"]])
    
    print("\n\nDetailed breakdown by policy:")
    for _, row in results.iterrows():
        print(f"\n{'=' * 80}")
        print(f"Policy: {row['policy_number']}")
        print(f"Total exposure: {row['exposure']:,.2f}")
        print(f"Total ceded: {row['ceded']:,.2f}")
        print(f"Total retained: {row['retained']:,.2f}")
        print(f"\nStructures applied:")
        
        for struct in row["structures_detail"]:
            status = "✓ Applied" if struct.get('applied', False) else "✗ Not applied"
            print(f"  {status} - {struct['structure_name']} ({struct['product_type']})")
            print(f"    Input exposure: {struct['input_exposure']:,.2f}")
            print(f"    Ceded: {struct['ceded']:,.2f}")


if __name__ == "__main__":
    main()
