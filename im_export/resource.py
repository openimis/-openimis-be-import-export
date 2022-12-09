import collections

from django.contrib.auth.models import User
from django.db.models import Q
from insuree.models import Family, Gender, Insuree
from location.models import Location

from im_export import fields, resources, widgets

# Register your models here.

#https://django-import-export.readthedocs.io/en/latest/api_widgets.html
class CharRequiredWidget(widgets.CharWidget):
    def clean(self, value, row=None, *args, **kwargs):
        val = super().clean(value)
        if val:
            return val
        else:
            raise ValueError('this field is required')

class ForeignkeyRequiredWidget(widgets.ForeignKeyWidget):
    def clean(self, value, row=None, *args, **kwargs):
        if value:
            print(self.field, value)
            return self.get_queryset(value, row, *args, **kwargs).get(**{self.field: value})
        else:
            raise ValueError(self.field+ " required")

def remove_empty_lines(dataset):
    indexes = []
    for i in range(0, len(dataset)):
        row = ''.join(dataset[i])
        if row.strip() == '':
            indexes.append(i)
    for index in sorted(indexes, reverse=True):
        del dataset[index]	

def get_uniq(elm_list):
    elm_list_stripped =  [d.strip() for d in elm_list]
    seen = set()
    # count unique insurance number
    return [x for x in elm_list_stripped if x not in seen and not seen.add(x)]

def insuree_number_uniqueness(dataset): 
    uniq = get_uniq(dataset['insuree number'])
    if len(uniq) != len(dataset['insuree number']):
        raise ValueError("there is duplicates insurance number in the list")
    
def validate_location_inject_id(dataset):
    # change the region name/code/id into id. 
    # a village can have homonyms therefore the parent must be taken into account
    regions = {}
    districts = {}
    municiplaities = {}
    region_seen = set()
    district_seen = set()
    municipality_seen = set()
    village_seen = set()
    villages = {}
    for idx, village in enumerate(dataset['village']):
        region = dataset['region'][idx].split()
        district = dataset['district'][idx].split()
        municipality = dataset['municipality'][idx].split()
        village = dataset['village'][idx].split()
        if region not in region_seen:
            region_seen.add(region)
            regions[region] = Location.all().filter(validity_to__is_null = True)\
            .filter(Q(code=region)|Q(id=region)|Q(name=region) ).first().id
            if regions[region] is None:
                raise ValueError("Region " + region + " not found in the database")
        uniq_district = district+region
        if uniq_district not in district_seen:
            district_seen.add(uniq_district)
            districts[uniq_district]= Location.all().filter(validity_to__is_null = True)\
                .filter(parent_location = regions[region])\
                .filter(Q(code=district)|Q(id=district)|Q(name=district) ).first().id
            if districts[uniq_district] is None:
                raise ValueError("Region {} |District {} not found in the database".format(
                    region,
                    district
                ))
        uniq_municipality = municipality+district+region
        if  uniq_municipality not in municipality_seen:
            municipality_seen.add(uniq_municipality)
            municiplaities[uniq_municipality]= Location.all().filter(validity_to__is_null = True)\
                .filter(parent_location = districts[uniq_district])\
                .filter(Q(code=district)|Q(id=district)|Q(name=district) ).first().id
            if municiplaities[uniq_municipality] is None:
                raise ValueError("Region {} |District {} |Municipality {} not found in the database".format(
                    region,
                    district,
                    municipality
                ))
        uniq_village = village+uniq_municipality
        if uniq_village not in village_seen:
            village_seen.add(uniq_village)
            villages[uniq_village]= Location.all().filter(validity_to__is_null = True)\
                .filter(parent_location = municiplaities[uniq_municipality])\
                .filter(Q(code=village)|Q(id=village)|Q(name=village) ).first().id
            if villages[uniq_village] is None:
                raise ValueError(
                    "Region {} |District {} |Municipality {} |village {} not found in the database".format(
                            region,
                            district,
                            municipality,
                            village
                        )
                    )
        dataset['village'][idx] = villages[uniq_village]
        dataset['municipality'][idx] = municipality[uniq_municipality]
        dataset['district'][idx] = district[uniq_district]
        dataset['region'][idx] = regions[region]
            
class InsureeResource(resources.ModelResource):
    # model should enable to add a family and insuree
    # https://django-import-export.readthedocs.io/en/latest/import_workflow.html
    current_village = fields.Field(
        column_name='village', 
        attribute='current_village', 
        widget=ForeignkeyRequiredWidget(Location, 'village'),           
        saves_null_values=False)
    

    
    def before_import(dataset, using_transactions, dry_run, **kwargs):
        # removing the empty rows https://github.com/django-import-export/django-import-export/issues/1192#issue-718848641
        remove_empty_lines(dataset)
        # look for duplicates within the list
        insuree_number_uniqueness(dataset)
        # sort the empty head first
        dataset.sort(key=lambda a: a['head insuree number'])
        # validate the location and replace rteference with location id
        validate_location_inject_id(dataset)

        return dataset
     
    def before_import_row(row, row_number=None, **kwargs):
        # set is head if no head insuree number
        # set family id if not head
        pass

    
    def after_import_instance(instance, new, row_number=None, **kwargs):
        # if head create family
        if instance.is_head:
            #create family
            #update family id
            
            pass
        
    


    fields = ('family', 'chf_id','last_name','other_names','gender', 'dob','head',\
        'marital','passport', 'phone', 'current_address','current_village','photo')
    
    class Meta:
        model = Insuree    
    #The before_import() hook is called. By implementing this method in your resource, you can customize the import process.

