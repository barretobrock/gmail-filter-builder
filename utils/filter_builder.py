import re
from typing import Dict, Union, List


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
