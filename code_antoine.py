import pandas as pd
import re
import unicodedata
from text_unidecode import unidecode
import chardet
import argparse
from pathlib import Path

# ===========================
# CONFIGURATION GLOBALE
# ===========================

LEGAL_FORMS = [
    "sa", "sas", "sasu", "sarl", "eurl", "sc", "scop", "sci", "snc", "sep",
    "selas", "selarl", "selafa", "scm", "inc", "corp", "co", "llc", "plc",
    "ltd", "gmbh", "ag", "bv", "nv", "oy", "ab", "as", "spa", "srl",
    "sa de cv", "pte ltd", "kk", "oyj", "aps"
]

CORPORATE_STOPWORDS = [
    "group", "holding", "international", "global", "solutions", "services",
    "technology", "technologies", "tech", "systems", "consulting",
    "partners", "investments", "capital", "industrie", "industries",
    "france", "europe", "company", "co", "societe"
]

ALIASES = {
    r"\bst\.?\b": "saint",
    r"\bste\.?\b": "sainte",
    r"\bsociete\b": "ste",
    r"\bcoy\b": "company",
}

# ===========================
# FONCTIONS UTILITAIRES
# ===========================

def detect_encoding(file_path):
    """Détecte automatiquement l’encodage d’un fichier texte."""
    with open(file_path, "rb") as f:
        rawdata = f.read(20000)
    return chardet.detect(rawdata)["encoding"] or "utf-8"

def strip_accents(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join([c for c in text if not unicodedata.combining(c)])
    return unidecode(text)  # œ→oe, æ→ae

def clean_punctuation(text: str) -> str:
    text = text.lower()
    text = text.replace("&", " and ").replace("+", " plus ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def remove_legal_forms(text: str) -> str:
    pattern = r"\b(" + "|".join(re.escape(f) for f in LEGAL_FORMS) + r")\b"
    return re.sub(pattern, " ", text)

def apply_aliases(text: str) -> str:
    for k, v in ALIASES.items():
        text = re.sub(k, v, text)
    return text

def remove_corporate_stopwords(tokens):
    return [t for t in tokens if t not in CORPORATE_STOPWORDS and len(t) > 1]

def normalize_name(name: str) -> str:
    if not isinstance(name, str) or not name.strip():
        return ""
    name = strip_accents(name)
    name = clean_punctuation(name)
    name = remove_legal_forms(name)
    name = apply_aliases(name)

    tokens = name.split()
    tokens = remove_corporate_stopwords(tokens)
    tokens = sorted(set(tokens))  # tri + déduplication

    normalized = " ".join(tokens).strip()
    return normalized

# ===========================
# PIPELINE PRINCIPAL
# ===========================

def prenormaliser_csv(fichier_entree, colonne_nom="nom", fichier_sortie=None):
    fichier = Path(fichier_entree)
    if not fichier.exists():
        raise FileNotFoundError(f"❌ Fichier non trouvé : {fichier_entree}")

    # Détection encodage
    encoding = detect_encoding(fichier)
    print(f"📄 Encodage détecté : {encoding}")

    # Lecture CSV robuste (auto-détection du séparateur)
    try:
        df = pd.read_csv(fichier, encoding=encoding, sep=None, engine="python")
    except Exception as e:
        print("⚠️ Erreur lecture CSV, tentative avec ';' comme séparateur.")
        df = pd.read_csv(fichier, encoding=encoding, sep=';')

    # Vérification de la colonne
    if colonne_nom not in df.columns:
        raise ValueError(f"❌ Colonne '{colonne_nom}' absente. Colonnes dispo : {list(df.columns)}")

    # Application normalisation
    df["normalized_key"] = df[colonne_nom].apply(normalize_name)

    # Détermination fichier de sortie
    if fichier_sortie is None:
        fichier_sortie = fichier.with_name(f"{fichier.stem}_normalized.csv")

    df.to_csv(fichier_sortie, index=False, encoding="utf-8")
    print(f"✅ Pré-normalisation terminée.\n📁 Fichier exporté : {fichier_sortie.resolve()}")
    return df


# ===========================
# LIGNE DE COMMANDE
# ===========================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pré-normalisation de noms d’assurés à partir d’un CSV.")
    parser.add_argument("fichier_csv", help="Chemin vers le fichier CSV (Windows ou Linux path)")
    parser.add_argument("--colonne", default="nom", help="Nom de la colonne contenant les noms (par défaut : 'nom')")
    parser.add_argument("--sortie", help="Chemin du fichier de sortie CSV (optionnel)")
    args = parser.parse_args()

    prenormaliser_csv(args.fichier_csv, colonne_nom=args.colonne, fichier_sortie=args.sortie)
 
Blocking
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02_blocking.py — Étape 3 du pipeline : Blocking (réduction des comparaisons)

Entrée :
    - Fichier CSV issu de la pré-normalisation, avec au minimum les colonnes :
        id, nom, normalized_key
Sortie :
    - Fichier CSV contenant les paires de candidats (id1, id2)

Exemple :
    python3 02_blocking.py "assures_normalized.csv" --sortie "blocking_pairs.csv"
"""

import argparse
import pandas as pd
import re
from collections import defaultdict
from datasketch import MinHash, MinHashLSH
import jellyfish
from itertools import combinations
from tqdm import tqdm

# ---------- Fonctions utilitaires ----------

def phonetic_key(name: str) -> str:
    """Construit une clé phonétique simple en appliquant Double Metaphone à chaque token."""
    tokens = re.findall(r'\w+', name)
    phonetics = []
    for t in tokens:
        try:
            p1, p2 = jellyfish.double_metaphone(t)
            phonetics.append(p1 or p2 or t)
        except Exception:
            phonetics.append(t)
    return "_".join(sorted(set(phonetics)))


def trigram_shingles(s: str):
    """Retourne les trigrammes d'une chaîne."""
    s = re.sub(r'\s+', ' ', s.strip())
    return {s[i:i+3] for i in range(len(s)-2)} if len(s) >= 3 else {s}


def lsh_bucket(name: str, lsh_model, num_perm=64):
    """Retourne le bucket LSH associé à un nom."""
    shingles = trigram_shingles(name)
    m = MinHash(num_perm=num_perm)
    for sh in shingles:
        m.update(sh.encode('utf8'))
    return m, lsh_model.query(m)


# ---------- Script principal ----------

def main():
    parser = argparse.ArgumentParser(description="Étape 3 : Blocking (réduction des comparaisons)")
    parser.add_argument("fichier_csv", help="Fichier CSV issu de la normalisation (avec normalized_key)")
    parser.add_argument("--sortie", default="blocking_pairs.csv", help="Nom du fichier CSV de sortie")
    parser.add_argument("--colonne", default="normalized_key", help="Nom de la colonne de clé normalisée")
    parser.add_argument("--id_col", default=None, help="Colonne identifiant unique (sinon index utilisé)")
    args = parser.parse_args()

    print("📥 Lecture du fichier :", args.fichier_csv)
    df = pd.read_csv(args.fichier_csv)
    if args.id_col and args.id_col in df.columns:
        ids = df[args.id_col].astype(str).tolist()
    else:
        df = df.reset_index().rename(columns={"index": "id"})
        ids = df["id"].astype(str).tolist()

    noms = df[args.colonne].fillna("").astype(str).tolist()

    print("🔹 Génération des clés de blocking...")
    buckets = defaultdict(list)

    # 1) Clé normalisée exacte
    for i, key in enumerate(noms):
        if key.strip():
            buckets[("A", key)].append(ids[i])

    # 2) Clé phonétique
    for i, name in enumerate(noms):
        key_phon = phonetic_key(name)
        buckets[("B", key_phon)].append(ids[i])

    # 3) Clé LSH (MinHash sur trigrammes)
    print("   Initialisation du LSH pour trigrammes...")
    num_perm = 64
    lsh = MinHashLSH(threshold=0.8, num_perm=num_perm)
    minhashes = {}
    for i, name in enumerate(tqdm(noms, desc="   Construction MinHash")):
        shingles = trigram_shingles(name)
        m = MinHash(num_perm=num_perm)
        for sh in shingles:
            m.update(sh.encode("utf8"))
        minhashes[ids[i]] = m
        lsh.insert(ids[i], m)

    print("   Attribution des buckets LSH...")
    for i, id_ in enumerate(ids):
        neighbors = lsh.query(minhashes[id_])
        if len(neighbors) > 1:
            buckets[("C", "lsh_"+id_)].extend(neighbors)

    # ---------- Génération des paires ----------
    print("🔹 Construction des paires candidates...")
    candidates = set()
    for bkey, id_list in tqdm(buckets.items(), desc="   Buckets"):
        if len(id_list) < 2:
            continue
        for id1, id2 in combinations(sorted(id_list), 2):
            candidates.add(tuple(sorted((id1, id2))))

    print(f"✅ {len(candidates):,} paires candidates générées")

    # ---------- Sauvegarde ----------
    out_df = pd.DataFrame(list(candidates), columns=["id1", "id2"])
    out_df.to_csv(args.sortie, index=False)
    print("💾 Fichier de sortie écrit :", args.sortie)


if __name__ == "__main__":
    main()
 
Pairing
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
03_scoring_pairs_chunked.py — Étape 4 : Scoring des paires candidates
Version corrigée : TF-IDF calculé par chunks pour éviter OOM
"""

import argparse
import pandas as pd
import numpy as np
from rapidfuzz import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm

# ---------------------------
# Paramètres généraux
# ---------------------------
AUTO_MERGE_THRESHOLD = 0.92
HOLD_OUT_THRESHOLD = 0.84
CHUNK_SIZE = 50000  # nombre de paires par chunk TF-IDF

# ---------------------------
# Fonctions utilitaires
# ---------------------------
def jaccard_token_set(a, b):
    set_a, set_b = set(a.split()), set(b.split())
    inter = len(set_a & set_b)
    union = len(set_a | set_b)
    return inter / union if union > 0 else 0

def jaro_winkler(a, b):
    return fuzz.WRatio(a, b) / 100.0

def decision_from_score(score):
    if score >= AUTO_MERGE_THRESHOLD:
        return "auto_merge"
    elif score >= HOLD_OUT_THRESHOLD:
        return "hold_out"
    else:
        return "reject"

# ---------------------------
# TF-IDF chunké
# ---------------------------
def compute_tfidf_chunked(df_pairs, df_norm, col_key, chunk_size=CHUNK_SIZE):
    vect = TfidfVectorizer(analyzer='word', token_pattern=r'\w+')

    print("🔹 Fit TF-IDF sur tous les noms normalisés...")
    # Corriger ici : remplacer les NaN par des chaînes vides
    names_list = df_norm[col_key].fillna("").tolist()
    tfidf_matrix = vect.fit_transform(names_list)

    id_to_idx = {str(id_): i for i, id_ in enumerate(df_norm['id'].tolist())}

    tfidf_scores = []

    print("🔹 Calcul TF-IDF cosine par chunks...")
    for start in tqdm(range(0, len(df_pairs), chunk_size)):
        end = min(start + chunk_size, len(df_pairs))
        chunk = df_pairs.iloc[start:end]

        chunk_scores = []
        for n1_id, n2_id in zip(chunk['id1'], chunk['id2']):
            idx1 = id_to_idx.get(n1_id, None)
            idx2 = id_to_idx.get(n2_id, None)
            if idx1 is None or idx2 is None:
                chunk_scores.append(0.0)
            else:
                sim = cosine_similarity(tfidf_matrix[idx1], tfidf_matrix[idx2])[0][0]
                chunk_scores.append(sim)
        tfidf_scores.extend(chunk_scores)

    return np.array(tfidf_scores)

# ---------------------------
# Script principal
# ---------------------------
def main():
    parser = argparse.ArgumentParser(description="Étape 4 : Scoring des paires")
    parser.add_argument("--normalized_csv", required=True, help="CSV normalisé (id + normalized_key)")
    parser.add_argument("--pairs_csv", required=True, help="CSV des paires candidates (id1,id2)")
    parser.add_argument("--sortie", default="pair_scores.csv", help="Nom du CSV de sortie")
    parser.add_argument("--id_col", default="id", help="Nom de la colonne identifiant unique")
    parser.add_argument("--col_key", default="normalized_key", help="Nom de la colonne normalisée")
    args = parser.parse_args()

    print("📥 Lecture des fichiers...")
    df_norm = pd.read_csv(args.normalized_csv, sep=';', engine='python')
    df_pairs = pd.read_csv(args.pairs_csv)

    df_norm[args.id_col] = df_norm[args.id_col].astype(str)
    df_pairs["id1"] = df_pairs["id1"].astype(str)
    df_pairs["id2"] = df_pairs["id2"].astype(str)

    d_map = df_norm.set_index(args.id_col)[args.col_key].to_dict()
    df_pairs["name1"] = df_pairs["id1"].map(d_map).fillna("")
    df_pairs["name2"] = df_pairs["id2"].map(d_map).fillna("")

    print("🔹 Calcul des scores de similarité (A : règles rapides)...")
    rule_scores = []
    for _, row in tqdm(df_pairs.iterrows(), total=len(df_pairs)):
        n1, n2 = row["name1"], row["name2"]
        if n1 == n2:
            s = 1.0
        else:
            s = max(jaccard_token_set(n1, n2), jaro_winkler(n1, n2))
        rule_scores.append(s)
    df_pairs["rule_score"] = rule_scores

    print("🔹 Calcul des scores TF-IDF cosine (B)...")
    df_pairs["tfidf_score"] = compute_tfidf_chunked(df_pairs, df_norm, args.col_key)

    print("🔹 Calcul du score final et décision...")
    df_pairs["final_score"] = 0.6 * df_pairs["rule_score"] + 0.4 * df_pairs["tfidf_score"]
    df_pairs["decision"] = df_pairs["final_score"].apply(decision_from_score)

    print("✅ Scores calculés. Sauvegarde...")
    df_pairs[["id1", "id2", "name1", "name2", "rule_score", "tfidf_score", "final_score", "decision"]].to_csv(
        args.sortie, index=False, sep=';'
    )
    print("💾 Fichier écrit :", args.sortie)
    print(df_pairs["decision"].value_counts())

if __name__ == "__main__":
    main()
 
Union
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
05_clustering_union_canonical.py — Étape 5 : Clustering des paires candidates + Canonicalisation

Entrées :
    - CSV avec paires et scores (id1, id2, final_score, decision)
      issu de l'étape 4
    - CSV normalisé (avec id et normalized_key) pour définir le nom canonique

Sortie :
    - CSV des clusters : cluster_id, canonical_name, members (liste d'IDs)
"""

import argparse
import pandas as pd
from tqdm import tqdm
from collections import Counter

# ---------------------------
# Union-Find pour composantes connexes
# ---------------------------

class UnionFind:
    def __init__(self):
        self.parent = dict()

    def find(self, x):
        if x not in self.parent:
            self.parent[x] = x
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px != py:
            self.parent[py] = px

    def clusters(self):
        d = dict()
        for node in self.parent:
            root = self.find(node)
            d.setdefault(root, []).append(node)
        return d

# ---------------------------
# Script principal
# ---------------------------

def main():
    parser = argparse.ArgumentParser(description="Étape 5 : Clustering & Union + Nom canonique")
    parser.add_argument("--pairs_csv", required=True, help="CSV avec paires et scores")
    parser.add_argument("--normalized_csv", required=True, help="CSV normalisé (id, normalized_key)")
    parser.add_argument("--sortie", default="clusters.csv", help="Nom du CSV de sortie")
    parser.add_argument("--merge_threshold", type=float, default=0.92,
                        help="Seuil pour fusion automatique des paires")
    parser.add_argument("--id_col", default="id", help="Colonne identifiant unique dans normalized CSV")
    parser.add_argument("--col_key", default="normalized_key", help="Colonne normalisée pour canonical name")
    args = parser.parse_args()

    print("📥 Lecture des fichiers...")
    df_pairs = pd.read_csv(args.pairs_csv, sep=',', engine='python')
    df_norm = pd.read_csv(args.normalized_csv, sep=';', engine='python')

    # Créer dictionnaire id -> normalized_key
    d_map = df_norm.set_index(args.id_col)[args.col_key].to_dict()

    print(f"🔹 Total de paires : {len(df_pairs)}")

    # Filtrer uniquement les paires "auto_merge" ou score >= seuil
    df_merge = df_pairs[df_pairs["final_score"] >= args.merge_threshold]
    print(f"🔹 Paires retenues pour clustering : {len(df_merge)}")

    # ---------------------------
    # Union-Find
    # ---------------------------
    print("🔹 Construction des clusters via Union-Find...")
    uf = UnionFind()
    for _, row in tqdm(df_merge.iterrows(), total=len(df_merge)):
        uf.union(str(row["id1"]), str(row["id2"]))

    clusters = uf.clusters()
    print(f"✅ Nombre de clusters détectés : {len(clusters)}")

    # ---------------------------
    # Préparer CSV de sortie avec canonical name
    # ---------------------------
    print("🔹 Détermination du nom canonique pour chaque cluster...")
    cluster_list = []
    for i, (root, members) in enumerate(clusters.items(), start=1):
        # Récupérer les normalized_key des membres
        keys = [d_map.get(m, "") for m in members if d_map.get(m)]
        if keys:
            # Compter les occurrences
            c = Counter(keys)
            max_count = max(c.values())
            # Choisir le(s) plus fréquent(s)
            candidates = [k for k, v in c.items() if v == max_count]
            # Si plusieurs, choisir le plus long informatif
            canonical_name = max(candidates, key=len)
        else:
            canonical_name = ""

        cluster_list.append({
            "cluster_id": i,
            "canonical_name": canonical_name,
            "members": "|".join(sorted(members))
        })

    df_clusters = pd.DataFrame(cluster_list)
    df_clusters.to_csv(args.sortie, index=False)
    print(f"💾 Fichier de clusters écrit : {args.sortie}")

if __name__ == "__main__":
    main()