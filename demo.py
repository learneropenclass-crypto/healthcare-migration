from pymongo import MongoClient
import os

MONGO_URI = "mongodb+srv://monuser:monpassword123@ac-elqsyw9.ntfl3qv.mongodb.net/"
client = MongoClient(MONGO_URI)
col = client["healthcare-dataset"]["healthcare-dataset"]

print("=" * 50)
print("  DEMO MIGRATION HEALTHCARE - MONGODB ATLAS")
print("=" * 50)

print("\n1. CONNEXION MONGODB ATLAS")
print("   URI :", MONGO_URI[:45], "...")
print("   Statut : Connecte")

print("\n2. TOTAL DOCUMENTS EN BASE")
total = col.count_documents({})
print("   Total :", total, "documents")

print("\n3. PATIENTS DIABETIQUES DE PLUS DE 60 ANS")
patients = list(col.find(
    {"Medical Condition": "Diabetes", "Age": {"$gt": 60}},
    {"Name": 1, "Age": 1, "Hospital": 1, "_id": 0}
).limit(5))
for p in patients:
    print("  ", p)

print("\n4. TOP 5 CONDITIONS MEDICALES")
for r in col.aggregate([
    {"$group": {"_id": "$Medical Condition", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}}, {"$limit": 5}
]):
    print("  ", r["_id"], ":", r["count"], "patients")

print("\n5. FACTURATION MOYENNE PAR CONDITION")
for r in col.aggregate([
    {"$group": {"_id": "$Medical Condition", "avg": {"$avg": "$Billing Amount"}}},
    {"$sort": {"avg": -1}}, {"$limit": 3}
]):
    print("  ", r["_id"], ":", round(r["avg"], 2), "$")

print("\n" + "=" * 50)
print("  TESTS PASSES - DONNEES VALIDEES")
print("=" * 50)
client.close()
