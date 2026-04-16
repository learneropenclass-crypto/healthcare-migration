# 🏥 Healthcare Dataset — Migration MongoDB avec Docker

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![MongoDB](https://img.shields.io/badge/MongoDB-6.0-green)](https://mongodb.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue)](https://docker.com)
[![GitHub](https://img.shields.io/badge/GitHub-learneropenclass--crypto-black)](https://github.com/learneropenclass-crypto/healthcare-migration)

Pipeline automatisé de migration du dataset healthcare (source Kaggle CSV) vers **MongoDB Atlas**,
conteneurisé avec **Docker** pour une portabilité et scalabilité maximales.

---

## 📋 Table des matières

1. [Présentation du projet](#-présentation-du-projet)
2. [Source des données](#-source-des-données)
3. [Architecture Docker & Réseau](#-architecture-docker--réseau)
4. [Pipeline de migration — 9 étapes](#-pipeline-de-migration--9-étapes)
5. [Schéma de la base de données](#-schéma-de-la-base-de-données)
6. [Authentification et rôles utilisateurs](#-authentification-et-rôles-utilisateurs)
7. [Prérequis](#-prérequis)
8. [Démarrage rapide — Nouveau utilisateur](#-démarrage-rapide--nouveau-utilisateur)
9. [Commandes Docker complètes](#-commandes-docker-complètes)
10. [Cas de tests et validation](#-cas-de-tests-et-validation)
11. [Résultats de migration](#-résultats-de-migration)
12. [Variables d'environnement](#-variables-denvironnement)
13. [Requêtes utiles](#-requêtes-utiles)
14. [Déploiement AWS](#-déploiement-aws)

---

## 🎯 Présentation du projet

Ce projet automatise la migration du dataset **healthcare_dataset** (55 500 documents patients)
depuis sa source CSV Kaggle vers **MongoDB Atlas**. Il inclut :

- **Conversion automatique CSV → JSON** avec typage des champs
- **Déduplication** par hash SHA-256 sur les champs métier clés
- **Script Python automatisé** — 9 étapes séquentielles
- **9 index optimisés** pour les requêtes analytiques
- **3 rôles utilisateurs** avec authentification SCRAM
- **Réseau Docker interne** pour la communication inter-conteneurs
- **Variables d'environnement** — aucun mot de passe en dur dans le code
- **Sécurisation** des credentials via `.env` (hors GitHub)

---

## 📦 Source des données

| Propriété           | Valeur                                  |
|---------------------|-----------------------------------------|
| **Source**          | Kaggle — Healthcare Dataset             |
| **Format original** | CSV (Comma-Separated Values)            |
| **Licence**         | CC0 — Domaine public                    |
| **Documents**       | 55 500 enregistrements patients         |
| **Attributs**       | 15 colonnes métier + 3 métadonnées      |
| **Taille CSV**      | ~22 MB                                  |
| **Conversion**      | CSV → JSON Lines (via `migrate.py`)     |

---

## 🏗 Architecture Docker & Réseau

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Compose                                │
│                                                                 │
│  ┌──────────────────┐   healthcare_network   ┌───────────────┐  │
│  │  mongo           │◄──────────────────────►│  migration    │  │
│  │  MongoDB 6.0     │     (bridge)           │  Python 3.11  │  │
│  │  Port 27017      │                        │  migrate.py   │  │
│  │  healthcheck ✓   │◄──────────────────────►│  demo.py      │  │
│  └──────────────────┘                        └───────────────┘  │
│           │                                          │           │
│    mongo_data (volume)                      ./data (volume bind) │
│    /data/db persistant                      healthcare_dataset   │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────────┐
              │      MongoDB Atlas         │
              │   (Production — Cloud)     │
              │   healthcare-dataset       │
              │   55 500 documents ✅      │
              │   9 index ✅               │
              └───────────────────────────┘
```

### Réseau inter-conteneurs

| Propriété     | Valeur                |
|---------------|-----------------------|
| **Nom**       | `healthcare_network`  |
| **Driver**    | `bridge`              |
| **Rôle**      | Communication sécurisée entre `mongo` et `migration` sans exposer les ports inutilement |

Le réseau `bridge` permet aux conteneurs de se parler par leur **nom de service** (`mongo`, `migration`)
sans avoir besoin d'adresses IP. Le service `migration` appelle `mongo` directement via `mongodb://mongo:27017/`.

### Volumes

| Volume        | Montage              | Rôle                              |
|---------------|----------------------|-----------------------------------|
| `mongo_data`  | `/data/db`           | Persistance des données MongoDB local |
| `./data`      | `/data` (read-only)  | Fichier source JSON pour l'import |

---

## 🔄 Pipeline de migration — 9 étapes

| Étape | Nom              | Fonction Python       | Description                          |
|-------|------------------|-----------------------|--------------------------------------|
| 1     | Connexion        | `connect()`           | Ping MongoDB + timeout 10s           |
| 2     | Idempotence      | `collection.drop()`   | Suppression avant re-migration       |
| 3     | Conv. CSV→JSON   | `csv_to_json()`       | Typage auto (int, float, str)        |
| 4     | Chargement JSON  | `load_json()`         | Tableau JSON ou JSON Lines           |
| 5     | Déduplication    | `deduplicate()`       | SHA-256 sur clé composée (4 champs)  |
| 6     | Métadonnées      | `add_metadata()`      | `_migrated_at`, `_schema_version`    |
| 7     | Batch Insert     | `insert_batches()`    | 500 docs/lot, `ordered=False`        |
| 8     | Index            | `create_indexes()`    | 9 index automatiques                 |
| 9     | Rapport          | `log.info(stats)`     | Durée, insérés, erreurs              |

---

## 🗄 Schéma de la base de données

**Base :** `healthcare-dataset` | **Collection :** `healthcare-dataset`

| Champ                | Type     | Requis | Exemple                    |
|----------------------|----------|--------|----------------------------|
| `_id`                | ObjectId | Auto   | `ObjectId("69d63a...")`    |
| `Name`               | String   | ✅     | `"CHrisTInA MARtinez"`     |
| `Age`                | Int      | ✅     | `20`                       |
| `Gender`             | String   | ✅     | `"Female"`                 |
| `Blood Type`         | String   | ❌     | `"A+"`                     |
| `Medical Condition`  | String   | ✅     | `"Cancer"`                 |
| `Date of Admission`  | String   | ✅     | `"2021-12-28"`             |
| `Discharge Date`     | String   | ❌     | `"2022-01-07"`             |
| `Doctor`             | String   | ❌     | `"Suzanne Thomas"`         |
| `Hospital`           | String   | ❌     | `"Powell Robinson..."`     |
| `Insurance Provider` | String   | ❌     | `"Cigna"`                  |
| `Billing Amount`     | Double   | ❌     | `45820.46`                 |
| `Room Number`        | Int      | ❌     | `277`                      |
| `Admission Type`     | String   | ❌     | `"Emergency"`              |
| `Medication`         | String   | ❌     | `"Paracetamol"`            |
| `Test Results`       | String   | ❌     | `"Inconclusive"`           |
| `_migrated_at`       | Date     | Auto   | `ISODate("2026-04-08...")`|
| `_schema_version`    | String   | Auto   | `"1.0"`                    |

### Index créés (9)

| Index                         | Type       | Objectif                        |
|-------------------------------|------------|---------------------------------|
| `Medical Condition`           | Ascendant  | Filtrage par pathologie         |
| `Age`                         | Ascendant  | Tranches d'âge                  |
| `Gender`                      | Ascendant  | Stats par genre                 |
| `Hospital`                    | Ascendant  | Par établissement               |
| `Doctor`                      | Ascendant  | Par médecin                     |
| `Insurance Provider`          | Ascendant  | Par assurance                   |
| `Test Results`                | Ascendant  | Par résultat                    |
| `Date of Admission`           | Descendant | Tri chronologique               |
| `Medical Condition` + `Age`   | Composé    | Analytique combinée             |

---

## 🔐 Authentification et rôles utilisateurs

**Mécanisme :** SCRAM-SHA-256 (local Docker) | SCRAM via TLS (MongoDB Atlas)

| Utilisateur   | Rôle MongoDB            | Droits                              | Usage                 |
|---------------|-------------------------|-------------------------------------|-----------------------|
| `admin`       | `root`                  | Accès total toutes bases            | Administration Docker |
| `data_reader` | `read`                  | Lecture seule `healthcare-dataset`  | Analystes, dashboards |
| `data_writer` | `readWrite`             | Lecture + écriture                  | Pipelines ETL         |
| `data_admin`  | `dbAdmin` + `readWrite` | Index, stats, schéma                | DBA, opérations       |

**Sécurité :**
- ✅ Mots de passe dans `.env` uniquement — jamais dans le code
- ✅ `.gitignore` protège `.env` et `data/`
- ✅ Variables d'environnement injectées dans Docker au runtime
- ✅ IP Whitelist activée sur MongoDB Atlas

---

## ✅ Prérequis

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé et lancé
- [Git](https://git-scm.com/) installé
- Compte [MongoDB Atlas](https://cloud.mongodb.com/) avec cluster actif

---

## 🚀 Démarrage rapide — Nouveau utilisateur

> **Aucun mot de passe à taper en dur.** Tout passe par le fichier `.env`.

### 1. Cloner le dépôt

```powershell
git clone https://github.com/learneropenclass-crypto/healthcare-migration.git
cd healthcare-migration
```

### 2. Configurer les variables d'environnement

```powershell
Copy-Item ".env.example" ".env"
notepad .env
```

Remplis uniquement ces valeurs dans `.env` :

```env
MONGO_ROOT_USER=admin
MONGO_ROOT_PASSWORD=TonMotDePasse
MONGO_URI=mongodb+srv://TON_USER:TON_MDP@cluster.mongodb.net/
READER_PASSWORD=TonReaderMDP
WRITER_PASSWORD=TonWriterMDP
DBADMIN_PASSWORD=TonAdminMDP
```

### 3. Placer le fichier de données

```powershell
mkdir data
Copy-Item "C:\chemin\vers\healthcare_dataset.json" "data\healthcare_dataset.json"
```

### 4. Lancer la stack complète

```powershell
docker compose up --build
```

C'est tout ! Docker va automatiquement :
- Démarrer MongoDB local sur le réseau `healthcare_network`
- Attendre que MongoDB soit healthy
- Lancer la migration vers Atlas
- Afficher le rapport final

---

## 🐳 Commandes Docker complètes

### Vérifier les conteneurs actifs
```powershell
docker ps
```

### Charger les données dans Atlas (mongoimport)
```powershell
docker run --rm `
  -v "C:\Users\ASF\healthcare-migration\data:/data" `
  mongo:6 mongoimport `
  --uri "${env:MONGO_URI}" `
  --collection "healthcare-dataset" `
  --type json --drop `
  --file /data/healthcare_dataset.json
```

### Vérifier la connexion Atlas
```powershell
docker run --rm mongo:6 mongosh "${env:MONGO_URI}healthcare-dataset" --eval "db.stats()"
```

### Lancer la démonstration des tests
```powershell
docker run --rm healthcare-migration python demo.py
```

### Lancer les cas de tests complets
```powershell
docker run --rm healthcare-migration python test_query.py
```

### Arrêter tous les conteneurs
```powershell
docker compose down
```

---

## 🧪 Cas de tests et validation

Le fichier `test_query.py` exécute **7 cas de tests** :

| Test | Description                        | Résultat attendu        | Statut  |
|------|------------------------------------|-------------------------|---------|
| 1    | Nombre total de documents          | 55 500                  | ✅ PASS |
| 2    | Structure d'un document            | 7 champs requis présents| ✅ PASS |
| 3    | Patients diabétiques > 60 ans      | Résultats > 0           | ✅ PASS |
| 4    | Top 5 conditions médicales         | 5 résultats             | ✅ PASS |
| 5    | Facturation moyenne par condition  | Valeurs numériques      | ✅ PASS |
| 6    | Types de champs (int, float)       | Age=int, Billing=float  | ✅ PASS |
| 7    | Index créés sur la collection      | ≥ 2 index               | ✅ PASS |

**Résultats réels (08/04/2026) :**
```
TOP 5 CONDITIONS MÉDICALES :
  Arthritis    : 9 308 patients
  Diabetes     : 9 304 patients
  Hypertension : 9 245 patients
  Obesity      : 9 231 patients
  Cancer       : 9 227 patients

PATIENTS DIABÉTIQUES > 60 ANS (extrait) :
  {'Name': 'connOR HANsEn',      'Age': 75, 'Hospital': 'Powers Miller, and Flores'}
  {'Name': 'NIcOlE LUcErO',      'Age': 70, 'Hospital': 'and Garcia Morris Cunningham,'}
  {'Name': 'SeaN jenniNGs',       'Age': 80, 'Hospital': 'Clark-Johnson'}
  {'Name': 'MR. TYler TAYLOR Phd','Age': 80, 'Hospital': 'Dean-Hawkins'}
  {'Name': 'heatHER mIller',      'Age': 76, 'Hospital': 'Powell Ward, and Mercado'}

FACTURATION MOYENNE :
  Obesity  : 25 805.97 $
  Diabetes : 25 638.41 $
  Asthma   : 25 635.25 $
```

---

## 📊 Résultats de migration

| Métrique              | Valeur         |
|-----------------------|----------------|
| Documents source      | 55 500         |
| Documents insérés     | 55 500         |
| Erreurs               | 0              |
| Doublons supprimés    | 0              |
| Index créés           | 9              |
| Durée totale          | ~202 secondes  |
| Taille fichier source | ~22 MB         |
| Dernière migration    | 08/04/2026     |

---

## ⚙️ Variables d'environnement

| Variable            | Défaut                                        | Description                      |
|---------------------|-----------------------------------------------|----------------------------------|
| `MONGO_ROOT_USER`   | `admin`                                       | Utilisateur root MongoDB local   |
| `MONGO_ROOT_PASSWORD`| `adminpassword`                              | Mot de passe root (à changer !)  |
| `MONGO_URI`         | `mongodb://admin:adminpassword@mongo:27017/`  | URI de connexion MongoDB         |
| `DB_NAME`           | `healthcare-dataset`                          | Nom de la base de données        |
| `COLL_NAME`         | `healthcare-dataset`                          | Nom de la collection             |
| `DATA_FILE`         | `/data/healthcare_dataset.json`               | Chemin du fichier JSON           |
| `BATCH_SIZE`        | `500`                                         | Taille des lots d'insertion      |
| `READER_PASSWORD`   | `ReaderPass123!`                              | Mot de passe data_reader         |
| `WRITER_PASSWORD`   | `WriterPass123!`                              | Mot de passe data_writer         |
| `DBADMIN_PASSWORD`  | `AdminPass123!`                               | Mot de passe data_admin          |

---

## 🔍 Requêtes utiles

```python
from pymongo import MongoClient
import os

client = MongoClient(os.getenv("MONGO_URI"))
col = client["healthcare-dataset"]["healthcare-dataset"]

# Nombre total de documents
col.count_documents({})  # → 55500

# Conditions médicales les plus fréquentes
list(col.aggregate([
    {"$group": {"_id": "$Medical Condition", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}},
    {"$limit": 5}
]))

# Patients diabétiques de plus de 60 ans
list(col.find(
    {"Medical Condition": "Diabetes", "Age": {"$gt": 60}},
    {"Name": 1, "Age": 1, "Hospital": 1, "_id": 0}
).limit(10))

# Facturation moyenne par condition
list(col.aggregate([
    {"$group": {"_id": "$Medical Condition", "avg_billing": {"$avg": "$Billing Amount"}}},
    {"$sort": {"avg_billing": -1}}
]))
```

---

## ☁️ Déploiement AWS

| Service                  | Rôle                                           |
|--------------------------|------------------------------------------------|
| **Amazon DocumentDB**    | Base MongoDB managée, compatible MongoDB 5.0   |
| **Amazon ECS + ECR**     | Déploiement des conteneurs Docker              |
| **Amazon S3**            | Stockage datasets CSV + backups MongoDB        |
| **AWS Secrets Manager**  | Remplacement du fichier `.env` en production   |

---

## 📁 Structure du projet

```
healthcare-migration/
│
├── migrate.py              # Script principal — 9 étapes
├── demo.py                 # Script de démonstration live
├── test_query.py           # 7 cas de tests automatiques
├── Dockerfile.migration    # Image Docker Python 3.11
├── docker-compose.yml      # Orchestration + réseau + volumes
├── init-mongo.js           # Init MongoDB local
├── requirements.txt        # pymongo[srv]==4.7.3
├── .env.example            # Template variables (sans secrets)
├── .gitignore              # Exclusions Git
├── README.md               # Documentation complète
└── data/                   # ⚠️ NON versionné
    └── healthcare_dataset.json
```

---

## 🔗 Liens utiles

- **Dépôt GitHub** : https://github.com/learneropenclass-crypto/healthcare-migration
- **MongoDB Atlas** : https://cloud.mongodb.com
- **Dataset Kaggle** : Healthcare Dataset (CC0)

---

## 📄 Licence

Projet réalisé dans le cadre d'une formation Data Engineering — DataSoluTech. Usage pédagogique.
