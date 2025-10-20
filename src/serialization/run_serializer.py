# src/serialization/run_serializer.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import uuid
import json
import pandas as pd


def _uuid() -> str:
    return uuid.uuid4().hex


def _json_or_none(obj: Any) -> Optional[str]:
    if obj is None:
        return None
    
    # Recursively convert objects to serializable format
    def _convert_to_serializable(obj: Any) -> Any:
        if obj is None:
            return None
        elif hasattr(obj, 'to_dict'):
            # Handle Condition objects specifically
            return _convert_to_serializable(obj.to_dict())
        elif isinstance(obj, dict):
            return {k: _convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [_convert_to_serializable(item) for item in obj]
        else:
            return obj
    
    converted_obj = _convert_to_serializable(obj)
    
    # obj peut déjà être un dict/list (ex: terms), ou un objet Condition (déjà to_dict côté engine)
    try:
        return json.dumps(converted_obj, ensure_ascii=False, separators=(",", ":"))
    except TypeError:
        # fallback: stringify
        return json.dumps(str(converted_obj), ensure_ascii=False, separators=(",", ":"))


@dataclass
class RunMeta:
    run_id: str
    program_name: str
    uw_dept: str
    calculation_date: str
    source_program: str
    source_bordereau: str
    program_fingerprint: Optional[str] = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    notes: Optional[str] = None


class RunSerializer:
    """
    Construit 3 DataFrames normalisés à partir de la sortie de l'engine:
      - runs
      - run_policies
      - run_policy_structures
    `results_df` doit contenir, par ligne: ProgramRunResult.to_dict()
    """

    def build_dataframes(
        self,
        run_meta: RunMeta,
        results_df: pd.DataFrame,
        source_policy_df: Optional[pd.DataFrame] = None,
    ) -> Dict[str, pd.DataFrame]:
        # ---- Table runs (1 ligne) ----
        runs_df = pd.DataFrame(
            [
                {
                    "run_id": run_meta.run_id,
                    "program_name": run_meta.program_name,
                    "uw_dept": run_meta.uw_dept,
                    "calculation_date": run_meta.calculation_date,
                    "source_program": run_meta.source_program,
                    "source_bordereau": run_meta.source_bordereau,
                    "program_fingerprint": run_meta.program_fingerprint,
                    "started_at": run_meta.started_at,
                    "ended_at": run_meta.ended_at,
                    "row_count": int(len(results_df) if results_df is not None else 0),
                    "notes": run_meta.notes,
                }
            ]
        )

        # ---- Table run_policies & run_policy_structures ----
        pol_rows: List[Dict[str, Any]] = []
        stru_rows: List[Dict[str, Any]] = []

        # Pour remonter un éventuel policy_id depuis le bordereau source
        policy_ids_series = (
            source_policy_df["policy_id"] if (source_policy_df is not None and "policy_id" in source_policy_df.columns)
            else None
        )

        for idx, result in results_df.iterrows():
            r = dict(result)  # to_dict()
            policy_run_id = _uuid()

            # Champs top-level (cf ProgramRunResult.to_dict())
            pol_rows.append(
                {
                    "policy_run_id": policy_run_id,
                    "run_id": run_meta.run_id,
                    "policy_id": (None if policy_ids_series is None else policy_ids_series.iloc[idx]),
                    "INSURED_NAME": r.get("INSURED_NAME"),
                    "INCEPTION_DT": r.get("policy_inception_date"),
                    "EXPIRE_DT": r.get("policy_expiry_date"),
                    "exclusion_status": r.get("exclusion_status"),
                    "exclusion_reason": r.get("exclusion_reason"),
                    "exposure": r.get("exposure"),
                    "effective_exposure": r.get("effective_exposure"),
                    "cession_to_layer_100pct": r.get("cession_to_layer_100pct"),
                    "cession_to_reinsurer": r.get("cession_to_reinsurer"),
                    "retained_by_cedant": r.get("retained_by_cedant"),
                    "raw_result_json": _json_or_none(r),
                }
            )

            # Structures à plat
            structures_detail = r.get("structures_detail") or []
            for sd in structures_detail:
                stru_rows.append(
                    {
                        "structure_row_id": _uuid(),
                        "policy_run_id": policy_run_id,
                        "structure_name": sd.get("structure_name"),
                        "type_of_participation": sd.get("type_of_participation"),
                        "predecessor_title": sd.get("predecessor_title") or None,
                        "claim_basis": sd.get("claim_basis"),
                        "period_start": sd.get("period_start"),
                        "period_end": sd.get("period_end"),
                        "applied": bool(sd.get("applied")),
                        "reason": sd.get("reason") or None,
                        "scope": sd.get("scope"),
                        "input_exposure": sd.get("input_exposure"),
                        "ceded_to_layer_100pct": sd.get("ceded_to_layer_100pct"),
                        "ceded_to_reinsurer": sd.get("ceded_to_reinsurer"),
                        "retained_after": sd.get("retained_after"),
                        "terms_json": _json_or_none(
                            {
                                # `terms_as_dict` est déjà aplati dans sd (via results.to_rows())
                                k: v
                                for k, v in sd.items()
                                if k
                                in {
                                    "qshare_cession_pct",
                                    "qshare_limit",
                                    "xol_attachment",
                                    "xol_limit",
                                    "signed_share",
                                }
                            }
                        ),
                        "matched_condition_json": _json_or_none(sd.get("matched_condition")),
                        "rescaling_json": _json_or_none(sd.get("rescaling")),
                        "matching_details_json": _json_or_none(sd.get("matching_details")),
                        "metrics_json": _json_or_none(sd.get("metrics")),
                    }
                )

        run_policies_df = pd.DataFrame(pol_rows)
        run_policy_structures_df = pd.DataFrame(stru_rows)

        return {
            "runs": runs_df,
            "run_policies": run_policies_df,
            "run_policy_structures": run_policy_structures_df,
        }
