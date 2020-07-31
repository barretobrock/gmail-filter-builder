#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
For building an managing filters in gmail
"""
from utils.filter_builder import GMailFilter
from utils.yaml_organizer import YamlWrapper
from utils.xml_builder import XMLBuilder


# Read in the YAML file
# Debug
#   When True: points to the example yaml file in this repo.
#   When False (default): takes in 1st argument in script run (i.e., sys.argv[1])
gmail_filters = YamlWrapper(debug=False).gmail_filters
# Load tools & API services
filter_tools = GMailFilter()
xml_tools = XMLBuilder(gmail_filters)
# Generate the xml & save to path
# (defaults to ~/Documents/gmail_filters.xml)
xml_tools.generate_xml()
