import pandas as pd
import numpy as np

program_data = {
    "program_name": ["PROGRAM_2024"],
    "mode": ["sequential"]
}

structures_data = {
    "structure_name": ["QS_GENERAL", "XOL_LARGE"],
    "order": [1, 2],
    "product_type": ["quote_share", "excess_of_loss"]
}

sections_data = {
    "structure_name": ["QS_GENERAL", "QS_GENERAL", "XOL_LARGE"],
    "session_rate": [0.30, 0.40, np.nan],
    "priority": [np.nan, np.nan, 500000],
    "limit": [np.nan, np.nan, 1000000],
    "localisation": [np.nan, "Paris", "Paris"],
    "industrie": [np.nan, np.nan, np.nan]
}

program_df = pd.DataFrame(program_data)
structures_df = pd.DataFrame(structures_data)
sections_df = pd.DataFrame(sections_data)

with pd.ExcelWriter("program_config.xlsx", engine="openpyxl") as writer:
    program_df.to_excel(writer, sheet_name="program", index=False)
    structures_df.to_excel(writer, sheet_name="structures", index=False)
    sections_df.to_excel(writer, sheet_name="sections", index=False)

print("✓ Excel file 'program_config.xlsx' created successfully!")
print("\n" + "=" * 80)
print("PROGRAM CONFIGURATION")
print("=" * 80)

print("\n=== Program ===")
print(program_df)

print("\n=== Structures ===")
print(structures_df)

print("\n=== Sections ===")
print(sections_df)

print("\n" + "=" * 80)
print("EXPLANATION")
print("=" * 80)
print("""
This configuration creates a sequential program with:

1. QS_GENERAL (Quote Share):
   - Section 1: 30% for all policies (no conditions)
   - Section 2: 40% for policies in Paris (localisation=Paris)
   → Most specific section wins: Paris policies get 40%, others get 30%

2. XOL_LARGE (Excess of Loss):
   - Section 1: 1M xs 500K for policies in Paris only
   → Applied only to Paris policies

The system automatically:
- Detects dimension columns (localisation, industrie)
- Matches the most specific section for each policy
- Applies structures sequentially (output of one → input of next)
""")

