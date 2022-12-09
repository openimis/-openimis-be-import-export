from django.test import TestCase
from resource import InsureeResource
import json


with open('import_insuree.json', 'r') as f:
    my_json_obj = json.load(f)

    result = InsureeResource.import_data(
        my_json_obj, dry_run=True, use_transactions=True,
        collect_failed_rows=True,
    )