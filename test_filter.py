from defusedxml import ElementTree
from filter import filter_writeups, FilterException
from typing import List

import unittest
import textwrap
import string
import random


"""
<?xml version="1.0" encoding="utf-8"?>
<rss xmlns:atom="http://www.w3.org/2005/Atom" version="2.0">
    <channel>
        <title>CTFtime.org: New writeups</title>
        <link>https://ctftime.org/writeups/rss/</link>
        <description>CTFtime.org: CTF Task writeups feed.</description>
        <atom:link href="https://ctftime.org/writeups/rss/" rel="self"></atom:link>
        <language>en-us</language>
        <lastBuildDate>Sat, 21 Nov 2020 17:56:26 -0000</lastBuildDate>
        <item>
            <title>Random CTF 2020 team CTFTeam</title>
            <link>https://ctftime.org/writeup/a</link>
            <description>Test Description</description>
            <guid>https://ctftime.org/writeup/a</guid>
            <original_url>https://example.com/ctf.html</original_url>
        </item>
    </channel>
</rss>
"""

def _get_random_word(length = 6):
    return ''.join(random.choice(string.ascii_letters) for i in range(length))

def _generate_rss_item(ctf_name):
    d = {}
    d["title"] = f"{ctf_name} team {_get_random_word()}"
    d["link"] = "https://ctftime.org/writeup/" + _get_random_word()
    d["guid"] = d["link"]
    d["description"] = " ".join(_get_random_word() for i in range(5))
    d["original_url"] = "https://example.com/"  + _get_random_word()
    return WriteupsRssItem(**d)

class WriteupsRssItem(object):
    _FIELDS = ["title", "link", "description", "guid", "original_url"]
    def __init__(self, **kwargs):
        for field in self._FIELDS:
            if field not in kwargs:
                raise ValueError(f"WriteupsRssItem missing field {field}")
            setattr(self, field, kwargs[field])
        if len(kwargs) != len(self._FIELDS):
            raise ValueError(f"WriteupsRssItem must contain {self._FIELDS} and only them")
        
    @classmethod
    def from_xml(cls, et):
        d = {}
        for child in et:
            if child.tag not in cls._FIELDS:
                raise ValueError(f"WriteupsRssItem: Unknown tag {child.tag}")
        for field in cls._FIELDS:
            d[field] = et.find(field).text
        return cls(**d)

    @classmethod
    def from_xml_string(cls, xml: str):
        et = ElementTree.fromstring(xml, forbid_dtd = True, forbid_entities = True, forbid_external = True)
        return cls.from_xml(et)

    def __str__(self):
        res = "<item>\n"
        for field in self._FIELDS:
            res += f"    <{field}>{getattr(self, field)}</{field}>\n"
        res += "</item>\n"
        return res

    def __eq__(self, other):
        if not type(other) is type(self):
            return False     
        for attr in vars(self):
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True

class WriteupsRssFeed(object):
    _FIELDS = ['title', 'link', 'description', 'language', 'lastBuildDate']
    def __init__(self, channel: dict, items: List[WriteupsRssItem]):
        for field in self._FIELDS:
            if field not in channel:
                raise ValueError(f"WriteupsRssFeed channel missing field {field}")
        if len(channel) != len(self._FIELDS):
            raise ValueError(f"WriteupsRssFeed channel must contain {self._FIELDS} and only them")
        self.channel = channel
        self.items = items

    @classmethod
    def from_item_list(cls, items: List[WriteupsRssItem]):
        channel = {}
        channel['title'] = "CTFtime.org: New writeups"
        channel['link'] = "https://ctftime.org/writeups/rss/"
        channel['description'] = "CTFtime.org: CTF Task writeups feed."
        channel['language'] = "en-us"
        channel['lastBuildDate'] = "Sat, 21 Nov 2020 17:56:26 -0000"
        return cls(channel, items)

    @classmethod
    def from_xml(cls, et):
        channel_elem = et.find("./channel")
        channel = {}
        for field in cls._FIELDS:
            channel[field] = channel_elem.find(field).text
        items = []
        for item in channel_elem.findall("./item"):
            items.append(WriteupsRssItem.from_xml(item))
        return cls(channel, items)

    @classmethod
    def from_xml_string(cls, xml: str):
        et = ElementTree.fromstring(xml, forbid_dtd = True, forbid_entities = True, forbid_external = True)
        return cls.from_xml(et)

    def __str__(self):
        items = textwrap.indent("\n".join(str(item) for item in self.items), "                    ").lstrip()
        res = f"""\
            <?xml version="1.0" encoding="utf-8"?>
            <rss xmlns:atom="http://www.w3.org/2005/Atom" version="2.0">
                <channel>
                    <title>{self.channel['title']}</title>
                    <link>{self.channel['link']}</link>
                    <description>{self.channel['description']}</description>
                    <language>{self.channel['language']}</language>
                    <lastBuildDate>{self.channel['lastBuildDate']}</lastBuildDate>
                    {items}
                </channel>
            </rss>
        """
        return textwrap.dedent(res).lstrip()

    def __eq__(self, other):
        if not type(other) is type(self):
            return False

        if self.channel != other.channel:
            return False

        return self.items == other.items
    

class TestWriteupsRssFeed(unittest.TestCase):
    def test_equal_empty(self):
        a = WriteupsRssFeed.from_item_list([])
        b = WriteupsRssFeed.from_item_list([])
        self.assertEqual(a, b)

    def test_equal(self):
        d = {}
        d["title"] = "MyCTF team FakeTeam"
        d["link"] = "https://ctftime.org/writeup/"
        d["guid"] = d["link"]
        d["description"] = "Test Description"
        d["original_url"] = "https://example.com/"
        item_a = WriteupsRssItem(**d)
        item_b = WriteupsRssItem(**d)
        a = WriteupsRssFeed.from_item_list([item_a])
        b = WriteupsRssFeed.from_item_list([item_b])
        self.assertEqual(a, b)

    def test_unequal(self):
        a = WriteupsRssFeed.from_item_list([_generate_rss_item("MyCTF")])
        b = WriteupsRssFeed.from_item_list([_generate_rss_item("OtherCTF")])
        self.assertNotEqual(a, b)

class TestFilter(unittest.TestCase):
    def test_empty_feed(self):
        feed = WriteupsRssFeed.from_item_list([])
        output = WriteupsRssFeed.from_xml_string(filter_writeups(str(feed), []))
        self.assertEqual(feed, output)

    def test_single_item_exists(self):
        ctf_name = "MyCTF"
        feed = WriteupsRssFeed.from_item_list([_generate_rss_item(ctf_name)])
        output = WriteupsRssFeed.from_xml_string(filter_writeups(str(feed), [ctf_name]))
        self.assertEqual(feed, output)

    def test_single_item_doesnt_exist(self):
        feed = WriteupsRssFeed.from_item_list([_generate_rss_item("MyCTF")])
        empty_feed = WriteupsRssFeed.from_item_list([])
        output = WriteupsRssFeed.from_xml_string(filter_writeups(str(feed), ["OtherCTF"]))
        self.assertEqual(empty_feed, output)

    def test_multiple_items_dont_exist(self):
        item_list = [_generate_rss_item("MyCTF"), _generate_rss_item("MyCTF"), _generate_rss_item("MyCTF")]
        feed = WriteupsRssFeed.from_item_list(item_list)
        empty_feed = WriteupsRssFeed.from_item_list([])
        output = WriteupsRssFeed.from_xml_string(filter_writeups(str(feed), ["OtherCTF"]))
        self.assertEqual(empty_feed, output)

    def test_multiple_item_to_remain(self):
        items_to_be_removed = [_generate_rss_item("MyCTF"), _generate_rss_item("MyCTF"), _generate_rss_item("MyCTF")]
        items_to_remain = [_generate_rss_item("OtherCTF"), _generate_rss_item("OtherCTF"), _generate_rss_item("OtherCTF")]
        item_list = items_to_be_removed + items_to_remain
        feed = WriteupsRssFeed.from_item_list(item_list)
        expected_feed = WriteupsRssFeed.from_item_list(items_to_remain)
        output = WriteupsRssFeed.from_xml_string(filter_writeups(str(feed), ["OtherCTF"]))
        self.assertEqual(expected_feed, output)

    def test_multiple_filter_names(self):
        items_to_be_removed = [_generate_rss_item("MyCTF"), _generate_rss_item("RandomCTF"), _generate_rss_item("MyCTF")]
        items_to_remain = [_generate_rss_item("OtherCTF"), _generate_rss_item("NewCTF"), _generate_rss_item("OtherCTF")]
        item_list = items_to_be_removed + items_to_remain
        feed = WriteupsRssFeed.from_item_list(item_list)
        expected_feed = WriteupsRssFeed.from_item_list(items_to_remain)
        output = WriteupsRssFeed.from_xml_string(filter_writeups(str(feed), ["OtherCTF", "NewCTF"]))
        self.assertEqual(expected_feed, output)

    def test_single_item_exists_middle_of_name(self):
        ctf_name = "My First CTF"
        feed = WriteupsRssFeed.from_item_list([_generate_rss_item(ctf_name)])
        output = WriteupsRssFeed.from_xml_string(filter_writeups(str(feed), ["First"]))
        self.assertEqual(feed, output)

    def test_single_item_case_insensitive(self):
        ctf_name = "MyCTF"
        feed = WriteupsRssFeed.from_item_list([_generate_rss_item(ctf_name)])
        output = WriteupsRssFeed.from_xml_string(filter_writeups(str(feed), [ctf_name.lower()]))
        self.assertEqual(feed, output)

    def test_special_regex_characters(self):
        items_to_be_removed = [_generate_rss_item("CTF"), _generate_rss_item("Other"), _generate_rss_item("MyCTF")]
        items_to_remain = [_generate_rss_item("Other|CTF")]
        item_list = items_to_be_removed + items_to_remain
        feed = WriteupsRssFeed.from_item_list(item_list)
        expected_feed = WriteupsRssFeed.from_item_list(items_to_remain)
        output = WriteupsRssFeed.from_xml_string(filter_writeups(str(feed), ["Other|CTF"]))
        self.assertEqual(expected_feed, output)

    def test_invalid_xml(self):
        xml = "NotXML"
        with self.assertRaises(FilterException):
            filter_writeups(xml, ["Test"])

if __name__ == '__main__':
    unittest.main()