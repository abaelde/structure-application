"""
Example: Creating a new program using the specification guide

This demonstrates how to create a program from natural language specification.

USER REQUEST:
"I want a program with:
- 25% quote-share by default
- 30% quote-share for France
- 35% quote-share for EMEA region
- XoL of 800K xs 400K only for Technology industry"
"""

import pandas as pd
import numpy as np

program_data = {
    "program_name": ["REGIONAL_TECH_2024"],
    "mode": ["sequential"]
}

structures_data = {
    "structure_name": ["QS_REGIONAL", "XOL_TECH"],
    "order": [1, 2],
    "product_type": ["quote_share", "excess_of_loss"]
}

sections_data = {
    "structure_name": ["QS_REGIONAL", "QS_REGIONAL", "QS_REGIONAL", "XOL_TECH"],
    "session_rate": [0.25, 0.30, 0.35, np.nan],
    "priority": [np.nan, np.nan, np.nan, 400000],
    "limit": [np.nan, np.nan, np.nan, 800000],
    "country": [np.nan, "France", np.nan, np.nan],
    "region": [np.nan, np.nan, "EMEA", np.nan],
    "product_type_1": [np.nan, np.nan, np.nan, np.nan],
    "product_type_2": [np.nan, np.nan, np.nan, np.nan],
    "product_type_3": [np.nan, np.nan, np.nan, np.nan],
    "currency": [np.nan, np.nan, np.nan, np.nan],
    "line_of_business": [np.nan, np.nan, np.nan, np.nan],
    "industry": [np.nan, np.nan, np.nan, "Technology"],
    "sic_code": [np.nan, np.nan, np.nan, np.nan],
    "include": [np.nan, np.nan, np.nan, np.nan]
}

program_df = pd.DataFrame(program_data)
structures_df = pd.DataFrame(structures_data)
sections_df = pd.DataFrame(sections_data)

with pd.ExcelWriter("program_config_regional.xlsx", engine="openpyxl") as writer:
    program_df.to_excel(writer, sheet_name="program", index=False)
    structures_df.to_excel(writer, sheet_name="structures", index=False)
    sections_df.to_excel(writer, sheet_name="sections", index=False)

print("✓ New program created: program_config_regional.xlsx")
print("\n" + "=" * 80)
print("PROGRAM STRUCTURE")
print("=" * 80)

print("\nProgram:")
print(program_df)

print("\nStructures:")
print(structures_df)

print("\nSections:")
print(sections_df)

print("\n" + "=" * 80)
print("EXPECTED BEHAVIOR")
print("=" * 80)
print("""
Policy in France, EMEA, Construction:
  → QS_REGIONAL: 30% (country=France section - most specific)
  → XOL_TECH: Not applied (industry != Technology)

Policy in Germany, EMEA, Technology:
  → QS_REGIONAL: 35% (region=EMEA section)
  → XOL_TECH: 800K xs 400K applied (industry=Technology)

Policy in Singapore, APAC, Manufacturing:
  → QS_REGIONAL: 25% (default section, no conditions)
  → XOL_TECH: Not applied (industry != Technology)
""")

