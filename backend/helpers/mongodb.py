from pymongo import MongoClient, errors as mongo_errors
from bson.objectid import ObjectId
import multiprocessing
import os
import sys

_mongoDB = dict()


def _config():
    host = os.environ.get('MONGO_HOST', '127.0.0.1')
    port = int(os.environ.get('MONGO_PORT', 27017))
    db = os.environ.get('MONGO_DB', 'LPOS')
    return {'host': host, 'port': port, 'database': db}


class mongoDB(object):
    _conn = dict()

    def __init__(self):
        mongoClient = MongoClient(host=_config()['host'], port=int(_config()['port']), serverSelectionTimeoutMS=500)
        mongoDB._conn[multiprocessing.current_process().name] = mongoClient.get_database(_config()['database'])

    def wait_for_connection(self):
        first = True
        mongoClient = MongoClient(host=_config()['host'], port=_config()['port'], serverSelectionTimeoutMS=2000)
        while True:
            try:
                mongoClient.server_info()
                print('MongoDB started ... continue', flush=True)
                return
            except mongo_errors.ServerSelectionTimeoutError:
                if first:
                    print('MongoDB pending ... waiting', flush=True)
                    first = False
            except Exception:
                print('MongoDB unknown error ... aborting', flush=True)
                sys.exit(1)

    def is_connected(self):
        try:
            mongoClient = MongoClient(host=_config()['host'], port=_config()['port'], serverSelectionTimeoutMS=1000)
            mongoClient.server_info()
            return True
        except Exception:
            return False

    def reset_connections(self):
        mongoDB._conn = dict()

    def conn(self):
        p = multiprocessing.current_process().name
        if p not in mongoDB._conn:
            mongoDB()
        return mongoDB._conn[p]

    def coll(self, which):
        return self.conn().get_collection(which)

    def clear(self, table=None):
        if table is None:
            for c in self.conn().list_collections():
                self.conn().get_collection(c['name']).drop()
        else:
            self.conn().get_collection(table).drop()

    def exists(self, where, what_id):
        return self.get(where, what_id) is not None

    def get(self, where, what_id):
        return self.coll(where).find_one({'_id': what_id})

    def search_one(self, where, what):
        return self.coll(where).find_one(what)

    def search_many(self, where, what):
        return self.coll(where).find(what)

    def create(self, where, what_data):
        if what_data.get('_id', None) is not None:
            return False
        what_data['_id'] = str(ObjectId())
        self.coll(where).insert_one(what_data)
        return True

    def update(self, where, what_id, with_data):
        if not self.exists(where, what_id):
            return False
        self.coll(where).update_one({'_id': what_id}, with_data)
        return True

    def update_many(self, where, what_data, with_data):
        self.coll(where).update_many(what_data, with_data)
        return True

    def replace(self, where, what_data):
        if what_data.get('_id', None) is None:
            return False
        self.coll(where).replace_one({'_id': what_data['_id']}, what_data, True)
        return True

    def delete(self, where, what_id):
        self.coll(where).delete_one({'_id': what_id})

    def delete_many(self, where, what):
        self.coll(where).delete_many(what)

    def sum(self, where, what_field, what_filter=None):
        pipeline = list()
        if what_filter is not None:
            pipeline.append({'$match': what_filter})
        pipeline.append({'$group': {'_id': 'sum', what_field: {'$sum': f'${what_field}'}}})
        result = self.coll(where).aggregate(pipeline)
        if result.alive:
            return result.next()[what_field]
        else:
            return 0

    def count(self, where, what={}):
        return self.coll(where).count_documents(what)
