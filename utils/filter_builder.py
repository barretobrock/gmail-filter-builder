import re
from typing import Dict, Union, List


class GMailFilter:
    """Class for building a single GMail filter"""

    def __init__(self, as_xml: bool = False):
        self.as_xml = as_xml

    @staticmethod
    def criteria_constructor(values: Union[List[str], str], key_part: str = None, join_part: str = None,
                             not_part: str = None) -> str:
        """Handles the construction of specific criteria of the filter
        (e.g., from: to: subject, etc...)"""
        if key_part is None:
            chunk = f' {values.upper()} '
        elif key_part in ('from', 'cc', 'bcc', 'to'):
            chunk = f'{key_part}:({f" {join_part} ".join(values)})'
        elif key_part in ('subject', ):
            # Format quotes between values
            val_list = ['{0}{1}{0}'.format('&quot;', x) if '*' not in x else x for x in values]
            vals_part = f' {join_part} '.join(val_list)
            chunk = f'{key_part}:({vals_part})'
        else:
            # Handles text area
            chunk = '({})'.format(f' {join_part} '.join(['{0}{1}{0}'.format('&quot;', x) for x in values]))

        if not_part is not None:
            chunk = f'NOT {chunk}'
        return chunk

    def query_constructor(self, section: Union[List[str], Dict[str, str]]) -> str:
        """Builds the query (i.e., assembles multiple criteria into a single query string)
        Args:
            section: list of str or dict, contains things like list of emails, text
                or subsections of filters (dict)
        """
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
                # Probably a nested dict (i.e., using the 'section' tag
                # We'll use a pipe so we can split this later from the other data into its own section
                return ' OR ({})'.format(''.join([self.query_constructor(x) for x in v]))

            section_text += self.criteria_constructor(v, key_part, join_part, not_part)

        return section_text

    def query_organizer(self, fdict: Dict[str, Union[str, int]]) -> List[str]:
        """Handles the processing of the final query, mainly by
        splitting it into multiple parts in the event that the query exceeds 600 chars

        Args:
            fdict: dict, the label-specific dictionary resulting from the pre-processed YAML file
                NOTE: expects a 'data' key
        """
        filter_text = ''.join([self.query_constructor(x) for x in fdict['data']])
        if len(filter_text) > 600:
            # Cut the filter text down some by splitting some sections into separate filters
            print('Filter exceeds bounds. Splitting')
            # Split on an 'OR' if possible
            matches = [x for x in re.finditer(r'(\w+\:\(.*?\))(?=\sOR)', filter_text, re.IGNORECASE)]
            filter_list = []
            remaining_text = filter_text
            for match in matches:
                filter_list.append(match.group())
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

    @staticmethod
    def action_assembler(fdict: Dict[str, Union[str, List[str]]]) -> List[str]:
        """Processes the actions (e.g., 'never-important', 'archive', etc.)"""
        if 'actions' not in fdict.keys():
            return []
        return fdict['actions']
