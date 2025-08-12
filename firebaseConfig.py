import firebase_admin
from firebase_admin import db, firestore, credentials
import os, json
firebase_config = json.loads(os.environ["FIREBASE_CONFIG"])
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://defi-ai-assistant-default-rtdb.firebaseio.com/"
    })

rtdb = db
fs = firestore.client()


