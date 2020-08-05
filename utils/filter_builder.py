from math import ceil
from typing import Dict, Union, List, Tuple, Optional
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
        # Using the API method, we don't need to format quotes
        self.q = '&quot;' if self.as_xml else '"'
        # Mapping of simplified joiners in gmail
        self.joiner_map = {
            'or': '|',
            'and': ' ',
            'not': '-'
        }
        self.log = Log('filter-builder')

    def criteria_constructor(self, values: Union[List[str], str], key_part: Optional[str] = None,
                             join_part: Optional[str] = None, not_part: Optional[str] = None) -> List[str]:
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
            chunk = '({})'.format(join_part.join(['{0}{1}{0}'.format(self.q, x) for x in values]))
        if not_part is not None:
            chunk = f'-{chunk}'

        if self._is_oversized(chunk):
            n_times = ceil(len(chunk) / self.char_limit)
            chunk_size = ceil(len(values) / n_times)
            chunks = []
            for i in range(n_times):
                st_pos = i * chunk_size
                end_pos = st_pos + chunk_size
                chunks += self.criteria_constructor(values[st_pos:end_pos], key_part, join_part, not_part)
            return chunks
        return [chunk]

    def _is_oversized(self, string: Union[str, List[str]]) -> bool:
        """Checks if provided string is larger than the character limit"""
        if isinstance(string, list):
            string = ''.join(string)
        if len(string) >= self.char_limit:
            return True
        return False

    def _key_splitter(self, key: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Takes in a key and splits it by associated parts"""
        join_part = key_part = not_part = None
        # Item follows the {join}-{key}[-not] syntax
        item_split = key.split('-')
        if len(item_split) == 3:
            join_part, key_part, not_part = item_split
            not_part = self.joiner_map[not_part]
        elif len(item_split) == 2:
            join_part, key_part = item_split
        elif len(item_split) == 1:
            join_part = item_split[0]

        if join_part in self.joiner_map.keys():
            join_part = self.joiner_map[join_part]

        return join_part, key_part, not_part

    def query_constructor(self, section: Union[List[str], dict]) -> List[str]:
        """Builds the query (i.e., assembles multiple criteria into a single query string)
        Args:
            section: list of str or dict, contains things like list of emails, text
                or subsections of filters (dict)
        """
        if isinstance(section, str):
            # Section is likely a joiner if it's just string (e.g., 'and', 'or')
            return [section]
        # Begin constructing the section from a dictionary
        sections = []
        for k, v in section.items():
            # Item follows the {join}-{key}[-not] syntax
            join_part, key_part, not_part = self._key_splitter(k)

            if isinstance(v, str) and key_part is not None:
                # Convert str object to list. Only joins will be allowed as str
                v = [v]
            elif isinstance(v, list) and isinstance(v[0], dict):
                # Probably a nested dict (i.e., using the 'section' tag)
                # We'll use a pipe so we can split this later from the other data into its own section
                if 'section' in k and '-' in k:
                    # Dealing with a section; parse out the leading joiner (if any)
                    #   and throw it in before it if there are other items in front
                    joiner = k.split('-')[0]
                    sections.append(f' {joiner.upper()} ')
                sections.append('(')
                for sect in v:
                    # Process the section
                    sections += self.query_constructor(sect)
                sections.append(')')
                return sections
            sections += self.criteria_constructor(v, key_part, join_part, not_part)
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

    def _merge_filters(self, filters: List[str]) -> List[str]:
        """Combines filters up to but not exceeding the character limit"""
        rebuilt_filters = []

        fstr = ''
        cnt = 0
        for i, filt in enumerate(filters):
            if cnt != i:
                continue
            if filt == '(':
                # Build a section
                # First, store what was in fstr
                if fstr != '':
                    rebuilt_filters.append(fstr)
                    fstr = ''
                lbrac_cnt = rbrac_cnt = 0
                for j, sect in enumerate(filters[i:]):
                    if sect == '(':
                        lbrac_cnt += 1
                    elif sect == ')':
                        rbrac_cnt += 1
                    if sect == ')' and rbrac_cnt == lbrac_cnt:
                        break
                section = ''.join(filters[i:i + j + 1])
                if self._is_oversized(section):
                    raise ValueError('A section exceeds the 600 char limit. '
                                     'It currently cannot be saved as a single filter. Reduce it at once.')
                rebuilt_filters.append(section)
                cnt = i + j
            elif filt == ' OR ':
                if fstr == '':
                    # Skip on new string construction
                    pass
                else:
                    if filters[i + 1] == '(':
                        # Upcoming bracket. If fstr has anything, save to rebuilt_filters and continue
                        if fstr != '':
                            rebuilt_filters.append(fstr)

                    # Check whether the string after this wouldn't exceed the limits
                    if self._is_oversized(fstr + filt + filters[i + 1]):
                        # Oversized. Save fstr to the list & ignore the current string
                        rebuilt_filters += [fstr, filters[i + 1]]
                        # Set count to after the next item in the list
                        fstr = ''
                    else:
                        # Not oversized. Add both to fstr
                        fstr += ''.join([filt, filters[i + 1]])
                    cnt = i + 1

            else:
                fstr += filt
                # Test if concatenating strings exceeds limit
                # make sure that the new string we're testing isn't just AND or OR
                # if so, iterate to next item. Make sure it's not '('
                # if _that's_ too big, save the first string. if not, save the new string and
                # set cnt = the place of the last string

            cnt += 1

        return rebuilt_filters

    @staticmethod
    def _intersperse(qlist: List[str], divider: str) -> List[str]:
        """Places {divider} between items in a list"""
        is_section = qlist[0] == '('

        # Populate items in list with just the divider
        use_list = qlist[1:-1] if is_section else qlist
        spaced = [divider] * (len(use_list) * 2 - 1)
        # Replace every other item with the actual list items
        spaced[0::2] = use_list
        return ['('] + spaced + [')'] if is_section else spaced

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
            #   Check if combining them yields an oversized string
            if self._is_oversized(query):
                # These filters are too big to be combined.
                #   Keep them on their own and intersperse with ' OR '
                query = self._intersperse(query, ' OR ')
            filters += query
        filter_text = ''.join(filters)
        if self._is_oversized(filter_text):
            # Cut the filter text down some by splitting some sections into separate filters
            self.log.debug(f'Filter exceeded bounds: {len(filter_text)} > {self.char_limit}. Splitting.')
            # Before splitting, combine any 'AND' queries
            filters = self._combine_and(filters)
            return self._merge_filters(filters)
        else:
            return [filter_text]

    def action_assembler(self, fdict: Dict[str, Union[str, List[str]]],
                         label_id: str = None) -> Union[Dict[str, List[str]], List[str]]:
        """Processes the actions (e.g., 'never-important', 'archive', etc.)"""
        if 'actions' not in fdict.keys() and label_id is None:
            return []

        if 'actions' in fdict.keys():
            action_obj = Action(fdict['actions'], as_xml=self.as_xml)
        else:
            # For when no actions are passed;
            #   we'll still need to create this object to pass a label
            action_obj = Action([], as_xml=self.as_xml)
        if self.as_xml:
            return action_obj.xml_actions
        else:
            return action_obj.build_actions(label_id)
