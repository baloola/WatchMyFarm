from pymongo import MongoClient
from urllib.parse import quote_plus


def create_user(database, user, password):
    database.command("createUser", user, pwd=password, roles=["readWrite"])


def login(user, password, host):
    uri = "mongodb://%s:%s@%s" % (
        quote_plus(user), quote_plus(password), host)
    client_db = MongoClient(uri)
    return client_db


user = 'root'
password = 'example'
host = 'localhost:8081/'

client = login('root', 'example', 'localhost:8081/')


watchDB = client["watchDB"]


farmersDB = watchDB["farmersDB"]

# print(client.list_database_names())
# print(watchDB.list_collection_names())
