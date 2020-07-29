import os
import time
from typing import List, Tuple
from .filter_builder import GMailFilter


class XMLBuilder:
    BASE = """<?xml version='1.0' encoding='UTF-8'?>
    <feed xmlns="http://www.w3.org/2005/Atom" xmlns:apps="http://schemas.google.com/apps/2006">
        <title>Mail Filters</title>
        <id>
            tag:mail.google.com,2008:filters:{filter_ids}
        </id>
        <updated>{updated}</updated>{entries}
    </feed>
    """
    ENTRY_BASE = """<entry>
        <category term='filter'></category>
        <title>Mail Filter</title>
        <id>tag:mail.google.com,2008:filter:{created}</id>
        <updated>{updated}</updated>
        <content/>
        <apps:property name='hasTheWord' value='{built_filter}'/>
        <apps:property name='label' value='{label}'/>{actions}
        <apps:property name='sizeOperator' value='s_sl'/>
        <apps:property name='sizeUnit' value='s_smb'/>
    </entry>"""

    def __init__(self, gmail_filter_dict: dict, output_path: str = None):
        self.gmail_filters = gmail_filter_dict
        self.filter_tools = GMailFilter(as_xml=True)
        if output_path is not None:
            self.output_path = output_path
        else:
            self.output_path = os.path.join(os.path.expanduser('~'), *['Documents', 'gmail_filters.xml'])

    def entry_builder(self) -> Tuple[List[int], str]:
        """Builds the actual entry for the filter"""
        xml_str = ''
        fids = []
        for filter_name, fdict in self.gmail_filters.items():
            # Build the filter
            queries = self.filter_tools.query_organizer(fdict)
            # Assemble actions
            actions = [
                f"<apps:property name='{x}' value='true'/>" for x in self.filter_tools.action_assembler(fdict)]

            # Append some standard keys to the dictionary
            fdict.update({
                'label': filter_name,
                'created': int(time.time()),
                'updated': self._time_xml(),
                'actions': '\n\t{}'.format('\n\t'.join(actions)) if len(actions) > 0 else ''
            })
            for query in queries:
                fids.append(int(time.time() * 10000000))
                fdict['built_filter'] = '({})'.format(query.replace("'", "&apos;"))
                # Build the XML for the entry
                xml_str += '{}\n'.format(self.ENTRY_BASE.format(**fdict))

        return fids, xml_str

    @staticmethod
    def _time_xml() -> str:
        """Returns a timestamp formatted for use in the XML file"""
        return time.strftime('%FT%TZ')

    def generate_xml(self):
        """Primary process for generating the XML file"""
        fid_list, entry_str = self.entry_builder()

        final_xml_dict = {
            'filter_ids': ','.join(list(map(str, fid_list))),
            'entries': entry_str,
            'updated': self._time_xml()
        }

        final_xml = self.BASE.format(**final_xml_dict)
        # Write to path
        self._write_xml_to_path(final_xml)

    def _write_xml_to_path(self, xml: str):
        """Saves the xml file to dedicated filepath"""
        with open(self.output_path, 'w') as f:
            f.write(xml)

