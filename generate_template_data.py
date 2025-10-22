#!/usr/bin/env python3
"""
Script pour générer un fichier CSV de template avec des données variées
pour l'entraînement des contreparties.
"""

import pandas as pd
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Configuration
NUM_RECORDS = 5000  # Nombre de lignes à générer
OUTPUT_FILE = "template_results.csv"

# Listes de données réalistes
CEDENT_NAMES = [
    "AXA",
    "ALLIANZ",
    "MUNICH RE",
    "SWISS RE",
    "HANNOVER RE",
    "SCOR",
    "GENERALI",
    "ZURICH",
    "CHUBB",
    "BERKSHIRE HATHAWAY"
]

# Mapping des cédantes avec leurs pays et monnaies principales
CEDENT_COUNTRIES = {
    "AXA": ["France", "Germany", "UK", "USA"],
    "ALLIANZ": ["Germany", "Austria", "Switzerland", "USA"],
    "MUNICH RE": ["Germany", "UK", "USA", "Singapore"],
    "SWISS RE": ["Switzerland", "UK", "USA", "Germany"],
    "HANNOVER RE": ["Germany", "UK", "USA", "France"],
    "SCOR": ["France", "Germany", "UK", "USA"],
    "GENERALI": ["Italy", "Germany", "France", "Austria"],
    "ZURICH": ["Switzerland", "UK", "USA", "Germany"],
    "CHUBB": ["USA", "UK", "Switzerland", "Singapore"],
    "BERKSHIRE HATHAWAY": ["USA", "UK", "Germany", "Switzerland"]
}

# Mapping des pays avec leurs monnaies
COUNTRY_CURRENCIES = {
    "France": "EUR",
    "Germany": "EUR", 
    "Austria": "EUR",
    "Italy": "EUR",
    "Switzerland": "CHF",
    "UK": "GBP",
    "USA": "USD",
    "Singapore": "SGD"
}

AIRLINE_NAMES = [
    "AIR FRANCE-KLM",
    "LUFTHANSA GROUP",
    "EMIRATES AIRLINES",
    "SINGAPORE AIRLINES",
    "AIR CANADA",
    "QATAR AIRWAYS",
    "BRITISH AIRWAYS",
    "AMERICAN AIRLINES",
    "DELTA AIR LINES",
    "UNITED AIRLINES",
    "JAPAN AIRLINES",
    "ANA (ALL NIPPON AIRWAYS)",
    "CATHAY PACIFIC",
    "THAI AIRWAYS",
    "MALAYSIA AIRLINES",
    "KOREAN AIR",
    "CHINA SOUTHERN",
    "CHINA EASTERN",
    "AIR CHINA",
    "TURKISH AIRLINES",
    "SAUDI ARABIAN AIRLINES",
    "ETIHAD AIRWAYS",
    "VIRGIN ATLANTIC",
    "EASYJET",
    "RYANAIR",
    "SOUTHWEST AIRLINES",
    "JETBLUE AIRWAYS",
    "ALASKA AIRLINES",
    "SPIRIT AIRLINES",
    "FRONTIER AIRLINES"
]

EXCLUSION_REASONS = [
    "",
    "War Risk Exclusion",
    "Nuclear Risk Exclusion",
    "Terrorism Exclusion",
    "Cyber Risk Exclusion",
    "Pandemic Exclusion"
]

def generate_policy_dates() -> tuple:
    """Génère des dates de début et fin de police réalistes."""
    # Date de début entre 2024 et 2025
    start_date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 365))
    
    # Durée de police entre 1 et 2 ans
    duration_days = random.choice([365, 730])  # 1 an ou 2 ans
    end_date = start_date + timedelta(days=duration_days)
    
    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

def generate_exposure_data() -> Dict[str, float]:
    """Génère des données d'exposition réalistes."""
    # Exposition de base entre 10M et 100M
    base_exposure = random.uniform(10000000, 100000000)
    
    # Pourcentage cédé au layer 100% (entre 0% et 90%)
    ceded_percentage = random.uniform(0, 0.9)
    ceded_to_layer = base_exposure * ceded_percentage
    
    # Montant cédé au réassureur (légèrement inférieur au layer)
    ceded_to_reinsurer = ceded_to_layer * random.uniform(0.95, 0.99)
    
    # Montant retenu par la cédante
    retained = base_exposure - ceded_to_layer
    
    return {
        "exposure": round(base_exposure, 1),
        "total_ceded_by_cedent": round(ceded_to_layer, 1),
        "ceded_to_reinsurer": round(ceded_to_reinsurer, 1),
        "retained_by_cedant": round(retained, 1)
    }

def generate_exclusion_data() -> tuple:
    """Génère des données d'exclusion."""
    # 80% des polices sont incluses, 20% exclues
    if random.random() < 0.8:
        return "included", ""
    else:
        return "excluded", random.choice(EXCLUSION_REASONS[1:])  # Exclure la chaîne vide

def generate_cedent_location_data(cedent_name: str) -> tuple:
    """Génère le pays et la monnaie pour une cédante donnée."""
    # Choisir un pays parmi ceux disponibles pour cette cédante
    available_countries = CEDENT_COUNTRIES[cedent_name]
    country = random.choice(available_countries)
    
    # Obtenir la monnaie correspondante
    currency = COUNTRY_CURRENCIES[country]
    
    return country, currency

def generate_record() -> Dict[str, Any]:
    """Génère un enregistrement complet."""
    exposure_data = generate_exposure_data()
    policy_start, policy_end = generate_policy_dates()
    exclusion_status, exclusion_reason = generate_exclusion_data()
    
    # Générer la cédante et ses données géographiques
    cedent_name = random.choice(CEDENT_NAMES)
    country, currency = generate_cedent_location_data(cedent_name)
    
    return {
        "insured_name": random.choice(AIRLINE_NAMES),
        "cedent_name": cedent_name,
        "country": country,
        "currency": currency,
        "exposure": exposure_data["exposure"],
        "total_ceded_by_cedent": exposure_data["total_ceded_by_cedent"],
        "ceded_to_reinsurer": exposure_data["ceded_to_reinsurer"],
        "retained_by_cedant": exposure_data["retained_by_cedant"],
        "policy_inception_date": policy_start,
        "policy_expiry_date": policy_end,
        "exclusion_status": exclusion_status,
        "exclusion_reason": exclusion_reason,        
    }

def main():
    """Fonction principale pour générer le fichier CSV."""
    print(f"Génération de {NUM_RECORDS} enregistrements...")
    
    # Générer tous les enregistrements
    records = []
    for i in range(NUM_RECORDS):
        records.append(generate_record())
        if (i + 1) % 10 == 0:
            print(f"Généré {i + 1}/{NUM_RECORDS} enregistrements...")
    
    # Créer le DataFrame
    df = pd.DataFrame(records)
    
    # Sauvegarder en CSV
    df.to_csv(OUTPUT_FILE, index=False)
    
    print(f"✅ Fichier généré : {OUTPUT_FILE}")
    print(f"📊 Statistiques :")
    print(f"   - Nombre d'enregistrements : {len(df)}")
    print(f"   - Nombre de cédantes uniques : {df['cedent_name'].nunique()}")
    print(f"   - Nombre d'airlines uniques : {df['insured_name'].nunique()}")
    print(f"   - Nombre de pays uniques : {df['country'].nunique()}")
    print(f"   - Nombre de monnaies uniques : {df['currency'].nunique()}")
    print(f"   - Polices exclues : {len(df[df['exclusion_status'] == 'excluded'])}")
    print(f"   - Polices incluses : {len(df[df['exclusion_status'] == 'included'])}")
    
    # Afficher la distribution par pays et monnaie
    print(f"\n🌍 Distribution par pays :")
    print(df['country'].value_counts().head())
    print(f"\n💰 Distribution par monnaie :")
    print(df['currency'].value_counts())
    
    # Afficher un échantillon
    print(f"\n📋 Échantillon des données :")
    print(df.head().to_string(index=False))

if __name__ == "__main__":
    main()
