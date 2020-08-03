#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
For building an managing filters in gmail
"""
from utils.gmail import GMailLabelAPI, GMailFilterAPI
from utils.filter_builder import GMailFilter
from utils.yaml_organizer import YamlWrapper
from utils.logger import Log


log = Log('main-script')
log.debug('Logging initiated')
# Read in the YAML file
# Debug points to the example yaml file in this repo
#   When True: points to the example yaml file in this repo.
#   When False (default): takes in 1st argument in script run (i.e., sys.argv[1])
gmail_filters = YamlWrapper().gmail_filters
# Load tools & API services
filter_tools = GMailFilter()
log.debug('Initializing APIs')
label_svc = GMailLabelAPI()
filter_svc = GMailFilterAPI()

# Get already-existing labels
all_labels = label_svc.get_all_labels(label_type='user')
label_name_list = [x['name'] for x in all_labels]
label_id_list = [x['id'] for x in all_labels]
# Get already-existing filters
all_filters = filter_svc.list_filters()

# Remove all the old filters
log.debug('Beginning filter removal process...')
for i, f in enumerate(all_filters):
    log.debug(f'Removing filter {i + 1} of {len(all_filters)}...')
    filter_svc.delete_filter(f['id'])

# Create new filters
log.debug('Beginning new label/filter creation process...')
for label_name, data in gmail_filters.items():
    log.debug(f'Working on label {label_name}')
    # Determine if the label already exists
    if label_name in label_name_list:
        # Label exists, retrieve its id
        label = label_svc.get_label(label_name)
    else:
        # Label doesn't exist, create a new one
        log.debug(f'Label "{label_name}" did not exist. Creating it...')
        label = label_svc.create_label(label_name)
    label_id = label['id']
    # Process the processed YAML file into a list of gmail queries and list of actions
    queries = filter_tools.query_organizer(data)
    actions = filter_tools.action_assembler(data, label_id)
    log.debug(f'Generated {len(queries)} queries...')
    for i, query in enumerate(queries):
        log.debug(f'Applying query {i + 1} of {len(queries)}...')
        filter_svc.create_filter(query=query, actions_dict=actions)

log.debug('Process completed. Ending script.')
