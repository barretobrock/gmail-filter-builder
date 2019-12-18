#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
For building an managing filters in gmail
"""
import os
import re
import sys
import time
import yaml


def filter_builder(fdict):
    """Builds the whole filter from items in a filter dictionary"""
    filter_text = ''.join([section_builder(x) for x in fdict['data']])
    if len(filter_text) > 600:
        # Cut the filter text down some by splitting some sections into separate filters
        print('Filter exceeds bounds. Splitting')
        matches = [x for x in re.finditer(r'(\w+\:\(.*?\))(?=\sOR)', filter_text, re.IGNORECASE)]
        filter_list = []
        remaining_text = filter_text
        for match in matches:
            filter_list.append(match.group())
            # Remove from the original filter string
            start_pos, end_pos = match.span()
            remaining_text = remaining_text.replace(match.group(), '')
            if remaining_text.startswith(' OR '):
                remaining_text = remaining_text[4:]
            elif remaining_text.startswith(' AND '):
                remaining_text = remaining_text[5:]
        if len(remaining_text) > 0:
            filter_list.append(remaining_text)
        return filter_list
    else:
        return [filter_text]


def entry_builder(gmail_filters):
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
                extras.append("<apps:property name='{}' value='{}'/>".format(k, v))

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


def section_builder(section):
    """Builds text for the specific section of the filter
    :param section:
    """

    def chunk_handler(values, key_part=None, join_part=None, not_part=None):
        """Handles a specific part of the data section"""
        if key_part is None:
            chunk = ' {} '.format(values.upper())
        elif key_part in ('from', 'cc', 'bcc', 'to'):
            chunk = '{}:({})'.format(key_part, ' {} '.format(join_part).join(values))
        else:
            chunk = '({})'.format(' {} '.format(join_part).join(['{0}{1}{0}'.format('&quot;', x) for x in values]))

        if not_part is not None:
            chunk = 'NOT {}'.format(chunk)
        return chunk

    if isinstance(section, str):
        # Section is likely a joiner if it's just string (e.g., 'and', 'or')
        return section
    # Begin constructing the section from a dictionary
    section_text = ''
    for k, v in section.items():
        not_part = key_part = join_part = None
        # Item follows the {join}-{key}[-not] syntax
        item_split = k.split('-')
        if len(item_split) == 3:
            join_part, key_part, not_part = item_split
        elif len(item_split) == 2:
            join_part, key_part = item_split
        elif len(item_split) == 1:
            join_part = item_split[0]

        join_part = join_part.upper()

        if isinstance(v, str) and key_part is not None:
            # Convert str object to list. Only joins will be allowed as str
            v = [v]
        elif isinstance(v, list) and isinstance(v[0], dict):
            # Probably a nested dict (i.e., using the 'group' tag
            # We'll use a pipe so we can split this later from the other data into its own section
            return ' OR ({})'.format(''.join([section_builder(x) for x in v]))

        section_text += chunk_handler(v, key_part, join_part, not_part)

    return section_text


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

inpath = sys.argv[1]
if not os.path.exists(inpath):
    raise ValueError('Path does not exist: {}'.format(inpath))

if not os.path.isfile(inpath):
    raise ValueError('File does not exist: {}'.format(inpath))

if not os.path.splitext(inpath)[1] == '.yaml':
    raise ValueError('File must end with \'.yaml\': {}'.format(inpath))

# Get the directory of the file we're reading in
docs_dir = os.path.dirname(inpath)
# We'll output the file in the same directory
outpath = os.path.join(docs_dir, 'mailFilters.xml')

# Read in the JSON file
with open(inpath, 'r') as f:
    gmail_filters = yaml.load(f)

fid_list, entry_str = entry_builder(gmail_filters)

final_xml = xml_base.format(filter_ids=','.join(list(map(str, fid_list))), entries=entry_str)

with open(outpath, 'w') as f:
    f.write(final_xml)
