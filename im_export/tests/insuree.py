import json
from resource import InsureeResource

from core.services import (create_or_update_core_user,
                           create_or_update_interactive_user)
from django.test import TestCase
from insuree.models import Family, Insuree
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
        'district': 'Batha' ,
        'municipality': 'BEGOU', 
        'villages' : [
            'Baguirmi',
            'Boua',
            'Niellim',
            'Sarakaba',
            'Maroc'
        ]
    }
]

        
class importInsureeTest(TestCase):
    regions = {}
    districts = {}
    municipalities = {}
    villages = []
    def setUp(self) -> None:
        
        super(importInsureeTest, self).setUp()
        i_user, i_user_created = create_or_update_interactive_user(
            user_id=None, data=_TEST_DATA_USER, audit_user_id=999, connected=False)
        user, user_created = create_or_update_core_user(
            user_uuid=None, username=_TEST_DATA_USER["username"], i_user=i_user)
        self.user = user
        test_location = json.loads(_TEST_LOCATIONS)

        for locations in test_location:
            # create the region (must be unique name)
            if locations['region'] not in self.regions:
                test_region = create_test_location('R', custom_props={"name":locations['region'] })
                self.regions[locations['region']] = test_region
            else:
                test_region = self.regions[locations['region']]
                
            # create the child district (must be unique name across district)    
            if locations['district'] not in self.districts:
                test_district = create_test_location('D', custom_props={"name":locations['district'],"parent_id": test_region.id })
                self.districts[locations['district']] = test_district
            else:
                test_district = self.districts[locations['district']]  
                
            # create the child municipalities (must be unique name across municipalities)    
            if locations['municipality'] not in self.municipalities:
                test_municipality = create_test_location('M', custom_props={"name":locations['municipality'],"parent_id": test_district.id })
                self.municipalities[locations['municipality']] = test_municipality
            else:
                test_municipality = self.municipalities[locations['municipality']]      
                
            # create the child municipalities: can have same name in other municipalities  
            for villages in locations['vilages']:
                village = create_test_location('V', custom_props={"name":villages,"parent_id": test_municipality.id })
                self.villages.append(village)

    def test_simple_import(self):
        with open('import_insuree.json', 'r') as f:
            my_json_obj = json.load(f)
            result = InsureeResource.import_data(
                my_json_obj, dry_run=True, use_transactions=True,
                collect_failed_rows=True,
            )
            self.assertEqual(result.has_errors(), False)
    
    def tearDown(self)-> None:
        for village in self.villages:
            # first remove the FK from the familly
            Family.all().filter(location = village).update(head=None)
            # then remove the insuree
            Insuree.all().filter(location = village).delete()
            #then remove the familly
            Family.all().filter(location = village).delete()
            # then remove the village
            village.delete()
        # remove the municipalities
        for municipality in self.municipalities.values():  
            municipality.delete()
        # remove the district
        for disctrict in self.disctricts.values():
            disctrict.delete()
        # remove the region
        for region in self.regions.values():
            region.delete()        
            
