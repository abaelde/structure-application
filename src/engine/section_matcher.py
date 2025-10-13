import pandas as pd
from typing import Dict, Any, Optional, List


def check_exclusion(
    policy_data: Dict[str, Any], sections: List[Dict[str, Any]], dimension_columns: List[str]
) -> bool:
    for section in sections:
        if section.get("BUSCL_EXCLUDE_CD") == "exclude":
            matches = True
            
            for dimension in dimension_columns:
                if dimension == "BUSCL_EXCLUDE_CD":
                    continue
                
                section_value = section.get(dimension)
                
                if pd.notna(section_value):
                    policy_value = policy_data.get(dimension)
                    if policy_value != section_value:
                        matches = False
                        break
            
            if matches:
                return True
    
    return False


def match_section(
    policy_data: Dict[str, Any], sections: List[Dict[str, Any]], dimension_columns: List[str]
) -> Optional[Dict[str, Any]]:
    matched_sections = []

    for section in sections:
        if section.get("BUSCL_EXCLUDE_CD") == "exclude":
            continue
        
        matches = True
        specificity = 0

        for dimension in dimension_columns:
            section_value = section.get(dimension)

            if pd.notna(section_value):
                policy_value = policy_data.get(dimension)
                if policy_value != section_value:
                    matches = False
                    break
                specificity += 1

        if matches:
            matched_sections.append((section, specificity))

    if not matched_sections:
        return None

    matched_sections.sort(key=lambda x: x[1], reverse=True)
    return matched_sections[0][0]

