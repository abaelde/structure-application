#!/usr/bin/env python3
"""
Script pour analyser la structure des CSV et générer automatiquement 
le DDL Snowflake correspondant.
"""

import pandas as pd
from pathlib import Path
import json

def analyze_csv_structure(csv_folder: str):
    """Analyse la structure des CSV et retourne les colonnes de chaque table"""
    
    folder = Path(csv_folder)
    if not folder.exists():
        raise ValueError(f"Dossier non trouvé: {csv_folder}")
    
    structure = {}
    
    # Analyser program.csv
    program_file = folder / "program.csv"
    if program_file.exists():
        df = pd.read_csv(program_file)
        structure['PROGRAMS'] = {
            'columns': list(df.columns),
            'sample_data': df.iloc[0].to_dict() if len(df) > 0 else {},
            'dtypes': df.dtypes.to_dict()
        }
    
    # Analyser structures.csv
    structures_file = folder / "structures.csv"
    if structures_file.exists():
        df = pd.read_csv(structures_file)
        structure['STRUCTURES'] = {
            'columns': list(df.columns),
            'sample_data': df.iloc[0].to_dict() if len(df) > 0 else {},
            'dtypes': df.dtypes.to_dict()
        }
    
    # Analyser conditions.csv
    conditions_file = folder / "conditions.csv"
    if conditions_file.exists():
        df = pd.read_csv(conditions_file)
        structure['CONDITIONS'] = {
            'columns': list(df.columns),
            'sample_data': df.iloc[0].to_dict() if len(df) > 0 else {},
            'dtypes': df.dtypes.to_dict()
        }
    
    # Analyser exclusions.csv
    exclusions_file = folder / "exclusions.csv"
    if exclusions_file.exists():
        df = pd.read_csv(exclusions_file)
        structure['EXCLUSIONS'] = {
            'columns': list(df.columns),
            'sample_data': df.iloc[0].to_dict() if len(df) > 0 else {},
            'dtypes': df.dtypes.to_dict()
        }
    
    return structure

def pandas_to_snowflake_type(pandas_dtype, sample_value=None):
    """Convertit un type pandas en type Snowflake"""
    
    if pandas_dtype == 'object':
        # String par défaut, mais on peut être plus précis
        if sample_value is not None:
            if isinstance(sample_value, str):
                # Vérifier si c'est une date
                if sample_value and ('-' in sample_value or '/' in sample_value):
                    try:
                        pd.to_datetime(sample_value)
                        return 'TIMESTAMP_NTZ'
                    except:
                        pass
                # Vérifier si c'est un booléen
                if sample_value in ['True', 'False', 'true', 'false']:
                    return 'BOOLEAN'
        return 'STRING'
    elif pandas_dtype == 'int64':
        return 'NUMBER(38,0)'
    elif pandas_dtype == 'float64':
        return 'FLOAT'
    elif pandas_dtype == 'bool':
        return 'BOOLEAN'
    elif 'datetime' in str(pandas_dtype):
        return 'TIMESTAMP_NTZ'
    else:
        return 'STRING'

def generate_ddl(structure):
    """Génère le DDL Snowflake basé sur la structure des CSV"""
    
    ddl_statements = []
    
    for table_name, table_info in structure.items():
        columns = table_info['columns']
        sample_data = table_info['sample_data']
        dtypes = table_info['dtypes']
        
        # Commencer le CREATE TABLE
        ddl = f"CREATE TABLE {table_name} (\n"
        
        # Ajouter PROGRAM_ID comme première colonne (clé de liaison)
        if table_name != 'PROGRAMS':
            ddl += "  PROGRAM_ID             STRING       NOT NULL,\n"
        
        # Ajouter toutes les colonnes du CSV
        for i, col in enumerate(columns):
            pandas_dtype = dtypes.get(col, 'object')
            sample_value = sample_data.get(col)
            snowflake_type = pandas_to_snowflake_type(pandas_dtype, sample_value)
            
            # Déterminer si la colonne est NOT NULL
            not_null = "NOT NULL" if sample_value is not None and sample_value != "" else ""
            
            ddl += f"  {col:<30} {snowflake_type:<15} {not_null}"
            
            # Ajouter une virgule sauf pour la dernière colonne
            if i < len(columns) - 1 or table_name != 'PROGRAMS':
                ddl += ","
            ddl += "\n"
        
        # Ajouter les colonnes d'audit pour PROGRAMS
        if table_name == 'PROGRAMS':
            ddl += "  CREATED_AT             STRING,\n"
            ddl += "  UPDATED_AT             STRING"
        
        # Ajouter les contraintes de clé primaire
        ddl += "\n"
        if table_name == 'PROGRAMS':
            ddl += "  PRIMARY KEY (REINSURANCE_PROGRAM_ID)"
        elif table_name == 'STRUCTURES':
            ddl += "  PRIMARY KEY (PROGRAM_ID, INSPER_ID_PRE)"
        elif table_name == 'CONDITIONS':
            ddl += "  PRIMARY KEY (PROGRAM_ID, BUSCL_ID_PRE)"
        elif table_name == 'EXCLUSIONS':
            ddl += "  -- Pas de clé primaire définie (table de référence)"
        
        ddl += "\n);"
        
        ddl_statements.append((table_name, ddl))
    
    return ddl_statements

def main():
    """Fonction principale"""
    print("🔍 Analyse de la structure des CSV...")
    
    # Analyser la structure des CSV
    csv_folder = "examples/programs/aviation_axa_xl_2024"
    structure = analyze_csv_structure(csv_folder)
    
    print(f"✅ Structure analysée pour {len(structure)} tables")
    
    # Afficher le résumé
    for table_name, table_info in structure.items():
        print(f"\n📋 Table {table_name}:")
        print(f"   Colonnes: {len(table_info['columns'])}")
        print(f"   Colonnes: {', '.join(table_info['columns'][:5])}{'...' if len(table_info['columns']) > 5 else ''}")
    
    # Générer le DDL
    print(f"\n🏗️  Génération du DDL Snowflake...")
    ddl_statements = generate_ddl(structure)
    
    # Afficher le DDL généré
    for table_name, ddl in ddl_statements:
        print(f"\n📝 DDL pour {table_name}:")
        print("=" * 50)
        print(ddl)
        print("=" * 50)
    
    # Sauvegarder le DDL dans un fichier
    output_file = "scripts/generated_snowflake_ddl.sql"
    with open(output_file, 'w') as f:
        f.write("-- DDL généré automatiquement à partir de la structure des CSV\n")
        f.write("-- Date: " + pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S') + "\n\n")
        
        for table_name, ddl in ddl_statements:
            f.write(f"-- Table {table_name}\n")
            f.write(ddl)
            f.write("\n\n")
    
    print(f"\n💾 DDL sauvegardé dans: {output_file}")
    
    # Sauvegarder aussi la structure en JSON pour référence
    structure_file = "scripts/csv_structure_analysis.json"
    with open(structure_file, 'w') as f:
        json.dump(structure, f, indent=2, default=str)
    
    print(f"💾 Structure détaillée sauvegardée dans: {structure_file}")

if __name__ == "__main__":
    main()
