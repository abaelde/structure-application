import pandas as pd
import argparse
import sys
from structures import ProgramLoader, apply_program_to_bordereau, generate_detailed_report
from structures.program_display import display_program


def format_section_conditions(section, dimension_columns):
    conditions = []
    for dim in dimension_columns:
        value = section.get(dim)
        if pd.notna(value):
            conditions.append(f"{dim}={value}")
    return ", ".join(conditions) if conditions else "All (no conditions)"


def main():
    parser = argparse.ArgumentParser(description='Reinsurance Program Application System')
    parser.add_argument('--program', '-p', required=True, help='Path to the program Excel file')
    parser.add_argument('--bordereau', '-b', required=True, help='Path to the bordereau CSV file')
    
    args = parser.parse_args()
    
    print("=== Reinsurance Program Application System ===\n")
    
    try:
        bordereau_df = pd.read_csv(args.bordereau)
        print("Bordereau loaded:")
        print(bordereau_df)
        print()
        
        loader = ProgramLoader(args.program)
        program = loader.get_program()
        dimension_columns = program['dimension_columns']
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading files: {e}")
        sys.exit(1)
    
    # Afficher la configuration du programme de manière user-friendly
    display_program(program)
    
    bordereau_with_net, results = apply_program_to_bordereau(bordereau_df, program)
    
    print("\n\n" + "=" * 80)
    print("BORDEREAU AVEC NET EXPOSURE")
    print("=" * 80)
    print(bordereau_with_net)
    
    print("\n\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print(results[["policy_number", "exposure", "gross_ceded", "net_ceded", "retained"]])
    
    print("\n\n" + "=" * 80)
    print("DETAILED BREAKDOWN BY POLICY")
    print("=" * 80)
    
    for _, row in results.iterrows():
        print(f"\n{'─' * 80}")
        print(f"Policy: {row['policy_number']}")
        print(f"Total exposure: {row['exposure']:,.2f}")
        print(f"Total ceded (gross): {row['gross_ceded']:,.2f}")
        print(f"Total ceded (net): {row['net_ceded']:,.2f}")
        print(f"Total retained: {row['retained']:,.2f}")
        print(f"\nStructures applied:")
        
        for struct in row["structures_detail"]:
            status = "✓ Applied" if struct.get('applied', False) else "✗ Not applied"
            print(f"\n  {status} - {struct['structure_name']} ({struct['type_of_participation']})")
            print(f"    Input exposure: {struct['input_exposure']:,.2f}")
            if struct.get('applied', False):
                print(f"    Ceded (gross): {struct['gross_ceded']:,.2f}")
                print(f"    Ceded (net): {struct['net_ceded']:,.2f}")
                print(f"    Reinsurer Share: {struct['reinsurer_share']:.4f} ({struct['reinsurer_share']*100:.2f}%)")
            
            if struct.get('section'):
                section = struct['section']
                conditions_str = format_section_conditions(section, dimension_columns)
                print(f"    Section matched: {conditions_str}")
    
    # Générer le rapport détaillé
    generate_detailed_report(results, "detailed_report.txt")
    
    # Sauvegarder le bordereau avec Net Exposure
    output_bordereau_file = "bordereau_with_net_exposure.csv"
    bordereau_with_net.to_csv(output_bordereau_file, index=False)
    print(f"✓ Bordereau avec Net Exposure sauvegardé: {output_bordereau_file}")


if __name__ == "__main__":
    main()
