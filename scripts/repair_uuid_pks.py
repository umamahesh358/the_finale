import os
import sys
from pathlib import Path
import django
from pymongo import MongoClient
from django.conf import settings
from django.db import models

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

def repair():
    client = MongoClient(settings.DATABASES["default"]["HOST"])
    db = client[settings.DATABASES["default"]["NAME"]]
    
    # Scan all models
    models_to_fix = []
    for model in django.apps.apps.get_models(include_auto_created=True):
        pk_field = model._meta.pk
        # Check if the primary key is a UUIDField
        if isinstance(pk_field, models.UUIDField):
            models_to_fix.append((model._meta.db_table, pk_field.column))
            
    summary = []
    for table_name, pk_column in models_to_fix:
        collection = db[table_name]
        updated_docs = 0
        
        # 1. First, repair any documents where _id is still an ObjectId
        for document in collection.find({"_id": {"$type": "objectId"}}):
            old_id = document["_id"]
            # Get the UUID string value
            new_id = document.get(pk_column)
            if not new_id:
                new_id = document.get("id")
            
            if new_id:
                new_doc = dict(document)
                # Keep both _id and id (or pk_column) as the UUID string
                new_doc["_id"] = str(new_id)
                new_doc[pk_column] = str(new_id)
                if "id" not in new_doc:
                    new_doc["id"] = str(new_id)
                    
                # Delete old document and insert new one
                collection.delete_one({"_id": old_id})
                collection.insert_one(new_doc)
                updated_docs += 1
                
        # 2. Repair any documents where _id is a UUID string, but pk_column or 'id' is missing
        for document in collection.find({"_id": {"$type": "string"}}):
            _id_val = document["_id"]
            # Check if pk_column or 'id' field is missing or not equal to _id_val
            needs_update = False
            new_doc = dict(document)
            
            if pk_column not in new_doc or new_doc[pk_column] != _id_val:
                new_doc[pk_column] = _id_val
                needs_update = True
            if "id" not in new_doc or new_doc["id"] != _id_val:
                new_doc["id"] = _id_val
                needs_update = True
                
            if needs_update:
                collection.replace_one({"_id": _id_val}, new_doc)
                updated_docs += 1
                
        if updated_docs:
            summary.append((table_name, updated_docs))
            
    client.close()
    return summary

if __name__ == "__main__":
    result = repair()
    if not result:
        print("No documents required primary key repair.")
    for table_name, updated_docs in result:
        print(f"{table_name}: updated {updated_docs} documents")
