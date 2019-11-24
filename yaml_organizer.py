#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sorts emails in to/from/cc/bcc sections by domain (if applicable)
    in order to make visual inspection of emails a bit more bearable
"""
import os
import re
import sys
import yaml


def email_sort(gmail_filters):
    """Sorts emails listed by domain or, when lacking an obvious domain, the first word in the string."""

    for filter_name, fdict in gmail_filters.items():
        # Sort the 'data' section, leave everything else alone
        if 'data' in fdict.keys():
            for section in fdict['data']:
                for k, v in section.items():
                    if any([x in k for x in ['from', 'to', 'bcc', 'cc']]):
                        # Working with emails. let's sort them as best we can by domain
                        # First, we'll make a 'cleaned' list
                        cleaner = re.compile(r'[^\w\.\@]', re.I)
                        cleaned = [re.findall(r'[\w]+', cleaner.sub('', x)) for x in v]
                        sortable = [x[-2] if len(x) > 1 else x[0] for x in cleaned]
                        # We'll then bind the two lists together and sort by the cleaned items
                        fdict['data'][0][k] = [x for _, x in sorted(zip(sortable, v))]
        # Write back to our filters
        gmail_filters[filter_name] = fdict
    return gmail_filters


inpath = sys.argv[1]
if not os.path.exists(inpath):
    raise ValueError('Path does not exist: {}'.format(inpath))

if not os.path.isfile(inpath):
    raise ValueError('File does not exist: {}'.format(inpath))

if not os.path.splitext(inpath)[1] == '.yaml':
    raise ValueError('File must end with \'.yaml\': {}'.format(inpath))

# Get the directory of the file we're reading in
docs_dir = os.path.dirname(inpath)
outpath = os.path.join(docs_dir, 'cleaned_filters.yaml')

# Read in the JSON file
with open(inpath, 'r') as f:
    gmail_filters = yaml.load(f)

cleaned_yaml = email_sort(gmail_filters)

with open(outpath, 'w') as f:
    f.write(yaml.dump(gmail_filters, allow_unicode=True))
