# 🏥 Healthcare Dataset — Migration MongoDB avec Docker

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![MongoDB](https://img.shields.io/badge/MongoDB-6.0-green)](https://mongodb.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue)](https://docker.com)

Pipeline automatisé de migration du dataset healthcare vers **MongoDB Atlas** (ou MongoDB local), conteneurisé avec **Docker** pour une portabilité et scalabilité maximales.

---

## 📋 Table des matières

1. [Présentation du projet](#-présentation-du-projet)
2. [Architecture](#-architecture)
3. [Schéma de la base de données](#-schéma-de-la-base-de-données)
4. [Authentification et rôles utilisateurs](#-authentification-et-rôles-utilisateurs)
5. [Prérequis](#-prérequis)
6. [Installation et démarrage rapide](#-installation-et-démarrage-rapide)
7. [Utilisation avec MongoDB Atlas](#-utilisation-avec-mongodb-atlas)
8. [Structure du projet](#-structure-du-projet)
9. [Variables d'environnement](#-variables-denvironnement)
10. [Requêtes utiles](#-requêtes-utiles)

---

## 🎯 Présentation du projet

Ce projet automatise la migration du dataset **healthcare_dataset.json** (55 500 documents) vers MongoDB. Il inclut :

- **Script de migration Python** avec insertion par lots, gestion des erreurs et logging
- **Validation du schéma** JSON Schema intégrée à MongoDB
- **Index optimisés** pour les requêtes analytiques
- **Gestion des rôles** utilisateurs (lecteur, écrivain, administrateur)
- **Conteneurisation Docker** complète (MongoDB local + script de migration)
- **Support MongoDB Atlas** pour la production

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                        │
│                                                         │
│  ┌──────────────────┐      ┌──────────────────────────┐ │
│  │  mongo (service) │◄────►│  migration (service)     │ │
│  │  MongoDB 6.0     │      │  Python 3.11             │ │
│  │  Port 27017      │      │  migrate.py              │ │
│  └──────────────────┘      └──────────────────────────┘ │
│           │                           │                  │
│    mongo_data (volume)         /data (volume)            │
│                                healthcare_dataset.json   │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │   MongoDB Atlas       │
            │   (Production)        │
            │   healthcare-dataset  │
            └───────────────────────┘
```

**Flux de migration :**

```
healthcare_dataset.json
        │
        ▼
  Chargement JSON
  (tableau ou JSON Lines)
        │
        ▼
  Enrichissement
  (_migrated_at, _schema_version)
        │
        ▼
  Insertion par lots (500 docs)
        │
        ▼
  Création des index
        │
        ▼
  Rapport de migration
```

---

## 🗄 Schéma de la base de données

### Base de données : `healthcare-dataset`
### Collection : `healthcare-dataset`

| Champ               | Type     | Requis | Description                          | Exemple                        |
|---------------------|----------|--------|--------------------------------------|--------------------------------|
| `_id`               | ObjectId | Auto   | Identifiant unique MongoDB           | `ObjectId("69cec7d5...")`      |
| `Name`              | String   | ✅     | Nom du patient                       | `"andrEw waTtS"`               |
| `Age`               | Int      | ✅     | Âge du patient (0–120)               | `28`                           |
| `Gender`            | String   | ✅     | Genre (Male / Female / Other)        | `"Female"`                     |
| `Blood Type`        | String   | ❌     | Groupe sanguin                       | `"O+"`                         |
| `Medical Condition` | String   | ✅     | Condition médicale diagnostiquée     | `"Diabetes"`                   |
| `Date of Admission` | String   | ✅     | Date d'admission (YYYY-MM-DD)        | `"2020-11-18"`                 |
| `Discharge Date`    | String   | ❌     | Date de sortie (YYYY-MM-DD)          | `"2020-12-18"`                 |
| `Doctor`            | String   | ❌     | Médecin responsable                  | `"Kevin Wells"`                |
| `Hospital`          | String   | ❌     | Établissement de soin                | `"Hernandez Rogers and Vang"`  |
| `Insurance Provider`| String   | ❌     | Assurance maladie                    | `"Medicare"`                   |
| `Billing Amount`    | Double   | ❌     | Montant facturé (USD, ≥ 0)           | `37909.78`                     |
| `Room Number`       | Int      | ❌     | Numéro de chambre (≥ 1)              | `450`                          |
| `Admission Type`    | String   | ❌     | Type d'admission                     | `"Elective"`                   |
| `Medication`        | String   | ❌     | Médicament prescrit                  | `"Ibuprofen"`                  |
| `Test Results`      | String   | ❌     | Résultat des tests                   | `"Abnormal"`                   |
| `_migrated_at`      | Date     | Auto   | Horodatage de migration              | `ISODate("2026-04-02...")`     |
| `_schema_version`   | String   | Auto   | Version du schéma                    | `"1.0"`                        |

### Valeurs énumérées

| Champ            | Valeurs autorisées                        |
|------------------|-------------------------------------------|
| `Gender`         | `Male`, `Female`, `Other`                 |
| `Admission Type` | `Elective`, `Emergency`, `Urgent`         |
| `Test Results`   | `Normal`, `Abnormal`, `Inconclusive`      |

### Index créés

| Index                             | Type     | Objectif                              |
|-----------------------------------|----------|---------------------------------------|
| `Medical Condition`               | Ascendant | Filtrage par pathologie              |
| `Age`                             | Ascendant | Tranches d'âge                       |
| `Gender`                          | Ascendant | Statistiques par genre               |
| `Hospital`                        | Ascendant | Recherche par établissement          |
| `Doctor`                          | Ascendant | Recherche par médecin                |
| `Insurance Provider`              | Ascendant | Filtrage par assurance               |
| `Test Results`                    | Ascendant | Filtrage par résultat                |
| `Date of Admission`               | Descendant| Tri chronologique                    |
| `Medical Condition` + `Age`       | Composé  | Requêtes analytiques combinées       |

---

## 🔐 Authentification et rôles utilisateurs

### Système d'authentification

MongoDB utilise le mécanisme **SCRAM-SHA-256** (par défaut) pour l'authentification locale, et **SCRAM** via TLS pour MongoDB Atlas. Chaque utilisateur est isolé dans la base `healthcare-dataset`.

### Rôles créés

| Utilisateur    | Rôle MongoDB  | Droits                              | Usage                          |
|----------------|---------------|-------------------------------------|--------------------------------|
| `admin`        | `root`        | Accès total à toutes les bases      | Administration système         |
| `data_reader`  | `read`        | Lecture seule sur `healthcare-dataset` | Analystes, dashboards       |
| `data_writer`  | `readWrite`   | Lecture + écriture                  | Pipelines ETL, ingestion       |
| `data_admin`   | `dbAdmin` + `readWrite` | Gestion des index, stats  | DBA, ops                       |

### Exemple de connexion par rôle

```python
# Analyste (lecture seule)
client = MongoClient(
    "mongodb+srv://data_reader:ReaderPass123!@cluster.mongodb.net/healthcare-dataset"
)

# Pipeline ETL (écriture)
client = MongoClient(
    "mongodb+srv://data_writer:WriterPass123!@cluster.mongodb.net/healthcare-dataset"
)
```

### Bonnes pratiques de sécurité

- Les mots de passe sont définis via **variables d'environnement** (fichier `.env`)
- Le fichier `.env` est exclu de Git via `.gitignore`
- En production, utilisez **MongoDB Atlas** avec IP Whitelist
- Activez l'**audit logging** Atlas pour tracer les accès

---

## ✅ Prérequis

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé et lancé
- [Git](https://git-scm.com/) pour versionner le projet
- Un compte [MongoDB Atlas](https://cloud.mongodb.com/) (pour la production)

---

## 🚀 Installation et démarrage rapide

### 1. Cloner le dépôt

```bash
git clone https://github.com/TON_USERNAME/healthcare-migration.git
cd healthcare-migration
```

### 2. Configurer les variables d'environnement

```bash
cp .env.example .env
# Édite .env avec tes valeurs (URI Atlas, mots de passe...)
```

### 3. Placer le fichier de données

```bash
mkdir data
cp /chemin/vers/healthcare_dataset.json data/
```

### 4. Lancer la migration (MongoDB local)

```bash
docker compose up --build
```

### 5. Lancer la migration vers Atlas uniquement

```bash
# Dans .env, configure MONGO_URI avec ton URI Atlas
docker compose run --rm migration
```

---

## ☁️ Utilisation avec MongoDB Atlas

1. Crée un cluster sur [cloud.mongodb.com](https://cloud.mongodb.com)
2. Crée un utilisateur Database Access avec mot de passe
3. Autorise ton IP dans Network Access
4. Copie l'URI de connexion dans `.env` :

```
MONGO_URI=mongodb+srv://monuser:monpassword@cluster.mongodb.net/
```

5. Lance la migration :

```bash
docker compose run --rm migration
```

---

## 📁 Structure du projet

```
healthcare-migration/
│
├── migrate.py              # Script principal de migration
├── docker-compose.yml      # Orchestration des services
├── Dockerfile.migration    # Image Docker du script Python
├── init-mongo.js           # Initialisation MongoDB local (rôles + schéma)
├── requirements.txt        # Dépendances Python
├── .env.example            # Template des variables d'environnement
├── .gitignore              # Fichiers exclus de Git
├── README.md               # Documentation
└── data/                   # (non versionné) fichiers de données
    └── healthcare_dataset.json
```

---

## ⚙️ Variables d'environnement

| Variable           | Défaut                                      | Description                     |
|--------------------|---------------------------------------------|---------------------------------|
| `MONGO_URI`        | `mongodb://admin:adminpassword@mongo:27017/`| URI de connexion MongoDB        |
| `DB_NAME`          | `healthcare-dataset`                        | Nom de la base de données       |
| `COLL_NAME`        | `healthcare-dataset`                        | Nom de la collection            |
| `DATA_FILE`        | `/data/healthcare_dataset.json`             | Chemin du fichier source        |
| `BATCH_SIZE`       | `500`                                       | Taille des lots d'insertion     |
| `READER_PASSWORD`  | `ReaderPass123!`                            | Mot de passe data_reader        |
| `WRITER_PASSWORD`  | `WriterPass123!`                            | Mot de passe data_writer        |
| `DBADMIN_PASSWORD` | `AdminPass123!`                             | Mot de passe data_admin         |

---

## 🔍 Requêtes utiles

```python
from pymongo import MongoClient

client = MongoClient("mongodb+srv://data_reader:ReaderPass123!@...")
col = client["healthcare-dataset"]["healthcare-dataset"]

# Nombre total de documents
col.count_documents({})

# Conditions médicales les plus fréquentes
list(col.aggregate([
    {"$group": {"_id": "$Medical Condition", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}},
    {"$limit": 5}
]))

# Facturation moyenne par condition
list(col.aggregate([
    {"$group": {
        "_id": "$Medical Condition",
        "avg_billing": {"$avg": "$Billing Amount"}
    }},
    {"$sort": {"avg_billing": -1}}
]))

# Patients diabétiques de plus de 60 ans
list(col.find(
    {"Medical Condition": "Diabetes", "Age": {"$gt": 60}},
    {"Name": 1, "Age": 1, "Hospital": 1, "_id": 0}
).limit(10))
```

---

## 📄 Licence

Projet réalisé dans le cadre d'une formation Data Engineering. Usage pédagogique.
