import firebase_admin
from firebase_admin import db, firestore, credentials
import os, json

firebase_config = json.loads(os.environ["FIREBASE_CONFIG"])

cred = credentials.Certificate(firebase_config)

try:
    firebase_admin.get_app()
except ValueError:
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://defi-ai-assistant-default-rtdb.firebaseio.com/"
    })

rtdb = db
fs = firestore.client()



