from pymongo import MongoClient
import pprint

client = MongoClient("mongodb+srv://monuser:monpassword123@ac-elqsyw9.ntfl3qv.mongodb.net/")
col = client["healthcare-dataset"]["healthcare-dataset"]

print("=== TOTAL DOCUMENTS ===")
print(col.count_documents({}))

print("=== PREMIER PATIENT ===")
pprint.pprint(col.find_one({}))

print("=== PATIENTS DIABETIQUES > 60 ANS ===")
for r in col.find({"Medical Condition": "Diabetes", "Age": {"$gt": 60}}, {"Name": 1, "Age": 1, "Hospital": 1, "_id": 0}).limit(3):
    print(r)

print("=== TOP 5 CONDITIONS MEDICALES ===")
for r in col.aggregate([{"$group": {"_id": "$Medical Condition", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}, {"$limit": 5}]):
    print(r)
