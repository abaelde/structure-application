# Program Specification Guide

This document defines the standard format for creating reinsurance programs. Use this as a reference when translating user requirements into Excel configuration files.

## Data Model Overview

A reinsurance program consists of three interconnected tables:

```
PROGRAM → STRUCTURES → SECTIONS
   1          n           n
```

### Table 1: PROGRAM (program sheet)
Defines the main program configuration.

**Columns:**
- `program_name` (string, required): Unique identifier for the program
- `mode` (enum, required): `"sequential"` or `"parallel"`
  - `sequential`: Structures apply one after another (output → input)
  - `parallel`: All structures apply independently on original exposure

**Rules:**
- Only ONE row per file
- program_name should be descriptive (e.g., "PROGRAM_2024", "TREATY_XYZ")

**Example:**
```
program_name  | mode
PROGRAM_2024  | sequential
```

---

### Table 2: STRUCTURES (structures sheet)
Defines the building blocks of the program.

**Columns:**
- `structure_name` (string, required): Unique identifier for the structure
- `order` (integer, required): Execution order (1, 2, 3, ...)
- `product_type` (enum, required): `"quote_share"` or `"excess_of_loss"`

**Rules:**
- Order must start at 1 and be consecutive
- structure_name should be descriptive (e.g., "QS_30", "XOL_PRIMARY")
- Each structure can have multiple sections (defined in sections sheet)

**Example:**
```
structure_name | order | product_type
QS_GENERAL     | 1     | quote_share
XOL_LARGE      | 2     | excess_of_loss
QS_SPECIAL     | 3     | quote_share
```

---

### Table 3: SECTIONS (sections sheet)
Defines parameter sets and conditions for each structure.

**Fixed Columns:**
- `structure_name` (string, required): References structures.structure_name
- `session_rate` (float, 0-1): For quote_share only (e.g., 0.30 = 30%)
- `priority` (float): For excess_of_loss only (in same unit as exposure)
- `limit` (float): For excess_of_loss only (in same unit as exposure)

**Dynamic Columns (Dimensions):**
- Any additional columns are automatically detected as dimensions
- Common dimensions: `localisation`, `industrie`, `product_line`, etc.
- Empty/NaN values mean "no condition on this dimension"
- Non-empty values create specific conditions

**Rules:**
1. One row = one section (one parameter set with specific conditions)
2. Multiple sections per structure allow different parameters for different conditions
3. When multiple sections match, the **most specific** wins (most non-empty dimensions)
4. At least one section per structure is required
5. For quote_share: session_rate is required, priority/limit must be empty
6. For excess_of_loss: priority and limit are required, session_rate must be empty

**Example:**
```
structure_name | session_rate | priority | limit   | localisation | industrie
QS_GENERAL     | 0.30         | NaN      | NaN     | NaN          | NaN
QS_GENERAL     | 0.40         | NaN      | NaN     | Paris        | NaN
QS_GENERAL     | 0.50         | NaN      | NaN     | Paris        | Technology
XOL_LARGE      | NaN          | 500000   | 1000000 | Paris        | NaN
XOL_LARGE      | NaN          | 300000   | 800000  | Lyon         | NaN
```

---

## Section Matching Logic

For each policy and each structure:
1. Find all sections where ALL non-empty dimension values match the policy
2. If multiple sections match, choose the one with the most conditions (highest specificity)
3. If no section matches, the structure is not applied

**Example:**
Policy: `{localisation: "Paris", industrie: "Technology"}`

Available sections for QS_GENERAL:
- Section A: no conditions (specificity=0) ✓ matches
- Section B: localisation="Paris" (specificity=1) ✓ matches
- Section C: localisation="Paris", industrie="Technology" (specificity=2) ✓ matches
- Section D: localisation="Lyon" (specificity=1) ✗ doesn't match

**Winner: Section C** (most specific with 2 conditions)

---

## Common Patterns

### Pattern 1: Global default with regional overrides
```
# Quote-share: 20% default, 30% for Paris, 40% for high-risk
structure_name | session_rate | localisation | risk_category
QS_BASE        | 0.20         | NaN          | NaN
QS_BASE        | 0.30         | Paris        | NaN
QS_BASE        | 0.40         | NaN          | high
```

### Pattern 2: Regional excess of loss
```
# Different XoL parameters per region
structure_name | priority | limit   | localisation
XOL_REGIONAL   | 500000   | 1000000 | France
XOL_REGIONAL   | 300000   | 800000  | Germany
XOL_REGIONAL   | 1000000  | 2000000 | USA
```

### Pattern 3: Industry-specific structures
```
# Different treatments per industry
structure_name | session_rate | priority | limit   | industrie
QS_INDUSTRY    | 0.25         | NaN      | NaN     | Construction
QS_INDUSTRY    | 0.35         | NaN      | NaN     | Technology
XOL_INDUSTRY   | NaN          | 400000   | 900000  | Manufacturing
```

### Pattern 4: Complex multi-dimensional
```
# Combination of location and industry
structure_name | session_rate | localisation | industrie
QS_COMPLEX     | 0.20         | NaN          | NaN
QS_COMPLEX     | 0.30         | Paris        | NaN
QS_COMPLEX     | 0.25         | Lyon         | NaN
QS_COMPLEX     | 0.35         | Paris        | Technology
QS_COMPLEX     | 0.40         | Paris        | Finance
```

---

## Translation Examples

### Example 1: Simple sequential program
**User Request:**
"I want a sequential program with a 30% quote-share followed by an XoL of 1M excess of 500K"

**Translation:**
```python
# Program sheet
program_name="SIMPLE_2024", mode="sequential"

# Structures sheet
QS_30, order=1, product_type="quote_share"
XOL_1M_500K, order=2, product_type="excess_of_loss"

# Sections sheet
QS_30: session_rate=0.30, all dimensions=NaN
XOL_1M_500K: priority=500000, limit=1000000, all dimensions=NaN
```

### Example 2: Regional variations
**User Request:**
"I need a quote-share that's 25% for most policies, but 35% for Paris and 40% for Lyon. Then an XoL of 800K xs 400K only for Paris."

**Translation:**
```python
# Program sheet
program_name="REGIONAL_2024", mode="sequential"

# Structures sheet
QS_REGIONAL, order=1, product_type="quote_share"
XOL_PARIS, order=2, product_type="excess_of_loss"

# Sections sheet
QS_REGIONAL: session_rate=0.25, localisation=NaN
QS_REGIONAL: session_rate=0.35, localisation="Paris"
QS_REGIONAL: session_rate=0.40, localisation="Lyon"
XOL_PARIS: priority=400000, limit=800000, localisation="Paris"
```

### Example 3: Parallel structures
**User Request:**
"Apply in parallel: 20% quote-share and an XoL of 500K xs 300K, both on all policies"

**Translation:**
```python
# Program sheet
program_name="PARALLEL_2024", mode="parallel"

# Structures sheet
QS_20, order=1, product_type="quote_share"
XOL_500_300, order=2, product_type="excess_of_loss"

# Sections sheet
QS_20: session_rate=0.20, all dimensions=NaN
XOL_500_300: priority=300000, limit=500000, all dimensions=NaN
```

### Example 4: Industry-specific with fallback
**User Request:**
"30% cession for Technology companies, 25% for Construction, and 20% for everyone else"

**Translation:**
```python
# Program sheet
program_name="INDUSTRY_2024", mode="sequential"

# Structures sheet
QS_INDUSTRY, order=1, product_type="quote_share"

# Sections sheet
QS_INDUSTRY: session_rate=0.20, industrie=NaN  # Default
QS_INDUSTRY: session_rate=0.30, industrie="Technology"
QS_INDUSTRY: session_rate=0.25, industrie="Construction"
```

---

## Python Script Template

When creating a program configuration programmatically, use this template:

```python
import pandas as pd
import numpy as np

# 1. Define program
program_data = {
    "program_name": ["YOUR_PROGRAM_NAME"],
    "mode": ["sequential"]  # or "parallel"
}

# 2. Define structures
structures_data = {
    "structure_name": ["STRUCT_1", "STRUCT_2"],
    "order": [1, 2],
    "product_type": ["quote_share", "excess_of_loss"]
}

# 3. Define sections
sections_data = {
    "structure_name": ["STRUCT_1", "STRUCT_1", "STRUCT_2"],
    "session_rate": [0.30, 0.40, np.nan],
    "priority": [np.nan, np.nan, 500000],
    "limit": [np.nan, np.nan, 1000000],
    # Add dimension columns here
    "localisation": [np.nan, "Paris", "Paris"],
    "industrie": [np.nan, np.nan, np.nan],
    # Add more dimensions as needed
}

# 4. Create DataFrames
program_df = pd.DataFrame(program_data)
structures_df = pd.DataFrame(structures_data)
sections_df = pd.DataFrame(sections_data)

# 5. Write to Excel
with pd.ExcelWriter("program_config.xlsx", engine="openpyxl") as writer:
    program_df.to_excel(writer, sheet_name="program", index=False)
    structures_df.to_excel(writer, sheet_name="structures", index=False)
    sections_df.to_excel(writer, sheet_name="sections", index=False)
```

---

## Validation Checklist

Before finalizing a program configuration, verify:

- [ ] Program sheet has exactly 1 row
- [ ] mode is either "sequential" or "parallel"
- [ ] Structure orders are consecutive starting from 1
- [ ] All structure_names in sections exist in structures
- [ ] Each structure has at least one section
- [ ] Quote-share sections have session_rate (0-1) and NaN for priority/limit
- [ ] Excess-of-loss sections have priority and limit, and NaN for session_rate
- [ ] Dimension column names match bordereau column names exactly
- [ ] No duplicate sections (same structure + same dimension values)
- [ ] At least one generic section (all dimensions NaN) OR all policies covered

---

## Best Practices

1. **Naming conventions:**
   - Use descriptive structure names (QS_30_PARIS, XOL_PRIMARY)
   - Keep names short but meaningful
   - Use UPPER_CASE for consistency

2. **Section design:**
   - Always include a generic fallback section (all dimensions NaN) if possible
   - Order sections from generic to specific in Excel for readability
   - Document complex logic in section names or comments

3. **Testing:**
   - Test with sample bordereaux covering all dimension combinations
   - Verify specificity matching works as expected
   - Check edge cases (no matching section, multiple matches)

4. **Maintenance:**
   - Keep dimension columns consistent across all programs
   - Document business rules separately
   - Version your configuration files

---

## Quick Reference

| Product Type   | Required Parameters          | Optional          |
|----------------|------------------------------|-------------------|
| quote_share    | session_rate (0-1)           | dimension columns |
| excess_of_loss | priority, limit (positive)   | dimension columns |

| Mode       | Behavior                                          |
|------------|---------------------------------------------------|
| sequential | Structures apply in order, output → next input    |
| parallel   | All structures apply on original exposure         |

**Remember:** The system automatically detects dimension columns. Any column in sections that's not `structure_name`, `session_rate`, `priority`, or `limit` is treated as a dimension for matching.

