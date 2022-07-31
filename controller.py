from pymongo import MongoClient
from urllib.parse import quote_plus
import bcrypt


class Controller:
    """
    a controller class that handles users registration, login
    logout, initiation of password reset and finalization of password reset.
    """

    def __init__(self):
        self.logged_in = False
        uri = "mongodb://%s:%s@%s" % (quote_plus('root'), quote_plus('example'), 'localhost:8081/')
        try:
            self.client = MongoClient(uri, serverSelectionTimeoutMS=2000)
            self.db = self.client['watchDB']
            self.collection = self.db['farmersDB']
        except Exception as e:
            print(e.message)

    def create_user(self, database, user, password):
        database.command('createUser', user, pwd=password, roles=['readWrite'])

    def register(self, newUser):
        old_user = self.collection.find_one({'email': newUser['email']})

        if old_user is not None:
            raise(Exception)
        else:
            # create hash of the new password
            bytes = newUser['password'].encode('utf-8')
            salt = bcrypt.gensalt()
            hash = bcrypt.hashpw(bytes, salt)

            new_user = {
                'email': newUser['email'],
                'password': hash,
                'polygon': newUser['polygon']
            }
            self.collection.insert_one(new_user)

    def login(self, user):
        existing_user = self.collection.find_one({'email': user['email']})

        if existing_user is None:
            # raise(Exception)
            self.register(user)
        else:
            user_password = user['password'].encode('utf-8')
            correct_password = bcrypt.checkpw(user_password, existing_user['password'])
            if correct_password:
                self.logged_in = True
            else:
                raise(Exception)

    def log_off(self):
        self.logged_in = False

    def password_reset(self, new_password, email):
        bytes = new_password.encode('utf-8')
        salt = bcrypt.gensalt()
        hash = bcrypt.hashpw(bytes, salt)

        new_values = {"$set": {'password': hash}}

        self.collection.update_one({'email': email}, new_values)

    def get_user_by_email(self, email):
        user_object = self.collection.find_one({'email': email})
        return user_object

    def update_geometry(self, polygon, email):
        new_values = {"$set": {'polygon': polygon}}

        self.collection.update_one({'email': email}, new_values)

    def update_history(self, user, items):
        items_list = []
        for key, item in items:
            items_list.append(item['identifier'])
        user_object = self.get_user_by_email(user['email'])

        last_product_date = user_object['last_product_date'] if hasattr(user_object, 'last_product_date') else None
        products_bucket_list = user_object['products_bucket_list']if hasattr(user_object, 'products_bucket_list') else []
        if (products_bucket_list is not None
            and isinstance(products_bucket_list, list)
            and len(products_bucket_list) > 0
            and last_product_date not in products_bucket_list):

            products_bucket_list + items_list
        else:
            products_bucket_list = items_list
        new_values = {
            "$set": {
                'products_bucket_list': products_bucket_list,
                'last_product_date': last_product_date
            }
        }

        self.collection.update_one({'email': user['email']}, new_values)

