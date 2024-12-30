import firebase_admin
from firebase_admin import initialize_app
import json
from decouple import Config, RepositoryEnv
import os

envPath = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
env = Config(RepositoryEnv(envPath))

firebaseCredentials = {
    "type": env("FIREBASE_TYPE"),
    "project_id": env("FIREBASE_PROJECT_ID"),
    "private_key_id": env("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": env("FIREBASE_PRIVATE_KEY").replace("\\n", "\n").strip("\""),
    "client_email": env("FIREBASE_CLIENT_EMAIL"),
    "client_id": env("FIREBASE_CLIENT_ID"),
    "auth_uri": env("FIREBASE_AUTH_URI"),
    "token_uri": env("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": env("FIREBASE_AUTH_PROVIDER_CERT_URL"),
    "client_x509_cert_url": env("FIREBASE_CLIENT_CERT_URL"),
    "universe_domain": env("FIREBASE_UNIVERSE_DOMAIN"),
}

def initializeFirebaseConnection():
    credentialsFile = "firebaseCredentials.json"

    try:
        with open(credentialsFile, "w") as f:
            json.dump(firebaseCredentials, f)

        credentials = firebase_admin.credentials.Certificate("firebaseCredentials.json")
        initialize_app(credentials, {"databaseURL": env("FIREBASE_DB_URL")})
    finally:
        if os.path.exists(credentialsFile):
            os.remove(credentialsFile)
