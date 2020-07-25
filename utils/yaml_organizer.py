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


class YamlPath:
    DEFAULT_PATH = 'example_gmail_filters.yaml'

    def __init__(self, debug: bool = False):
        self.yaml_path = self.DEFAULT_PATH if debug else sys.argv[1]
        self._check_path()
        # Get the directory of the file we're reading in
        self.yaml_dir = os.path.dirname(self.yaml_path)

    def _check_path(self):
        if not os.path.exists(self.yaml_path):
            raise ValueError(f'Path does not exist: {self.yaml_path}')

        if not os.path.isfile(self.yaml_path):
            raise ValueError(f'File does not exist: {self.yaml_path}')

        if not os.path.splitext(self.yaml_path)[1] == '.yaml':
            raise ValueError(f'File must end with \'.yaml\': {self.yaml_path}')


class YamlWrapper:
    """Wrapper class to clean YAML files"""
    def __init__(self, debug: bool = False):
        self.yaml_obj = YamlPath(debug)
        self.new_yaml_path = os.path.join(self.yaml_obj.yaml_dir, 'cleaned_filters.yaml')
        self.gmail_filters = self._load_yaml()

    def _load_yaml(self) -> dict:
        """Loads a yaml file"""
        with open(self.yaml_obj.yaml_path, 'r') as f:
            return yaml.load(f, Loader=yaml.FullLoader)

    def _save_yaml(self):
        with open(self.new_yaml_path, 'w') as f:
            f.write(yaml.dump(self.gmail_filters, allow_unicode=True))

    def email_sort_and_save(self):
        """Sorts emails listed by domain or, when lacking an obvious domain,
        the first word in the string. Saves to the new file when complete."""

        for filter_name, fdict in self.gmail_filters.items():
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
            self.gmail_filters[filter_name] = fdict
        self._save_yaml()
