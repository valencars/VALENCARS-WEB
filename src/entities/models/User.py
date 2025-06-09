from flask_login import UserMixin
from werkzeug.security import check_password_hash,generate_password_hash

class User(UserMixin):
    
    def __init__(self,id,nombre,password,email):
        self.id = id
        self.nombre = nombre
        self.email = email
        self.password = password


    @classmethod
    def check_password(cls,hashed_password,password):
        return check_password_hash(hashed_password,password)
    
    @classmethod
    def hash_password(cls,password):
        return generate_password_hash(password)
