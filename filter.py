from defusedxml import ElementTree
from typing import List
import re

class FilterException(Exception):
    pass

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

