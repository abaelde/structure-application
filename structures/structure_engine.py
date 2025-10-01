import pandas as pd
from typing import Dict, Any
from products import quote_share, excess_of_loss


def check_conditions(policy_data: Dict[str, Any], conditions: list) -> bool:
    if not conditions:
        return True
    
    for condition in conditions:
        dimension = condition["dimension"]
        value = condition["value"]
        
        policy_value = policy_data.get(dimension)
        
        if policy_value != value:
            return False
    
    return True


def apply_structure(exposure: float, structure: Dict[str, Any]) -> float:
    product_type = structure["product_type"]
    
    if product_type == "quote_share":
        session_rate = structure["session_rate"]
        return quote_share(exposure, session_rate)
    
    elif product_type == "excess_of_loss":
        priority = structure["priority"]
        limit = structure["limit"]
        return excess_of_loss(exposure, priority, limit)
    
    else:
        raise ValueError(f"Unknown product type: {product_type}")


def apply_program(policy_data: Dict[str, Any], program: Dict[str, Any]) -> Dict[str, Any]:
    exposure = policy_data.get("exposition")
    mode = program["mode"]
    structures = program["structures"]
    
    total_ceded = 0.0
    structures_detail = []
    
    if mode == "sequential":
        remaining_exposure = exposure
        for structure in structures:
            if not check_conditions(policy_data, structure["conditions"]):
                structures_detail.append({
                    "structure_name": structure.get("structure_name"),
                    "product_type": structure["product_type"],
                    "input_exposure": remaining_exposure,
                    "ceded": 0.0,
                    "applied": False
                })
                continue
            
            ceded = apply_structure(remaining_exposure, structure)
            structures_detail.append({
                "structure_name": structure.get("structure_name"),
                "product_type": structure["product_type"],
                "input_exposure": remaining_exposure,
                "ceded": ceded,
                "applied": True
            })
            total_ceded += ceded
            remaining_exposure -= ceded
    
    elif mode == "parallel":
        for structure in structures:
            if not check_conditions(policy_data, structure["conditions"]):
                structures_detail.append({
                    "structure_name": structure.get("structure_name"),
                    "product_type": structure["product_type"],
                    "input_exposure": exposure,
                    "ceded": 0.0,
                    "applied": False
                })
                continue
            
            ceded = apply_structure(exposure, structure)
            structures_detail.append({
                "structure_name": structure.get("structure_name"),
                "product_type": structure["product_type"],
                "input_exposure": exposure,
                "ceded": ceded,
                "applied": True
            })
            total_ceded += ceded
    
    else:
        raise ValueError(f"Unknown mode: {mode}")
    
    return {
        "policy_number": policy_data.get("numero_police"),
        "exposure": exposure,
        "ceded": total_ceded,
        "retained": exposure - total_ceded,
        "structures_detail": structures_detail
    }


def apply_program_to_bordereau(bordereau_df: pd.DataFrame, program: Dict[str, Any]) -> pd.DataFrame:
    results = []
    
    for _, row in bordereau_df.iterrows():
        policy_data = row.to_dict()
        result = apply_program(policy_data, program)
        results.append(result)
    
    return pd.DataFrame(results)

