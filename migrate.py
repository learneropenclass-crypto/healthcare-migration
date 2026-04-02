"""
Healthcare Dataset Migration Script
Automatise la migration du dataset healthcare vers MongoDB Atlas
"""

import os
import json
import logging
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import BulkWriteError, ConnectionFailure

# ─── Configuration du logging ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("migration.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ─── Variables d'environnement ───────────────────────────────────────────────
MONGO_URI  = os.getenv("MONGO_URI", "mongodb://admin:adminpassword@mongo:27017/")
DB_NAME    = os.getenv("DB_NAME",   "healthcare-dataset")
COLL_NAME  = os.getenv("COLL_NAME", "healthcare-dataset")
DATA_FILE  = os.getenv("DATA_FILE", "/data/healthcare_dataset.json")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "500"))


def connect(uri: str) -> MongoClient:
    """Connexion à MongoDB avec retry."""
    log.info("Connexion à MongoDB : %s", uri)
    client = MongoClient(uri, serverSelectionTimeoutMS=10_000)
    client.admin.command("ping")
    log.info("Connexion réussie ✓")
    return client


def create_roles(client: MongoClient) -> None:
    """Crée les rôles utilisateurs dans la base healthcare-dataset."""
    db = client[DB_NAME]
    admin_db = client["admin"]

    users = [
        {
            "user": "data_reader",
            "pwd":  os.getenv("READER_PASSWORD", "ReaderPass123!"),
            "roles": [{"role": "read", "db": DB_NAME}],
            "customData": {"description": "Lecture seule – analystes"}
        },
        {
            "user": "data_writer",
            "pwd":  os.getenv("WRITER_PASSWORD", "WriterPass123!"),
            "roles": [{"role": "readWrite", "db": DB_NAME}],
            "customData": {"description": "Lecture/écriture – ETL"}
        },
        {
            "user": "data_admin",
            "pwd":  os.getenv("DBADMIN_PASSWORD", "AdminPass123!"),
            "roles": [{"role": "dbAdmin", "db": DB_NAME},
                      {"role": "readWrite", "db": DB_NAME}],
            "customData": {"description": "Administrateur base de données"}
        },
    ]

    for u in users:
        try:
            db.command("createUser", u["user"],
                       pwd=u["pwd"], roles=u["roles"],
                       customData=u.get("customData", {}))
            log.info("Utilisateur créé : %s", u["user"])
        except Exception as e:
            if "already exists" in str(e):
                log.warning("Utilisateur déjà existant : %s", u["user"])
            else:
                log.error("Erreur création utilisateur %s : %s", u["user"], e)


def create_indexes(collection) -> None:
    """Crée les index pour optimiser les requêtes."""
    indexes = [
        ([("Medical Condition", ASCENDING)], {}),
        ([("Age", ASCENDING)],               {}),
        ([("Gender", ASCENDING)],            {}),
        ([("Hospital", ASCENDING)],          {}),
        ([("Doctor", ASCENDING)],            {}),
        ([("Insurance Provider", ASCENDING)],{}),
        ([("Test Results", ASCENDING)],      {}),
        ([("Date of Admission", DESCENDING)],{}),
        ([("Medical Condition", ASCENDING),
          ("Age", ASCENDING)],               {"name": "condition_age"}),
    ]
    for keys, opts in indexes:
        collection.create_index(keys, **opts)
        log.info("Index créé : %s", keys)


def load_json(path: str) -> list:
    """Charge le fichier JSON (tableau ou JSON Lines)."""
    log.info("Chargement du fichier : %s", path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if content.startswith("["):
        data = json.loads(content)
    else:
        data = [json.loads(line) for line in content.splitlines() if line.strip()]

    log.info("%d documents chargés", len(data))
    return data


def add_metadata(docs: list) -> list:
    """Ajoute des métadonnées de migration à chaque document."""
    ts = datetime.utcnow()
    for doc in docs:
        doc["_migrated_at"]      = ts
        doc["_schema_version"]   = "1.0"
    return docs


def insert_batches(collection, docs: list) -> dict:
    """Insère les documents par lots."""
    total     = len(docs)
    inserted  = 0
    errors    = 0

    for i in range(0, total, BATCH_SIZE):
        batch = docs[i:i + BATCH_SIZE]
        try:
            result = collection.insert_many(batch, ordered=False)
            inserted += len(result.inserted_ids)
        except BulkWriteError as bwe:
            inserted += bwe.details.get("nInserted", 0)
            errors   += len(bwe.details.get("writeErrors", []))
            log.warning("Lot %d/%d – erreurs : %d", i, total, errors)

        pct = min(100, (i + BATCH_SIZE) * 100 // total)
        log.info("Progression : %d%% (%d/%d)", pct, inserted, total)

    return {"inserted": inserted, "errors": errors, "total": total}


def migrate() -> None:
    """Pipeline de migration complet."""
    start = datetime.utcnow()
    log.info("=== DÉBUT DE LA MIGRATION ===")

    client     = connect(MONGO_URI)
    db         = client[DB_NAME]
    collection = db[COLL_NAME]

    # Suppression de l'ancienne collection
    collection.drop()
    log.info("Collection supprimée (drop)")

    # Création des rôles
    create_roles(client)

    # Chargement + enrichissement
    docs = add_metadata(load_json(DATA_FILE))

    # Insertion
    stats = insert_batches(collection, docs)

    # Index
    create_indexes(collection)

    # Rapport
    duration = (datetime.utcnow() - start).total_seconds()
    log.info("=== MIGRATION TERMINÉE ===")
    log.info("Durée        : %.1f s", duration)
    log.info("Insérés      : %d", stats["inserted"])
    log.info("Erreurs      : %d", stats["errors"])
    log.info("Total fichier: %d", stats["total"])
    log.info("Collection   : %s.%s", DB_NAME, COLL_NAME)

    client.close()


if __name__ == "__main__":
    migrate()
