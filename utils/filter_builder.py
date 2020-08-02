import re
from math import ceil
from typing import Dict, Union, List
from .logger import Log


class Action:
    """GMail Actions"""
    def __init__(self, action_list: List[str], as_xml: bool = False):
        self.as_xml = as_xml
        # When using Gmail API (as_xml = False)
        self.add_actions = []
        self.remove_actions = []
        # When building an XML (as_xml = True)
        self.xml_actions = []

        self.action_map = {
            'archive': self.action_archive,
            'mark-read': self.action_mark_read,
            'never-spam': self.action_never_spam,
            'never-important': self.action_never_important,
            'always-important': self.action_always_important,
            'delete-email': self.action_delete_email,
            'mark-starred': self.action_mark_starred
        }
        # Build out the action lists
        self._process_actions(action_list)

    def _process_actions(self, action_list: List[str]):
        """Move through the list of actions and build out the final action lists"""
        for action in action_list:
            # Call the action, which will add to the respective lists
            self.action_map[action]()

    def build_actions(self, label_id: str = None) -> Union[Dict[str, List[str]], List[str]]:
        """Takes the action lists and compiles them into a dictionary to create a filter
        If label id included, will append to list as well
        """
        if self.as_xml:
            # Returns a list of the actions in XML parlance to be placed into their property tags
            return self.xml_actions

        # For the API, we'll make a dictionary instead
        action_dict = {}
        for k, v in zip(['removeLabelIds', 'addLabelIds'], [self.remove_actions, self.add_actions]):
            if len(v) > 0:
                # Add to final action dict
                action_dict[k] = v
            if k == 'addLabelIds' and label_id is not None:
                # Add the label we'll assign to the filter
                if 'addLabelIds' in action_dict.keys():
                    action_dict[k].append(label_id)
                else:
                    action_dict[k] = [label_id]

        return action_dict

    def action_archive(self):
        """Archive the email (skip inbox)"""
        if self.as_xml:
            self.xml_actions.append('shouldArchive')
        else:
            self.remove_actions.append('INBOX')

    def action_mark_read(self):
        """Mark email as unread"""
        if self.as_xml:
            self.xml_actions.append('shouldMarkAsRead')
        else:
            self.remove_actions.append('UNREAD')

    def action_never_spam(self):
        """Never mark as spam"""
        if self.as_xml:
            self.xml_actions.append('shouldNeverSpam')
        else:
            self.remove_actions.append('SPAM')

    def action_never_important(self):
        """Never mark as important"""
        if self.as_xml:
            self.xml_actions.append('shouldNeverMarkAsImportant')
        else:
            self.remove_actions.append('IMPORTANT')

    def action_always_important(self):
        """Always mark as important"""
        if self.as_xml:
            self.xml_actions.append('shouldAlwaysMarkAsImportant')
        else:
            self.add_actions.append('IMPORTANT')

    def action_delete_email(self):
        """Move the email to trash"""
        if self.as_xml:
            self.xml_actions.append('shouldDelete')
        else:
            self.add_actions.append('TRASH')

    def action_mark_starred(self):
        """Mark email as starred"""
        if self.as_xml:
            self.xml_actions.append('shouldStar')
        else:
            self.add_actions.append('STARRED')


class GMailFilter:
    """Class for building a single GMail filter"""

    def __init__(self, as_xml: bool = False):
        self.as_xml = as_xml
        # Maximum (supposed) limit of characters to use in a query
        self.char_limit = 600
        # Mapping of simplified joiners in gmail
        self.joiner_map = {
            'or': '|',
            'and': ' ',
            'not': '-'
        }
        self.log = Log('filter-builder')

    def criteria_constructor(self, values: Union[List[str], str], key_part: str = None, join_part: str = None,
                             not_part: str = None) -> Union[str, List[str]]:
        """Handles the construction of specific criteria of the filter
        (e.g., from: to: subject, etc...)

        If the resulting string is longer than the allowed character limits,
            the string will be split accordingly
        """
        if key_part is None:
            chunk = f' {values.upper()} '
        elif key_part in ('from', 'cc', 'bcc', 'to', 'list', 'replyto', 'subject'):
            chunk = f'{key_part}:({join_part.join(values)})'
        else:
            # Handles text area
            chunk = '({})'.format(join_part.join(['{0}{1}{0}'.format('&quot;', x) for x in values]))
        if not_part is not None:
            chunk = f'-{chunk}'

        if self._is_oversized(chunk):
            n_times = ceil(len(chunk) / self.char_limit)
            chunk_size = ceil(len(values) / n_times)
            chunks = []
            for i in range(n_times):
                st_pos = i * chunk_size
                end_pos = st_pos + chunk_size
                chunks.append(self.criteria_constructor(values[st_pos:end_pos], key_part, join_part, not_part))
            return chunks
        return chunk

    def _is_oversized(self, string: str) -> bool:
        """Checks if provided string is larger than the character limit"""
        if len(string) >= self.char_limit:
            return True
        return False

    def query_constructor(self, section: Union[List[str], dict]) -> Union[str, List[str]]:
        """Builds the query (i.e., assembles multiple criteria into a single query string)
        Args:
            section: list of str or dict, contains things like list of emails, text
                or subsections of filters (dict)
        """
        if isinstance(section, str):
            # Section is likely a joiner if it's just string (e.g., 'and', 'or')
            return section
        # Begin constructing the section from a dictionary
        sections = []
        section_text = ''
        for k, v in section.items():
            not_part = key_part = join_part = None
            # Item follows the {join}-{key}[-not] syntax
            item_split = k.split('-')
            if len(item_split) == 3:
                join_part, key_part, not_part = item_split
                not_part = self.joiner_map[not_part]
            elif len(item_split) == 2:
                join_part, key_part = item_split
            elif len(item_split) == 1:
                join_part = item_split[0]

            if join_part in self.joiner_map.keys():
                join_part = self.joiner_map[join_part]
            else:
                # Processing a joiner
                join_part = section[join_part]

            if isinstance(v, str) and key_part is not None:
                # Convert str object to list. Only joins will be allowed as str
                v = [v]
            elif isinstance(v, list) and isinstance(v[0], dict):
                # Probably a nested dict (i.e., using the 'section' tag
                # We'll use a pipe so we can split this later from the other data into its own section
                sects = []
                for sect in v:
                    # Process the section
                    proc_sect = self.query_constructor(sect)
                    if isinstance(proc_sect, list):
                        sects += proc_sect
                    else:
                        sects.append(proc_sect)
                return ' OR ({})'.format(''.join(sects))

            new_text = self.criteria_constructor(v, key_part, join_part, not_part)
            if isinstance(new_text, list):
                # Already been split
                sections += new_text
            elif self._is_oversized(section_text + new_text):
                sections.append(section_text)
                section_text = new_text
            else:
                section_text += new_text
        if len(section_text) > 0:
            sections.append(section_text)

        return sections

    @staticmethod
    def _combine_and(filters: List[str]) -> List[str]:
        """ Go through the filters, combine AND filters"""
        rebuilt_filters = []
        cnt = 0
        for i, filt in enumerate(filters):
            if filt == ' AND ':
                # Combine the previous entry with this one and the next, reset i
                rebuilt_filters[-1] = ''.join(filters[i - 1:i + 2])
                cnt = i + 2
            elif cnt == i:
                rebuilt_filters.append(filt)
                cnt += 1
        return rebuilt_filters

    def _merge_filters(self, filters: List[str]):
        """Combines filters up to but not exceeding the character limit"""
        rebuilt_filters = []
        cnt = 0
        for i, filt in enumerate(filters):
            if cnt != i:
                continue
            for j in range(i + 1, len(filters)):
                test = ''.join(filters[i:j])
                if j == len(filters) - 1:
                    # Reached the end
                    test = ''.join(filters[i:])
                    if not self._is_oversized(test):
                        rebuilt_filters.append(test)
                    else:
                        rebuilt_filters += [''.join(filters[i:j]), filters[j]]
                    return rebuilt_filters
                elif not self._is_oversized(test):
                    continue
                else:
                    end_pos = j - 1
                    final = ''.join(filters[i: end_pos])
                    end_txt = ' OR '
                    if final.endswith(end_txt):
                        final = final[:-len(end_txt)]
                    rebuilt_filters.append(final)
                    cnt = end_pos
                    break

    def query_organizer(self, fdict: Dict[str, Union[str, int]]) -> List[str]:
        """Handles the processing of the final query, mainly by
        splitting it into multiple parts in the event that the query exceeds 600 chars

        Args:
            fdict: dict, the label-specific dictionary resulting from the pre-processed YAML file
                NOTE: expects a 'data' key
        """
        filters = []
        for filter_dict in fdict['data']:
            # Pass in a single dictionary of filter data (e.g., or-from: [])
            query = self.query_constructor(filter_dict)
            if isinstance(query, str):
                filters.append(query)
            else:
                # The query was already broken down into multiples
                if not self._is_oversized(''.join(query)):
                    filters.append(''.join(query))
                else:
                    filters += query
        filter_text = ''.join(filters)
        if self._is_oversized(filter_text):
            # Cut the filter text down some by splitting some sections into separate filters
            print(f'Filter exceeded bounds: {len(filter_text)} > {self.char_limit}. Splitting.')
            # Before splitting, combine any 'AND' queries
            filters = self._combine_and(filters)
            return self._merge_filters(filters)
        else:
            return [filter_text]

    def action_assembler(self, fdict: Dict[str, Union[str, List[str]]],
                         label_id: str = None) -> Union[Dict[str, List[str]], List[str]]:
        """Processes the actions (e.g., 'never-important', 'archive', etc.)"""
        if 'actions' not in fdict.keys():
            return []

        action_obj = Action(fdict['actions'], as_xml=self.as_xml)
        if self.as_xml:
            return action_obj.xml_actions
        else:
            return action_obj.build_actions(label_id)
