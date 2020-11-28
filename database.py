import os
import re
import base64
import json

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

from typing import List

ENTRY_SEPARATOR = "␞"

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

_INVALID_KEY_CHARS = re.compile(r"[\.\$#\[\]/\x00-\x1f\x7f]")

def _is_legal_key(key: str):
    # https://firebase.google.com/docs/database/web/structure-data#how_data_is_structured_its_a_json_tree
    return not _INVALID_KEY_CHARS.search(key)

def get_ctf_names(uid: str) -> List[str]:
    if not _is_legal_key(uid):
        raise ValueError(f"Invalid DB key: {uid}")
    
    ref = db.reference(f'data/{uid}/ctf_names')
    ctf_names = ref.get()
    if ctf_names is None:
        raise DatabaseException(f"Unknown user: {uid}")

    res = ctf_names.split(ENTRY_SEPARATOR)

    return res


cred = credentials.Certificate(_get_private_key())
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://ctftime-writeups.firebaseio.com'
})


# Realtime Database Rules:
"""
{
  "rules": {
    "data" : {
          "$uid" : {
             ".read" : "auth != null && auth.uid == $uid" ,
             ".write" : "auth != null && auth.uid == $uid",
             "ctf_names": {
             			".validate": "newData.isString() && newData.val().length < 620"
             },
             "$other": { ".validate": false }
           }
      }
  }
}
"""