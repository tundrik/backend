import datetime
import jwt
from django.conf import settings
from base.exceptions import JwtError


def generate_access_token(employee):
    access_token_payload = {
        'iss': 'local:django',
        'person': {
            'pk': employee.id,
            'guid':  str(employee.guid),
            'internal': True,
        },
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7, minutes=5),
        'iat': datetime.datetime.utcnow(),
    }
    access_token = jwt.encode(access_token_payload, settings.SECRET_KEY, algorithm='HS256')
    return access_token


def decode_token(token: str) -> dict:
    try:
        token_payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            issuer="local:django",
            algorithms=["HS256"],
            verify_exp=True
        )
        return token_payload.get('person')

    except (jwt.ExpiredSignatureError, jwt.MissingRequiredClaimError, jwt.InvalidIssuerError):
        raise JwtError()
