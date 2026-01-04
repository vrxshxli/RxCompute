import json
import firebase_admin
from firebase_admin import credentials, auth
from .config import FIREBASE_SERVICE_ACCOUNT_JSON
import os

def init_firebase():
    if firebase_admin._apps:
        return firebase_admin.get_app()

    if FIREBASE_SERVICE_ACCOUNT_JSON:
        cred_obj = json.loads(FIREBASE_SERVICE_ACCOUNT_JSON)
        cred = credentials.Certificate(cred_obj)
    elif os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        cred = credentials.ApplicationDefault()
    else:
        raise RuntimeError('Firebase Admin credentials not provided')

    return firebase_admin.initialize_app(cred)


def verify_id_token(id_token: str):
    init_firebase()
    return auth.verify_id_token(id_token)
