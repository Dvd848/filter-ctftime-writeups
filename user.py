from typing import List
import database

MAX_CTF_ENTRIES = 20

class User(object):
    def __init__(self, user_id: str):
        if not self.is_valid_user_id(user_id):
            raise ValueError(f"Invalid User ID: {user_id}")

        self._user_id = user_id

    @property
    def user_id(self) -> str:
        return self._user_id

    @staticmethod
    def is_valid_user_id(uid: str) -> bool:
        return uid.isalnum()

    @property
    def ctf_list(self) -> List[str]:
        ctf_list = database.get_ctf_names(self.user_id)
        if len(ctf_list) > MAX_CTF_ENTRIES:
            raise RuntimeError(f"Failed to read CTF list for user {self.user_id}: Too many entries ({ctf_list})")
        return ctf_list
