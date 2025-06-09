import datetime
import pytz
from jwt import InvalidTokenError, decode, encode, ExpiredSignatureError, InvalidSignatureError
from decouple import config

class Security():

    secret = config("JWT_KEY")
    tz = pytz.timezone('Europe/Madrid')

    @classmethod
    def generate_token(cls, authenticated_user):
        payload = {
            'iat':datetime.datetime.now(tz=cls.tz),
            'exp':datetime.datetime.now(tz=cls.tz)+datetime.timedelta(minutes=10),
            'email':authenticated_user.email,
            'id':authenticated_user.id
        }

        return encode(payload,cls.secret, algorithm='HS256')
    
    @classmethod
    def verify_token(cls, token):
            try:
                payload = decode(token, cls.secret, algorithms=['HS256'])
                return True, payload
            except (ExpiredSignatureError, InvalidSignatureError) as e:
                return False
            except InvalidTokenError:
                return False
            
