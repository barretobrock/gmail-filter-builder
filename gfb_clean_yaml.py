#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
For cleaning & sorting entries in a YAML file
"""
from utils.yaml_organizer import YamlWrapper
from utils.logger import Log



# Read in the YAML file
# Debug
#   When True: points to the example yaml file in this repo.
#   When False (default): takes in 1st argument in script run (i.e., sys.argv[1])
YamlWrapper(debug=False).sort_and_save()
