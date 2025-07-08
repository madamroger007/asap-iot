from os import environ
from dotenv import load_dotenv
load_dotenv()

SQLALCHEMY_TRACK_MODIFICATIONS = False

DB_DRIVER = environ.get('DB_DRIVER', 'mysql+pymysql')
DB_USER = environ.get('DB_USER', 'root')
DB_PASSWORD = environ.get('DB_PASSWORD', '')
DB_HOST = environ.get('DB_HOST', '127.0.0.1')
DB_PORT = environ.get('DB_PORT', 3306)
DB_NAME = environ.get('DB_NAME')


# AUTH
SECRET_KEY = environ.get('SECRET_KEY', 'your-secret-key')
ADMIN_PASSWORD = environ.get('ADMIN_PASSWORD', '123')
ADMIN_EMAIL = environ.get('ADMIN_EMAIL', 'admin@gmail.com')
# JWT