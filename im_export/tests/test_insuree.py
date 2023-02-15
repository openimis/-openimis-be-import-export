import os
from tablib import Dataset
from im_export.resources import InsureeResource
from core.services import create_or_update_core_user, create_or_update_interactive_user
from django.test import TestCase
from location.test_helpers import create_test_location

_TEST_USER_NAME = "test_insuree_import"
_TEST_USER_PWD = "test_insuree_import"
_TEST_DATA_USER = {
    "username": _TEST_USER_NAME,
    "last_name": _TEST_USER_NAME,
    "password": _TEST_USER_PWD,
    "other_names": _TEST_USER_NAME,
    "user_types": "INTERACTIVE",
    "language": "en",
    "roles": [1, 5, 9],
}

# all location used in the test files must use those name
_TEST_LOCATIONS = [
    {
        'region': 'Batha',
        'district': 'Batha',
        'municipality': 'BEGOU',
        'villages': [
            'Baguirmi',
            'Boua',
            'Niellim',
            'Sarakaba',
            'Maroc'
        ]
    }
]


class ImportInsureeTest(TestCase):
    regions = {}
    districts = {}
    municipalities = {}
    villages = []

    def setUp(self) -> None:

        super(ImportInsureeTest, self).setUp()
        self.i_user, i_user_created = create_or_update_interactive_user(
            user_id=None, data=_TEST_DATA_USER, audit_user_id=999, connected=False)
        user, user_created = create_or_update_core_user(
            user_uuid=None, username=_TEST_DATA_USER["username"], i_user=self.i_user)
        self.user = user
        test_location = _TEST_LOCATIONS

        for locations in test_location:
            # create the region (must be unique name)
            if locations['region'] not in self.regions:
                test_region = create_test_location('R', custom_props={"name": locations['region']})
                self.regions[locations['region']] = test_region
            else:
                test_region = self.regions[locations['region']]

            # create the child district (must be unique name across district)    
            if locations['district'] not in self.districts:
                test_district = create_test_location('D', custom_props={"name": locations['district'],
                                                                        "parent_id": test_region.id})
                self.districts[locations['district']] = test_district
            else:
                test_district = self.districts[locations['district']]

                # create the child municipalities (must be unique name across municipalities)
            if locations['municipality'] not in self.municipalities:
                test_municipality = create_test_location('M', custom_props={"name": locations['municipality'],
                                                                            "parent_id": test_district.id})
                self.municipalities[locations['municipality']] = test_municipality
            else:
                test_municipality = self.municipalities[locations['municipality']]

                # create the child municipalities: can have same name in other municipalities
            for villages in locations['villages']:
                village = create_test_location('V', custom_props={"name": villages, "parent_id": test_municipality.id})
                self.villages.append(village)

    def test_simple_import(self):
        dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        resource = InsureeResource(user=self.i_user)
        with open(os.path.join(dir_path, 'tests/import_example.csv'), 'r') as f:
            imported_data = resource \
                .validate_and_sort_dataset(Dataset(headers=InsureeResource.insuree_headers).load(f.read()))
            result = resource.import_data(
                imported_data, dry_run=True, use_transactions=True,
                collect_failed_rows=False,
            )
            self.assertEqual(result.has_errors(), False)

    def test_simple_export(self):
        result = InsureeResource(self.i_user).export().dict
        self.assertTrue(result)

# todo expand tests
