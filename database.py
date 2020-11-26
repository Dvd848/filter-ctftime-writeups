import os
import base64
import json

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

from typing import List

MAX_CTF_ENTRIES = 20

class DatabaseException(Exception):
    pass

def _get_private_key():
    try:
        b64_key = os.environ["FIREBASE_PRIVATE_KEY"]
        return json.loads(base64.b64decode(b64_key))
    except KeyError:
        private_key_file = "private_key.json"
        if os.path.exists(private_key_file):
            return private_key_file
        raise DatabaseException("Can't find private key")


def init():
    cred = credentials.Certificate(_get_private_key())
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://ctftime-writeups.firebaseio.com'
    })

def get_ctf_names(uid: str) -> List[str]:
    if not is_valid_uid(uid):
        raise ValueError(f"Invalid user ID: {uid}")
    
    ref = db.reference(f'data/{uid}/ctf_names')
    ctf_names = ref.get()
    if ctf_names is None:
        raise DatabaseException(f"Unknown user: {uid}")

    res = ctf_names.split("␞")

    if len(res) > MAX_CTF_ENTRIES:
        raise DatabaseException(f"Too many entries for user {uid}: {res}")

    return res


def is_valid_uid(uid):
    return uid.isalnum()