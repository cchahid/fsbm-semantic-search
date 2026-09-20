# FSBM NLP & Semantic Search Engine - Baseline Starter

This folder contains the core baseline code to run the pipeline from raw Scholar profiles to a searchable vector store.

---

## 1. Architecture et Étapes du Projet

Le projet se décompose en trois grandes phases techniques :

**Étape 1 : Web Scraping & Collecte de Données (Data Engineering)**
* **Cible :** Une liste prédéfinie de chercheurs de la FSBM.
* **Données à extraire par chercheur :** Informations du profil (Nom, département, métriques : h-index, i10-index, total citations) et liste des publications (Titre, auteurs, date de publication, revue/conférence, nombre de citations, et surtout l'abstract).
* **Livrable intermédiaire :** Un script gérant l'extraction des données et un export brut au format JSON (`scraper.py`).

**Étape 2 : Nettoyage et Prétraitement des Données (Data Cleaning)**
* **Gestion des anomalies :** Filtrage des articles sans résumé.
* **Prétraitement du texte :** Normalisation en minuscules, suppression des caractères spéciaux superflus et des balises HTML.
* **Livrable intermédiaire :** Un script produisant un dataset structuré et propre au format JSON et Parquet (`cleaner.py`).

**Étape 3 : Vectorisation (Embedding) et Cas d'Usage NLP**
* **Modèle d'embedding :** Utilisation d'un modèle (ex: `zembed-1` ou `all-MiniLM-L6-v2`) pour encoder les résumés d'articles nettoyés en vecteurs denses.
* **Mise en œuvre :** Stockage des vecteurs dans une base vectorielle (ChromaDB) et implémentation d'une recherche sémantique par similarité cosinus (`generate_vectors_and_index.py`).

---

## 2. Structure du Dataset Attendu

Les données extraites et nettoyées suivent un format standardisé hiérarchique. Voici le schéma JSON de sortie pour chaque profil de chercheur :

```json
[
  {
    "chercheur_id": "ID_GOOGLE_SCHOLAR",
    "nom_complet": "Nom du chercheur",
    "affiliation": "Faculté des Sciences Ben M'Sick...",
    "metriques": {
      "citations_totales": 150,
      "h_index": 10,
      "i10_index": 12
    },
    "articles": [
      {
        "article_id": "ID_UNIQUE_ARTICLE",
        "titre": "Titre de la publication",
        "auteurs": ["Auteur 1", "Auteur 2"],
        "date_publication": "2023",
        "journal": "Nom de la revue ou conférence",
        "citations": 25,
        "abstract": "Résumé original de l'article...",
        "abstract_clean": "résumé nettoyé normalisé sans caractères spéciaux..."
      }
    ]
  }
]