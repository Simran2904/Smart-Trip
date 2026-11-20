import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()


def get_mongo_client():
    try:
        client = MongoClient(
            os.getenv("MONGO_URI", "mongodb://localhost:27017"),
            serverSelectionTimeoutMS=5000
        )

        # Check whether MongoDB is available
        client.admin.command("ping")

        return client

    except Exception as error:
        print("MongoDB Connection Error:", error)
        raise


def get_mongo_database():
    client = get_mongo_client()
    database = client[
        os.getenv("MONGO_DATABASE", "smarttrip_mongo")
    ]

    return client, database
