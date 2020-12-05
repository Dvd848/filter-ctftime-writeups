"""A (tailored) abstraction layer for the Firebase Realtime Database.

This module provides an abstraction layer for accessing the Firebase Realtime Database.
It allows the caller to retrieve predefined information (e.g. the CTF list for a given user)
while hiding the Firebase specifics.
(However, since Firebase specifics are shared with the Javascript frontend as well, it must
expose some implementation details in the form of constants which are propagated to the frontend 
implementation).
"""
import os
import re
import base64
import json

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from typing import List

"""
The Firebase Realtime Database is built as a large JSON structure.
This application needs to store the CTF names for each user.
The structure that was chosen for this is:
{
  "data" : {
    "<user1_id>" : {
      "ctf_names" : <list>
    },
    "<user2_id>" : {
      "ctf_names" : <list>
    }
  }
}

Each user has a single child key called "ctf_names", where a delimited list of CTF names is stored.
The main reason for choosing such a structure is the fact that Firebase do not provide a free method
for limiting the number of children for a given key, but they do allow limiting the length of a value.
Therefore, in order to be able to set limits, the ctf_names list length is limited via the Realtime
Database Rules (see below). 
"""


ENTRY_SEPARATOR = "␞" # Used to separate entries in the database

# Definitions for paths in the database
UID_PLACEHOLDER = "##UID##"
PATH_TO_USER_DATA = "data/" + UID_PLACEHOLDER + "/"
KEY_USER_CTF_NAMES = "ctf_names"
PATH_TO_CTF_NAMES = PATH_TO_USER_DATA + KEY_USER_CTF_NAMES


class DatabaseException(Exception):
    """Represents an exception thrown by the database module."""
    pass

def _get_private_key() -> str:
    """Returns the private key for accessing the database.
    
    Returns the private key for accessing the database. 
    Searches first for an environment variable with the key (FIREBASE_PRIVATE_KEY),
    if not found searches for the key in a file called "private_key.json".

    Returns:
        The private key as a JSON Python object.

    Raises:
        DatabaseException: In case the key could not be found or read.
    """
    try:
        b64_key = os.environ["FIREBASE_PRIVATE_KEY"]
        return json.loads(base64.b64decode(b64_key))
    except KeyError:
        pass # Fallback to file
    try:
        with open("private_key.json") as f:
            return json.load(f)
    except Exception:
        raise DatabaseException("Can't find private key")

# Regular expression to catch invalid chars in the Firebase Realtime Database key
_INVALID_KEY_CHARS = re.compile(r"[\.\$#\[\]/\x00-\x1f\x7f]") 

def _is_legal_key(key: str):
    """Returns True iff the given key is a valid Firebase Realtime Database key.

    Based on https://firebase.google.com/docs/database/web/structure-data#how_data_is_structured_its_a_json_tree

    Args:
        key:
            The key to check for validity
    
    Returns:
        True if the key is legal, False otherwise
    """
    return not _INVALID_KEY_CHARS.search(key)

def get_ctf_names(uid: str) -> List[str]:
    """Returns the list of CTF Names for a give user

    Args:
        uid:
            The user ID for the requested user
    
    Returns:
        A list containing the CTF names for the given user

    Raises:
        ValueError: User ID is not legal
        DatabaseException: Unable to retrive list of CTF Names for given user

    """
    if not _is_legal_key(uid):
        raise ValueError(f"Invalid DB key: {uid}")
    
    ref = db.reference(PATH_TO_CTF_NAMES.replace(UID_PLACEHOLDER, uid))
    ctf_names = ref.get()
    if ctf_names is None:
        raise DatabaseException(f"Unknown user: {uid}")

    res = ctf_names.split(ENTRY_SEPARATOR)

    return res

# Setup DB Access:
cred = credentials.Certificate(_get_private_key())
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://ctftime-writeups.firebaseio.com',
    'databaseAuthVariableOverride': {
        'uid': 'feed-reader'
    }
})

# Maximum length of the ctf_names DB entry for a given user (composed of the list of names separated by the record separator)
MAX_CTF_NAMES_LENGTH = 620 # Needs to be kept in sync with Realtime Database Rules
# Realtime Database Rules:
"""
{
  "rules": {
    "data" : {
          "$uid" : {
             ".read" : "auth != null && (auth.uid == $uid || auth.uid === 'feed-reader')" ,
             ".write" : "auth != null && auth.uid == $uid",
             "ctf_names": {
             			".validate": "newData.isString() && newData.val().length < 620"
             },
             "$other": { ".validate": false }
           }
      }
  }
"""