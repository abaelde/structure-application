import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from products import quote_share, excess_of_loss


def match_section(policy_data: Dict[str, Any], sections: list, dimension_columns: list) -> Optional[Dict[str, Any]]:
    matched_sections = []
    
    for section in sections:
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


def apply_section(exposure: float, section: Dict[str, Any], product_type: str) -> float:
    if product_type == "quote_share":
        session_rate = section["session_rate"]
        if pd.isna(session_rate):
            raise ValueError("session_rate is required for quote_share")
        return quote_share(exposure, session_rate)
    
    elif product_type == "excess_of_loss":
        priority = section["priority"]
        limit = section["limit"]
        if pd.isna(priority) or pd.isna(limit):
            raise ValueError("priority and limit are required for excess_of_loss")
        return excess_of_loss(exposure, priority, limit)
    
    else:
        raise ValueError(f"Unknown product type: {product_type}")


def apply_program(policy_data: Dict[str, Any], program: Dict[str, Any]) -> Dict[str, Any]:
    exposure = policy_data.get("exposition")
    mode = program["mode"]
    structures = program["structures"]
    dimension_columns = program["dimension_columns"]
    
    total_ceded = 0.0
    structures_detail = []
    
    if mode == "sequential":
        remaining_exposure = exposure
        for structure in structures:
            matched_section = match_section(policy_data, structure["sections"], dimension_columns)
            
            if matched_section is None:
                structures_detail.append({
                    "structure_name": structure["structure_name"],
                    "product_type": structure["product_type"],
                    "claim_basis": structure.get("claim_basis"),
                    "inception_date": structure.get("inception_date"),
                    "expiry_date": structure.get("expiry_date"),
                    "input_exposure": remaining_exposure,
                    "ceded": 0.0,
                    "applied": False,
                    "section": None
                })
                continue
            
            ceded = apply_section(remaining_exposure, matched_section, structure["product_type"])
            structures_detail.append({
                "structure_name": structure["structure_name"],
                "product_type": structure["product_type"],
                "claim_basis": structure.get("claim_basis"),
                "inception_date": structure.get("inception_date"),
                "expiry_date": structure.get("expiry_date"),
                "input_exposure": remaining_exposure,
                "ceded": ceded,
                "applied": True,
                "section": matched_section
            })
            total_ceded += ceded
            remaining_exposure -= ceded
    
    elif mode == "parallel":
        for structure in structures:
            matched_section = match_section(policy_data, structure["sections"], dimension_columns)
            
            if matched_section is None:
                structures_detail.append({
                    "structure_name": structure["structure_name"],
                    "product_type": structure["product_type"],
                    "claim_basis": structure.get("claim_basis"),
                    "inception_date": structure.get("inception_date"),
                    "expiry_date": structure.get("expiry_date"),
                    "input_exposure": exposure,
                    "ceded": 0.0,
                    "applied": False,
                    "section": None
                })
                continue
            
            ceded = apply_section(exposure, matched_section, structure["product_type"])
            structures_detail.append({
                "structure_name": structure["structure_name"],
                "product_type": structure["product_type"],
                "claim_basis": structure.get("claim_basis"),
                "inception_date": structure.get("inception_date"),
                "expiry_date": structure.get("expiry_date"),
                "input_exposure": exposure,
                "ceded": ceded,
                "applied": True,
                "section": matched_section
            })
            total_ceded += ceded
    
    else:
        raise ValueError(f"Unknown mode: {mode}")
    
    return {
        "policy_number": policy_data.get("numero_police"),
        "exposure": exposure,
        "ceded": total_ceded,
        "retained": exposure - total_ceded,
        "policy_inception_date": policy_data.get("inception_date"),
        "policy_expiry_date": policy_data.get("expiry_date"),
        "structures_detail": structures_detail
    }


def apply_program_to_bordereau(bordereau_df: pd.DataFrame, program: Dict[str, Any]) -> pd.DataFrame:
    results = []
    
    for _, row in bordereau_df.iterrows():
        policy_data = row.to_dict()
        result = apply_program(policy_data, program)
        results.append(result)
    
    return pd.DataFrame(results)

