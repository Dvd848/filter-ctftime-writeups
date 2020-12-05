from defusedxml import ElementTree
from typing import List
import re

class FilterException(Exception):
    """Represents an exception thrown by the filtering module."""
    pass

def filter_writeups(feed: str, ctf_list: List[str]) -> str:
    """Filters the given writeups feed, keeping only entries from the given CTF list.

    Receives a given list of CTF names, and filters the given CTFTime writeups RSS feed 
    by going over all writeup items and removing items which don't contain one of the provided
    CTF names in the title. 
    An item will be kept if one of the CTF names in ctf_list can be found anywhere withing the item's
    title (case insensitive).

    The feed is expected to be structured in a similar manner to the following template:
    <?xml version="1.0" encoding="utf-8"?>
    <rss xmlns:atom="http://www.w3.org/2005/Atom" version="2.0">
        <channel>
            <title></title>
            <link></link>
            <description></description>
            <atom:link href="" rel="self"></atom:link>
            <language></language>
            <lastBuildDate></lastBuildDate>
            <item>
                <title></title>
                <link></link>
                <description></description>
                <guid></guid>
                <original_url></original_url>
            </item>
        </channel>
    </rss>

    In practice, only the "/channel/item/title" node is used.

    Args:
        feed: 
            A CTFTime writeups RSS feed. 
        ctf_list: 
            A list of CTF names whose corresponding items should be kept in the feed.
            A list containing an empty string will filter out all items.
            It is forbidden to include an empty string together with non-empty strings
            in the same list.

    Returns:
        A CTFTime writeups RSS feed XML where non-matching items were removed.

    Raises:
        FilterException: An error occurred during the processing of the feed.
    """

    try:
        et = ElementTree.fromstring(feed, forbid_dtd = True, forbid_entities = True, forbid_external = True)
        channel = et.find("./channel")
        if channel is None:
            raise FilterException("Can't find channel in provided XML")

        if '' in ctf_list and len(ctf_list) > 1:
            raise ValueError("An empty string can't act as a filter together with other filters")

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

