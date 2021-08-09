from os import getenv
from typing import Iterator, Dict, Iterable

from pymongo import MongoClient
import pandas as pd
from dotenv import load_dotenv


class DataBase:
    """ MongoDB Data Model """
    load_dotenv()
    db_url = getenv('DB_URL')

    def connect(self):
        return MongoClient(self.db_url).monster_db.rpgz_monsters

    def find(self, query_obj: Dict) -> Dict:
        return self.connect().find_one(query_obj)

    def insert(self, insert_obj: Dict):
        self.connect().insert_one(insert_obj)

    def find_many(self, query_obj: Dict, limit=0) -> Iterator[Dict]:
        return self.connect().find(query_obj, limit=limit)

    def insert_many(self, insert_obj: Iterable[Dict]):
        self.connect().insert_many(insert_obj)

    def update(self, query, data):
        self.connect().update_one(query, {"$set": data})

    def delete(self, query_obj):
        self.connect().delete_many(query_obj)

    def reset_db(self):
        self.connect().delete_many({})

    def get_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.find_many({}))

    def get_count(self):
        return self.connect().find({}).count()

    def __str__(self):
        return f"{self.get_df()}"
