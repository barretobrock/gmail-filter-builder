#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
For building an managing filters in gmail
"""
from utils.gmail import GMailLabelAPI, GMailFilterAPI
from utils.filter_builder import GMailFilter
from utils.yaml_organizer import YamlWrapper


# Read in the YAML file
# Debug points to the example yaml file in this repo
gmail_filters = YamlWrapper().gmail_filters
# Load tools & API services
filter_tools = GMailFilter()
label_svc = GMailLabelAPI()
filter_svc = GMailFilterAPI()

# Get already-existing labels
all_labels = label_svc.get_all_labels(label_type='user')
label_name_list = [x['name'] for x in all_labels]
label_id_list = [x['id'] for x in all_labels]
# Get already-existing filters
all_filters = filter_svc.list_filters()

# Remove all the old filters
for f in all_filters:
    filter_svc.delete_filter(f['id'])

# Create new filters
for label_name, data in gmail_filters.items():
    # Determine if the label already exists
    if label_name in label_name_list:
        # Label exists, retrieve its id
        label = label_svc.get_label(label_name)
    else:
        # Label doesn't exist, create a new one
        label = label_svc.create_label(label_name)
    label_id = label['id']
    # Process the processed YAML file into a list of gmail queries and list of actions
    queries = filter_tools.query_organizer(data)
    actions = filter_tools.action_assembler(data)
    for query in queries:
        filter_svc.create_filter(query=query, action_list=actions, label_id=label_id)

