# 🏢 Reinsurance Program Analyzer - Application Streamlit

## 🚀 Lancement de l'application

Pour démarrer l'application Streamlit, utilisez la commande suivante :

```bash
uv run streamlit run app/main.py
```

L'application s'ouvrira automatiquement dans votre navigateur à l'adresse `http://localhost:8501`

## 📋 Fonctionnalités

### 🏠 Page d'accueil
- Vue d'ensemble des fonctionnalités de l'application
- Guide rapide d'utilisation

### 📊 Analyse
- **Upload de fichiers**: Programme Excel + Bordereau CSV
- **Métriques globales**: Exposition totale, nombre de polices, structures
- **Configuration du programme**: Visualisation détaillée de la configuration
- **Résultats par police**: Tableau interactif avec toutes les polices
- **Détails par assuré**: Vue détaillée de l'application des structures
- **Export**: Téléchargement des résultats au format CSV

### 📖 Guide
- Documentation sur les formats de fichiers
- Types de structures supportées
- Conseils d'utilisation

## 🎨 Fonctionnalités visuelles

- **Design moderne** avec gradient coloré
- **Métriques en temps réel** pour suivre les cessions et rétentions
- **Tableaux interactifs** pour explorer les résultats
- **Expandeurs** pour les détails des structures
- **Export facile** des résultats en CSV

## 📂 Exemples de fichiers

Vous pouvez tester l'application avec les fichiers d'exemple du projet :

- **Programme**: `examples/programs/aviation_axa_xl_2024.xlsx`
- **Bordereau**: `examples/bordereaux/aviation/bordereau_aviation_axa_xl.csv`

## 🔧 Configuration

L'application utilise automatiquement les modules du projet :
- `src.loaders`: Pour charger les programmes et bordereaux
- `src.engine`: Pour appliquer les programmes
- `src.domain`: Pour les modèles de données

Aucune configuration supplémentaire n'est nécessaire.

