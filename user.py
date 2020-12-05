"""Represents a user in the system."""
from typing import List
import database

# Maximum amount of CTFs a user can follow
MAX_CTF_ENTRIES = 10

# Maximum length for a CTF name
MAX_ENTRY_NAME_LEN = (database.MAX_CTF_NAMES_LENGTH - MAX_CTF_ENTRIES) // MAX_CTF_ENTRIES

class User(object):
    """A user in the system."""
    def __init__(self, user_id: str):
        """Initialize a user.

        Args:
            user_id:
                The user ID
        """
        if not self.is_valid_user_id(user_id):
            raise ValueError(f"Invalid User ID: {user_id}")

        self._user_id = user_id

    @property
    def user_id(self) -> str:
        """"The user's user ID."""
        return self._user_id

    @staticmethod
    def is_valid_user_id(uid: str) -> bool:
        """Validates the user ID and determines if the given string can act as a user ID.

        This method does not check if the given user ID exists, just that it looks like a string
        which can be a user ID.

        Args:
            uid: The user ID to validate.

        Returns:
            True iff the user ID has a valid form.
        """
        return uid.isalnum()

    @property
    def ctf_list(self) -> List[str]:
        """Returns the list of CTF names this user ID is subscribed to.
        
        Raises a RuntimeError if the number of CTFs is above the limit.
        """
        ctf_list = database.get_ctf_names(self.user_id)
        if len(ctf_list) > MAX_CTF_ENTRIES:
            raise RuntimeError(f"Failed to read CTF list for user {self.user_id}: Too many entries ({ctf_list})")
        return ctf_list
