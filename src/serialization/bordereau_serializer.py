# src/serialization/bordereau_serializer.py
from __future__ import annotations
from typing import Optional
import pandas as pd
from src.domain.bordereau import Bordereau
from src.domain.program import Program


class BordereauSerializer:
    """
    Parité avec ProgramSerializer, mais fin et volontairement simple.
    - dataframe -> Bordereau (normalisation/validation via Bordereau)
    - Bordereau -> dataframe canonique pour l'engine
    """

    def dataframe_to_bordereau(
        self,
        df: pd.DataFrame,
        *,
        uw_dept: Optional[str] = None,
        source: Optional[str] = None,
        program: Optional[Program] = None,
        validate: bool = True,
    ) -> Bordereau:
        b = Bordereau(df, uw_dept=uw_dept, source=source, program=program)
        if validate:
            # Si on a le uw_dept (direct ou via program), on valide l'expo de façon stricte
            b.validate(check_exposure_columns=bool(uw_dept or program))
        return b

    def bordereau_to_dataframe(self, bordereau: Bordereau) -> pd.DataFrame:
        # Vue canonique prête pour l'engine
        return bordereau.to_engine_dataframe()
