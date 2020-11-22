from defusedxml import ElementTree
import re

class FilterException(Exception):
    pass

def filter_writeups(feed, ctf_list):
    try:
        et = ElementTree.fromstring(feed, forbid_dtd = True, forbid_entities = True, forbid_external = True)
        channel = et.find("./channel")
        if channel is None:
            raise FilterException("Can't find channel in provided XML")

        ctfnames_regex = re.compile("|".join(re.escape(name) for name in ctf_list), re.IGNORECASE)

        for item in channel.findall("./item"):
            title = item.find("title").text
            if title is None:
                raise FilterException("Can't find item title in provided XML")
            if not ctfnames_regex.search(title):
                channel.remove(item)

        return ElementTree.tostring(et, encoding='unicode', method='xml')
    except FilterException:
        raise
    except Exception as e:
        raise FilterException("Failed to filter XML") from e
