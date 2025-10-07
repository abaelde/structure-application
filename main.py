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
    
    display_program(program)
    
    bordereau_with_net, results = apply_program_to_bordereau(bordereau_df, program)
    
    print("\n\n" + "=" * 80)
    print("BORDEREAU WITH NET EXPOSURE")
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
        print(f"POLICY: {row['policy_number']}")
        print(f"Initial exposure: {row['exposure']:,.2f}")
        print(f"Total ceded (gross): {row['gross_ceded']:,.2f}")
        print(f"Total ceded (net): {row['net_ceded']:,.2f}")
        print(f"Retention: {row['retained']:,.2f}")
        print(f"\nStructures applied:")
        
        for i, struct in enumerate(row["structures_detail"], 1):
            status = "✓ APPLIED" if struct.get('applied', False) else "✗ NOT APPLIED"
            print(f"\n{i}. {struct['structure_name']} ({struct['type_of_participation']}) - {status}")
            print(f"   Input exposure: {struct['input_exposure']:,.2f}")
            if struct.get('applied', False):
                print(f"   Ceded (gross): {struct['gross_ceded']:,.2f}")
                print(f"   Ceded (net): {struct['net_ceded']:,.2f}")
                print(f"   Reinsurer Share: {struct['reinsurer_share']:.4f} ({struct['reinsurer_share']*100:.2f}%)")
                
                if struct.get('section'):
                    section = struct['section']
                    print(f"   Applied section parameters:")
                    
                    if struct['type_of_participation'] == 'quota_share':
                        if pd.notna(section.get('CESSION_PCT')):
                            print(f"      CESSION_PCT: {section['CESSION_PCT']}")
                        if pd.notna(section.get('LIMIT_OCCURRENCE_100')):
                            print(f"      LIMIT_OCCURRENCE_100: {section['LIMIT_OCCURRENCE_100']}")
                    elif struct['type_of_participation'] == 'excess_of_loss':
                        if pd.notna(section.get('ATTACHMENT_POINT_100')):
                            print(f"      ATTACHMENT_POINT_100: {section['ATTACHMENT_POINT_100']}")
                        if pd.notna(section.get('LIMIT_OCCURRENCE_100')):
                            print(f"      LIMIT_OCCURRENCE_100: {section['LIMIT_OCCURRENCE_100']}")
                    
                    if pd.notna(section.get('SIGNED_SHARE_PCT')):
                        print(f"      SIGNED_SHARE_PCT: {section['SIGNED_SHARE_PCT']}")
                    
                    conditions_str = format_section_conditions(section, dimension_columns)
                    print(f"   Matching conditions: {conditions_str}")
            else:
                print(f"   Reason: No matching section found")
    
    generate_detailed_report(results, "detailed_report.txt")
    
    output_bordereau_file = "bordereau_with_net_exposure.csv"
    bordereau_with_net.to_csv(output_bordereau_file, index=False)
    print(f"\n✓ Bordereau with Net Exposure saved: {output_bordereau_file}")


if __name__ == "__main__":
    main()
