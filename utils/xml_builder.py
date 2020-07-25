import time
from typing import List, Tuple


xml_base = """<?xml version='1.0' encoding='UTF-8'?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:apps="http://schemas.google.com/apps/2006">
    <title>Mail Filters</title>
    <id>
        tag:mail.google.com,2008:filters:{filter_ids}
    </id>
    <updated>2019-10-27T24:02:22Z</updated>{entries}
</feed>
"""

xml_entry_base = """<entry>
    <category term='filter'></category>
    <title>Mail Filter</title>
    <id>tag:mail.google.com,2008:filter:{created}</id>
    <updated>{updated}</updated>
    <content/>
    <apps:property name='hasTheWord' value='{built_filter}'/>
    <apps:property name='label' value='{label}'/>{extras}
    <apps:property name='sizeOperator' value='s_sl'/>
    <apps:property name='sizeUnit' value='s_smb'/>
</entry>"""


def entry_builder(gmail_filters: dict) -> Tuple[List[int], str]:
    """Builds the actual entry for the filter"""
    xml_str = ''
    fids = []
    for filter_name, fdict in gmail_filters.items():
        # Build the filter
        built_filters = filter_builder(fdict)
        # Begin working with extra items in the dictionary
        extras = []
        for k, v in fdict.items():
            if k != 'data':
                # Extra things to add
                extras.append(f"<apps:property name='{k}' value='{v}'/>")

        # Append some standard keys to the dictionary
        fdict.update({
            'label': filter_name,
            'created': int(time.time()),
            'updated': time.strftime('%FT%TZ'),
            'extras': '\n\t{}'.format('\n\t'.join(extras)) if len(extras) > 0 else ''
        })
        for built_filter in built_filters:
            fids.append(int(time.time() * 10000000))
            fdict['built_filter'] = '({})'.format(built_filter.replace("'", "&apos;"))
            # Build the XML for the entry
            xml_str += '{}\n'.format(xml_entry_base.format(**fdict))

    return fids, xml_str


fid_list, entry_str = entry_builder(gmail_filters)

final_xml = xml_base.format(filter_ids=','.join(list(map(str, fid_list))), entries=entry_str)

with open(outpath, 'w') as f:
    f.write(final_xml)
