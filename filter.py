from defusedxml import ElementTree
from typing import List
import re

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

MAX_CTF_ENTRIES = 20

class FilterException(Exception):
    pass

def init():
    cred = credentials.Certificate("private_key.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://ctftime-writeups.firebaseio.com'
    })

def filter_writeups(feed: str, ctf_list: List[str]) -> str:
    try:
        et = ElementTree.fromstring(feed, forbid_dtd = True, forbid_entities = True, forbid_external = True)
        channel = et.find("./channel")
        if channel is None:
            raise FilterException("Can't find channel in provided XML")

        if '' in ctf_list and len(ctf_list) > 1:
            raise FilterException("An empty string can't act as a filter together with other filters")

        pattern = "|".join(re.escape(name) for name in ctf_list)
        if pattern == "":
            pattern = "$^" # Won't match anything
        ctfnames_regex = re.compile(pattern, re.IGNORECASE)

        for item in channel.findall("./item"):
            title = item.find("title").text
            if title is None:
                raise FilterException("Can't find item title in provided XML")
            if not ctfnames_regex.search(title):
                channel.remove(item)

        return ElementTree.tostring(et, encoding = 'unicode', method = 'xml', xml_declaration = True)
    except FilterException:
        raise
    except Exception as e:
        raise FilterException("Failed to filter XML") from e

def get_ctf_names(uid: str) -> List[str]:
    if not is_valid_uid(uid):
        raise ValueError(f"Invalid user ID: {uid}")
    
    ref = db.reference(f'data/{uid}/ctf_names')
    ctf_names = ref.get()
    if ctf_names is None:
        raise FilterException(f"Unknown user: {uid}")

    res = ctf_names.split("␞")

    if len(res) > MAX_CTF_ENTRIES:
        raise FilterException(f"Too many entries for user {uid}: {res}")

    return res


def is_valid_uid(uid):
    return uid.isalnum()