import os
from dotenv import load_dotenv

load_dotenv()

PORT = int(os.getenv('PORT', '8000'))
DATABASE_URL = os.getenv('DATABASE_URL')
APP_JWT_SECRET = os.getenv('APP_JWT_SECRET', 'change_this_super_secret')
APP_JWT_EXPIRES = os.getenv('APP_JWT_EXPIRES', '7d')
FIREBASE_SERVICE_ACCOUNT_JSON = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
