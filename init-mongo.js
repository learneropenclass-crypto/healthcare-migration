// init-mongo.js
// Exécuté automatiquement au premier démarrage du conteneur MongoDB local

db = db.getSiblingDB("healthcare-dataset");

// ── Rôles utilisateurs ────────────────────────────────────────────────────────

db.createUser({
  user: "data_reader",
  pwd:  "ReaderPass123!",
  roles: [{ role: "read", db: "healthcare-dataset" }],
  customData: { description: "Lecture seule – analystes & dashboards" }
});

db.createUser({
  user: "data_writer",
  pwd:  "WriterPass123!",
  roles: [{ role: "readWrite", db: "healthcare-dataset" }],
  customData: { description: "Lecture/écriture – pipelines ETL" }
});

db.createUser({
  user: "data_admin",
  pwd:  "AdminPass123!",
  roles: [
    { role: "dbAdmin",    db: "healthcare-dataset" },
    { role: "readWrite",  db: "healthcare-dataset" }
  ],
  customData: { description: "Administrateur base de données" }
});

print("✓ Utilisateurs créés : data_reader, data_writer, data_admin");

// ── Validation du schéma ──────────────────────────────────────────────────────

db.createCollection("healthcare-dataset", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["Name", "Age", "Gender", "Medical Condition", "Date of Admission"],
      properties: {
        Name:                { bsonType: "string",  description: "Nom du patient" },
        Age:                 { bsonType: "int",     minimum: 0, maximum: 120 },
        Gender:              { bsonType: "string",  enum: ["Male", "Female", "Other"] },
        "Blood Type":        { bsonType: "string" },
        "Medical Condition": { bsonType: "string" },
        "Date of Admission": { bsonType: "string" },
        "Discharge Date":    { bsonType: "string" },
        Doctor:              { bsonType: "string" },
        Hospital:            { bsonType: "string" },
        "Insurance Provider":{ bsonType: "string" },
        "Billing Amount":    { bsonType: "double",  minimum: 0 },
        "Room Number":       { bsonType: "int",     minimum: 1 },
        "Admission Type":    { bsonType: "string",  enum: ["Elective", "Emergency", "Urgent"] },
        Medication:          { bsonType: "string" },
        "Test Results":      { bsonType: "string",  enum: ["Normal", "Abnormal", "Inconclusive"] }
      }
    }
  },
  validationAction: "warn"
});

print("✓ Collection healthcare-dataset créée avec validation de schéma");
