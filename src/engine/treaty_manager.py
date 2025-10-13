"""
Gestionnaire de traités pour gérer plusieurs traités par année
et la logique de sélection selon claim_basis
"""

import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from src.loaders import ProgramLoader


class TreatyManager:
    def __init__(self, treaty_paths: Dict[str, str]):
        """
        Initialise le gestionnaire de traités

        Args:
            treaty_paths: Dictionnaire {année: chemin_vers_fichier_excel}
                         Exemple: {"2023": "treaty_2023.xlsx", "2024": "treaty_2024.xlsx"}
        """
        self.treaty_paths = treaty_paths
        self.treaties = {}
        self.load_all_treaties()

    def load_all_treaties(self):
        """Charge tous les traités disponibles"""
        for year, path in self.treaty_paths.items():
            try:
                loader = ProgramLoader(path)
                self.treaties[year] = loader.get_program()
                print(f"✓ Traité {year} chargé depuis {path}")
            except Exception as e:
                print(f"⚠️  Erreur lors du chargement du traité {year}: {e}")

    def get_available_years(self) -> List[str]:
        """Retourne la liste des années de traités disponibles"""
        return sorted(self.treaties.keys())

    def get_treaty_for_year(self, year: str) -> Optional[Dict[str, Any]]:
        """Retourne le traité pour une année donnée"""
        return self.treaties.get(year)

    def select_treaty(
        self, claim_basis: str, policy_inception_date: str, calculation_date: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Sélectionne le traité approprié selon la logique claim_basis

        Args:
            claim_basis: "risk_attaching" ou "loss_occurring"
            policy_inception_date: Date de souscription de la police (YYYY-MM-DD)
            calculation_date: Date de calcul "as of now" (YYYY-MM-DD)
                             Si None, utilise la date actuelle

        Returns:
            Le traité approprié ou None si aucun traité n'est trouvé
        """
        if calculation_date is None:
            calculation_date = datetime.now().strftime("%Y-%m-%d")

        # Déterminer l'année de référence selon claim_basis
        if claim_basis == "risk_attaching":
            # Pour risk_attaching, on utilise la date de souscription de la police
            reference_date = policy_inception_date
        elif claim_basis == "loss_occurring":
            # Pour loss_occurring, on utilise la date de calcul
            reference_date = calculation_date
        else:
            raise ValueError(
                f"claim_basis invalide: {claim_basis}. Doit être 'risk_attaching' ou 'loss_occurring'"
            )

        # Extraire l'année de la date de référence
        reference_year = reference_date.split("-")[0]

        # Retourner le traité pour cette année
        treaty = self.get_treaty_for_year(reference_year)

        if treaty is None:
            print(
                f"⚠️  Aucun traité trouvé pour l'année {reference_year} (claim_basis: {claim_basis})"
            )

        return treaty

    def get_treaty_info(self) -> Dict[str, Any]:
        """Retourne des informations sur tous les traités disponibles"""
        info = {
            "available_years": self.get_available_years(),
            "treaties_count": len(self.treaties),
            "treaties_details": {},
        }

        for year, treaty in self.treaties.items():
            info["treaties_details"][year] = {
                "name": treaty["name"],
                "structures_count": len(treaty["structures"]),
                "structures": [
                    {
                        "name": s["structure_name"],
                        "type": s["type_of_participation"],
                        "claim_basis": s.get("claim_basis"),
                        "inception_date": s.get("inception_date"),
                        "expiry_date": s.get("expiry_date"),
                    }
                    for s in treaty["structures"]
                ],
            }

        return info


def create_treaty_manager_from_directory(
    directory_path: str, pattern: str = "treaty_{year}.xlsx"
) -> TreatyManager:
    """
    Crée un TreatyManager à partir d'un répertoire contenant des fichiers de traités

    Args:
        directory_path: Chemin vers le répertoire
        pattern: Pattern des noms de fichiers (par défaut: "treaty_{year}.xlsx")

    Returns:
        TreatyManager configuré
    """
    import os
    import glob

    treaty_paths = {}

    # Chercher tous les fichiers correspondant au pattern
    search_pattern = os.path.join(directory_path, pattern.replace("{year}", "*"))
    files = glob.glob(search_pattern)

    for file_path in files:
        # Extraire l'année du nom de fichier
        filename = os.path.basename(file_path)
        # Supposer que l'année est dans le nom de fichier
        for year in ["2023", "2024", "2025", "2026", "2027"]:
            if year in filename:
                treaty_paths[year] = file_path
                break

    return TreatyManager(treaty_paths)

