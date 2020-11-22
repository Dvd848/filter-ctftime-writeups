from defusedxml import ElementTree


def filter_writeups(feed, ctf_list):
    try:
        et = ElementTree.fromstring(feed, forbid_dtd = True, forbid_entities = True, forbid_external = True)
        channel = et.find("./channel")
        for item in channel.findall("./item"):
            found = False
            title = item.find("title").text
            for ctf_name in ctf_list:
                if ctf_name in title:
                    found = True
                    break
            if not found:
                channel.remove(item)
        return ElementTree.tostring(et, encoding='unicode', method='xml')
    except Exception:
        # TODO: Better exception messages
        raise
