from django.db.models import Q

from core.models import InteractiveUser
from insuree.models import Insuree, Family, Gender
from insuree.services import FamilyService
from location.models import Location

from import_export import fields, resources, widgets


# https://django-import-export.readthedocs.io/en/latest/api_widgets.html
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
            raise ValueError(self.field + ' required')


def remove_empty_lines(dataset):
    indexes = []
    for i in range(0, len(dataset)):
        row = ''.join(dataset[i])
        if row.strip() == '':
            indexes.append(i)
    for index in sorted(indexes, reverse=True):
        del dataset[index]


def get_uniq(elm_list):
    elm_list_stripped = [d.strip() for d in elm_list]
    seen = set()
    # count unique insurance number
    return [x for x in elm_list_stripped if x not in seen and not seen.add(x)]


def insuree_number_uniqueness(dataset):
    uniq = get_uniq(dataset['insuree_number'])
    if len(uniq) != len(dataset['insuree_number']):
        raise ValueError('There are duplicates of insurance number in the list')


def get_location_str_filter(str):
    return Q(code=str) | Q(name=str)  # | Q(uuid=str) | Q(id=int(str) if str.isdigit() else None)


def validate_location_inject_id(dataset):
    # change the region name/code/id/uuid into id.
    # a village can have homonyms therefore the parent must be taken into account
    regions = {}
    districts = {}
    municipalities = {}
    villages = {}

    for idx, row in enumerate(dataset.dict):
        uniq_region = row['region'].strip()
        if uniq_region not in regions:
            region_model = Location.objects.all().filter(validity_to__isnull=True).filter(
                get_location_str_filter(uniq_region)).first()
            if region_model:
                regions[uniq_region] = region_model.id
            else:
                raise ValueError('Location {} not found in the database'.format(uniq_region))

        district = row['district'].strip()
        uniq_district = uniq_region + "|" + district
        if uniq_district not in districts:
            district_model = Location.objects.all().filter(validity_to__isnull=True,
                                                           parent__id=regions[uniq_region]).filter(
                get_location_str_filter(district)).first()
            if district_model:
                districts[uniq_district] = district_model.id
            else:
                raise ValueError('Location {} not found in the database'.format(uniq_district))

        municipality = row['municipality'].strip()
        uniq_municipality = uniq_district + "|" + municipality
        if uniq_municipality not in municipalities:
            municipality_model = Location.objects.all().filter(validity_to__isnull=True,
                                                               parent__id=districts[uniq_district]).filter(
                get_location_str_filter(municipality)).first()
            if municipality_model:
                municipalities[uniq_municipality] = municipality_model.id
            else:
                raise ValueError('Location {} not found in the database'.format(uniq_municipality))

        village = row['village'].strip()
        uniq_village = uniq_municipality + "|" + village
        if uniq_village not in villages:
            village_model = Location.objects.all().filter(validity_to__isnull=True,
                                                          parent__id=municipalities[uniq_municipality]).filter(
                get_location_str_filter(village)).first()
            if village_model:
                villages[uniq_village] = village_model.id
            else:
                raise ValueError('Location {} not found in the database'.format(uniq_village))

        row['village'] = villages[uniq_village]
        row['municipality'] = municipalities[uniq_municipality]
        row['district'] = districts[uniq_district]
        row['region'] = regions[uniq_region]


class InsureeResource(resources.ModelResource):
    insuree_headers = ['head_insuree_number', 'insuree_number', 'last_name', 'other_names', 'dob', 'sex', 'village',
                       'municipality', 'district', 'region']

    head_insuree_number = fields.Field(
        attribute='family',
        column_name='head_insuree_number',
        widget=ForeignkeyRequiredWidget(Family, field='head_insuree__chf_id'),
    )

    insuree_number = fields.Field(
        attribute='chf_id',
        column_name='insuree_number',
    )

    last_name = fields.Field(
        attribute='last_name',
        column_name='last_name',
    )

    other_names = fields.Field(
        attribute='other_names',
        column_name='other_names',
    )

    dob = fields.Field(
        attribute='dob',
        column_name='dob',
    )

    sex = fields.Field(
        attribute='gender',
        column_name='sex',
        widget=ForeignkeyRequiredWidget(Gender, field='gender'),
    )

    # todo current_village vs family__location (current village is frequently NULL and possibly different than family__locaiton, family__locaiton is redundant for all non head insurees)
    village = fields.Field(
        attribute='current_village',
        column_name='village',
        widget=ForeignkeyRequiredWidget(Location, field='name'),
    )

    # readonly, just for export and import validation
    municipality = fields.Field(
        attribute='current_village',
        column_name='municipality',
        widget=ForeignkeyRequiredWidget(Location, field='parent__name'),
        readonly=True
    )

    # readonly, just for export and import validation
    district = fields.Field(
        attribute='current_village',
        column_name='district',
        widget=ForeignkeyRequiredWidget(Location, field='parent__parent__name'),
        readonly=True
    )

    # readonly, just for export and import validation
    region = fields.Field(
        attribute='current_village',
        column_name='region',
        widget=ForeignkeyRequiredWidget(Location, field='parent__parent__parent__name'),
        readonly=True
    )

    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        # removing the empty rows https://github.com/django-import-export/django-import-export/issues/1192#issue-718848641
        remove_empty_lines(dataset)
        # look for duplicates within the list
        insuree_number_uniqueness(dataset)
        # validate the location and replace rteference with location id
        validate_location_inject_id(dataset)

    def before_import_row(self, row, row_number=None, **kwargs):
        # todo not ready
        # set is head if no head_insuree_number
        row['card_issued'] = False
        row['audit_user_id'] = 0
        if row['head_insuree_number'] == row['insuree_number']:
            row['head'] = True
            row['family'] = None
        else:
            row['head'] = False
            # get head
            head = Insuree.objects.all().filter(validity_to__isnull=True).get(chf_id=row['head_insuree_number'])
            row['family'] = head.family_id
            # set family id if not head

    def after_import_instance(self, instance, new, row_number=None, **kwargs):
        # todo untested
        # if head create family
        if instance.head:
            # create family
            data = {'head_insuree': instance.chf_id, 'location': instance.current_village}
            instance.family = FamilyService(InteractiveUser.objects.get(login_name='Admin')).create_or_update(data)
            # update family id
            instance.save()

    def get_queryset(self):
        # TODO add location based filtering (possibly push current user to InsureeResource.__init__)
        return super().get_queryset() \
            .filter(validity_to__isnull=True) \
            .select_related('gender', 'current_village', 'family', 'family__location', 'family__location__parent',
                            'family__location__parent__parent', 'family__location__parent__parent__parent')

    class Meta:
        model = Insuree
        import_id_fields = ('insuree_number',)
        fields = ('insuree_number', 'head_insuree_number', 'last_name', 'other_names', 'dob', 'sex', 'village',
                  'municipality', 'district', 'region')
