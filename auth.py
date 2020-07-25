#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
For building an managing filters in gmail
"""
from utils.gmail import GMailLabelAPI, GMailFilterAPI


# Test connection to GMailAPI
label_svc = GMailLabelAPI()
filter_svc = GMailFilterAPI()

# Get already-existing labels
all_labels = label_svc.get_all_labels(label_type='user')
all_filters = filter_svc.list_filters()

print('Label & filter services seem to be authenticated!')
