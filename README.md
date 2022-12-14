# import-export
 openimis-be-import-export



## Process:

pre-import 
1- validate data
2- inject location id

for each insuree
1- check if head (no head_insuree_number)
2- if not head add family id
3- create instance
4- if head, create family


the data seems to be formated using the tablib library

## annex

fields
------
head_insuree_number :  str - empty for head
insuree_number: str
first_name: str
other_name: str
dob: date  - integer (unix) or YYYY-MM-DD
sex: char -  M/F/O
village: str :  code or name
municipality: str :  code or name
district: str :  code or name
region: str :  code or name
regenerate_insuree_id (optionnal) : bool
photo (optionnal) : b64 encoded
Process:
-------
0- validate
0.1 -  all location, return fail if a single one is wrong, enrich the list with the location id
0.2 - look for duplicates within the list
0.3- look for already used insuree id  (regenerate_insuree_id is null or false)
1- extract the list of the head of family (i.e. head_insuree_number__is_null)
2- create familly if not exist
3- enrich the list of insuree  with the family id
4- save insuree



********

class Family(core_models.VersionedModel, core_models.ExtendableModel):
    id = models.AutoField(db_column='FamilyID', primary_key=True)
    uuid = models.CharField(db_column='FamilyUUID',
                            max_length=36, default=uuid.uuid4, unique=True)
    head_insuree = models.OneToOneField(
        'Insuree', models.DO_NOTHING, db_column='InsureeID', null=False,
        related_name='head_of')
    location = models.ForeignKey(
        location_models.Location,
        models.DO_NOTHING, db_column='LocationId', blank=True, null=True)
    poverty = models.BooleanField(db_column='Poverty', blank=True, null=True)
    family_type = models.ForeignKey(
        FamilyType, models.DO_NOTHING, db_column='FamilyType', blank=True, null=True,
        related_name='families')
    address = models.CharField(
        db_column='FamilyAddress', max_length=200, blank=True, null=True)
    is_offline = models.BooleanField(
        db_column='isOffline', blank=True, null=True)
    ethnicity = models.CharField(
        db_column='Ethnicity', max_length=1, blank=True, null=True)
    confirmation_no = models.CharField(
        db_column='ConfirmationNo', max_length=12, blank=True, null=True)
    confirmation_type = models.ForeignKey(
        ConfirmationType,
        models.DO_NOTHING, db_column='ConfirmationType', blank=True, null=True,
        related_name='families')
    audit_user_id = models.IntegerField(db_column='AuditUserID')
    # rowid = models.TextField(db_column='RowID', blank=True, null=True)
    
************** 


class Insuree(core_models.VersionedModel, core_models.ExtendableModel):
    id = models.AutoField(db_column='InsureeID', primary_key=True)
    uuid = models.CharField(db_column='InsureeUUID', max_length=36, default=uuid.uuid4, unique=True)
    class Meta:
        model = Insuree
    family = models.ForeignKey(Family, models.DO_NOTHING, blank=True, null=True,
                               db_column='FamilyID', related_name="members")
    chf_id = models.CharField(db_column='CHFID', max_length=12, blank=True, null=True)
    last_name = models.CharField(db_column='LastName', max_length=100)
    other_names = models.CharField(db_column='OtherNames', max_length=100)

    gender = models.ForeignKey(Gender, models.DO_NOTHING, db_column='Gender', blank=True, null=True,
                               related_name='insurees')
    dob = core.fields.DateField(db_column='DOB')


    head = models.BooleanField(db_column='IsHead')
    marital = models.CharField(db_column='Marital', max_length=1, blank=True, null=True)

    passport = models.CharField(max_length=25, blank=True, null=True)
    phone = models.CharField(db_column='Phone', max_length=50, blank=True, null=True)
    email = models.CharField(db_column='Email', max_length=100, blank=True, null=True)
    current_address = models.CharField(db_column='CurrentAddress', max_length=200, blank=True, null=True)
    geolocation = models.CharField(db_column='GeoLocation', max_length=250, blank=True, null=True)
    current_village = models.ForeignKey(
        location_models.Location, models.DO_NOTHING, db_column='CurrentVillage', blank=True, null=True)
    photo = models.OneToOneField(InsureePhoto, models.DO_NOTHING,
                              db_column='PhotoID', blank=True, null=True, related_name='+')
    photo_date = core.fields.DateField(db_column='PhotoDate', blank=True, null=True)
    card_issued = models.BooleanField(db_column='CardIssued')
    relationship = models.ForeignKey(
        Relation, models.DO_NOTHING, db_column='Relationship', blank=True, null=True,
        related_name='insurees')
    profession = models.ForeignKey(
        Profession, models.DO_NOTHING, db_column='Profession', blank=True, null=True,
        related_name='insurees')
    education = models.ForeignKey(
        Education, models.DO_NOTHING, db_column='Education', blank=True, null=True,
        related_name='insurees')
    type_of_id = models.ForeignKey(
        IdentificationType, models.DO_NOTHING, db_column='TypeOfId', blank=True, null=True)
    health_facility = models.ForeignKey(
        location_models.HealthFacility, models.DO_NOTHING, db_column='HFID', blank=True, null=True,
        related_name='insurees')

    offline = models.BooleanField(db_column='isOffline', blank=True, null=True)
    audit_user_id = models.IntegerField(db_column='AuditUserID')
    # row_id = models.BinaryField(db_column='RowID', blank=True, null=True)