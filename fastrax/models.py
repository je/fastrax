from django.db import models
from django.contrib.gis.db import models
from django.db.models import Manager as GeoManager
from django.contrib.gis.db.models import PolygonField, MultiPolygonField
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _
from django.core.files.storage import FileSystemStorage
import datetime
import uuid
import settings

OWNERSHIP_CHOICES = (
    ('U', 'USFS'),
    ('F', 'BLM'),
    ('O', 'Other Federal'),
    ('S', 'State, City, Muni'),
    ('P', 'Private'),
)

SPZ_CHOICES_RET = (
    ('N', 'None'),
    ('G', 'Grant\'s Pass'), 
    ('K', 'Klamath Falls'),
    ('L', 'LaGrande'),
    ('M', 'Medford'),
    ('R', 'Oak Ridge'),
    ('V', 'Lakeview'),
)

SPZ_CHOICES = (
    ('N', 'None'),
    ('K', 'Klamath Falls'),
    ('V', 'Lakeview'),
    ('M', 'Medford'),
    ('R', 'Oak Ridge'),
)

HARVESTD_CHOICES = (
    ('1', 'NA'),
    ('2', '<4"'),
    ('4', '4"'),
    ('6', '6"'),
    ('8', '8"'),
    ('9', '>8"'),
)

TYPEBURN_CHOICES = (
    ('B', 'Broadcast Activity'),
    ('F', 'Broadcast Natural'),
    ('U', 'Underburn Activity'),
    ('N', 'Underburn Natural'),
    ('H', 'Handpile'),
    ('G', 'Grapple Pile'),
    ('T', 'Tractor Pile'),
    ('L', 'Landing only'),
    ('R', 'Right-of-way'),
    ('S', 'Rangeland'),
)

FUELSPECIES_CHOICES = (
    ('D', 'Douglas-fir, Hemlock, Cedar'),
    ('P', 'Ponderosa Pine'),
    ('L', 'Lodgepole Pine'),
    ('M', 'Mixed Conifer'),
    ('H', 'Hardwood'),
    ('B', 'Brush'),
    ('J', 'Juniper'),
    ('G', 'Grass'),
    ('S', 'Sagebrush, bitterbrush'),
)

LOADMETHOD_CHOICES = (
    ('T ', 'Transect'),
    ('P1', 'PNW51'),
    ('P2', 'PNW52'),
    ('P3', 'PNW231'),
    ('P4', 'PNW258'),
    ('P5', 'PNW105'),
    ('P6', 'PNW830'),
    ('P7', 'PNW839'),
    ('L ', 'Local/other'),
    ('M ', 'Other method'),
    ('A ', 'Aerial photo'),
    ('R ', 'Random sample'),
    ('C ', 'Ocular'),
)

REASON_CHOICES = (
    ('H', 'Hazard Reduction'),
    ('S', 'Silviculture'),
    ('F', 'Forest Health'),
    ('W', 'Wildlife Habitat'),
    ('B', 'Hazard and Silviculture'),
    ('E', 'Level 2, Fee Exempt'),
    ('M', 'Forest Health Maintenance'),
    ('R', 'Other'),
)

COUNTY_CHOICES = (
    ('01', 'Baker'),
    ('02', 'Benton'),
    ('03', 'Clackamas'),
    ('04', 'Clatsop'),
    ('05', 'Columbia'),
    ('06', 'Coos'),
    ('07', 'Crook'),
    ('08', 'Curry'),
    ('09', 'Deschutes'),
    ('10', 'Douglas'),
    ('11', 'Gilliam'),
    ('12', 'Grant'),
    ('13', 'Harney'),
    ('14', 'Hood River'),
    ('15', 'Jackson'),
    ('16', 'Jefferson'),
    ('17', 'Josephine'),
    ('18', 'Klamath'),
    ('19', 'Lake'),
    ('20', 'Lane'),
    ('21', 'Lincoln'),
    ('22', 'Linn'),
    ('23', 'Malheur'),
    ('24', 'Marion'),
    ('25', 'Morrow'),
    ('26', 'Multnomah'),
    ('27', 'Polk'),
    ('28', 'Sherman'),
    ('29', 'Tillamook'),
    ('30', 'Umatilla'),
    ('31', 'Union'),
    ('32', 'Wallowa'),
    ('33', 'Wasco'),
    ('34', 'Washington'),
    ('35', 'Wheeler'),
    ('36', 'Yamhill'),
)

IGNITION_CHOICES = (
    (' ', 'NA'),
    ('A', 'Aerial'),
    ('H', 'Hand'),
    ('C', 'Combination'),
    ('M', 'Other'),
)

THOUSANDHOUR_CHOICES = (
    (' ', 'NA'),
    ('N', 'NFDRS-th'),
    ('A', 'Adj-th'),
    ('W', 'Weighted'),
)

SNOWOFF_CHOICES = (
    (' ', 'NA'),
    ('00', 'No snowpack'),
    ('01', 'Jan'),
    ('02', 'Feb'),
    ('03', 'Mar'),
    ('04', 'Apr'),
    ('05', 'May'),
    ('06', 'Jun'),
    ('07', 'Jul'),
    ('08', 'Aug'),
    ('09', 'Sep'),
    ('10', 'Oct'),
    ('11', 'Nov'),
    ('12', 'Dec'),
)

WINDDIR_CHOICES = (
    ('  ', 'NA'),
    ('00', 'North'),
    ('02', 'NNE'),
    ('05', 'NE'),
    ('07', 'ENE'),
    ('09', 'East'),
    ('11', 'ESE'),
    ('14', 'SE'),
    ('16', 'SSE'),
    ('18', 'South'),
    ('20', 'SSW'),
    ('23', 'SW'),
    ('25', 'WSW'),
    ('27', 'West'),
    ('29', 'WNW'),
    ('32', 'NW'),
    ('34', 'NNW'),
)

LIVEFUELSTYPE_CHOICES = (
    (' ', 'NA'),
    ('B', 'Broadleaf'),
    ('E', 'Evergreen'),
    ('S', 'Sage'),
)

LITTER_CHOICES = (
    (' ', 'NA'),
    ('S', 'Short Needle Pine'),
    ('L', 'Long Needle Pine'),
    ('O', 'Other Conifer'),
    ('D', 'Deciduous Hardwood'),
    ('E', 'Evergreen Hardwood'),
    ('G', 'Grass'),
)

class SmokeRegister(models.Model):
    entered = models.DateTimeField('Created', auto_now_add=True)
    modified = models.DateTimeField('Modified', auto_now=True)
    author = models.ForeignKey(User, on_delete=models.PROTECT, to_field="id", related_name="reg_user")
    district = models.ForeignKey('District', on_delete=models.PROTECT, to_field="id", related_name="reg_district")
    revenue = models.CharField('RevNo', max_length=5, blank=True, help_text="Revenue number. Optional. Last 5 digits of notification number, used in smoke numbers for revenue smoke.")
    sn = models.CharField('SN', max_length=12, unique=True, default='10XXXXXXXXNN', help_text="Smoke number. Natural fuels is YY+406+ODFID+NN, where ODFID is the district's 5-digit ODF id, and NN is a sequence. Revenue (timber sale) is YY+ODF+REVNO+NN, where ODF is the district's 3-digit ODF id, and REVNO is the revenue number. YY is always the current calendar year, and NN is a number from 01 to 99.")
    sequence = models.IntegerField('Plan Sequence', default='01', help_text = "Unless this is an old registration from FASTRACS, leave this as '01'.")
    regname = models.CharField('Name', max_length=30, help_text="Name this registration.")
    regdate = models.DateField('Registered', auto_now_add=True)
    township = models.CharField('Township', max_length=4, default='000N', help_text="Third digit is partial section: 1/4=2 1/2=5 3/4=7 Full=0.")
    range = models.CharField('Range', max_length=4, default='000E', help_text="Third digit is partial section: 1/4=2 1/2=5 3/4=7 Full=0.")
    section = models.CharField('Section', max_length=2, default='00')
    county = models.CharField('County', max_length=2, choices=COUNTY_CHOICES)
    elevation = models.IntegerField('Elev', help_text="Average elevation to nearest 100ft.")
    slope = models.IntegerField('Slope %',  help_text="Average slope as percent.")
    ownership = models.CharField('Ownership', max_length=1, choices=OWNERSHIP_CHOICES)
    ssradistance = models.CharField('dSSRA', max_length=2, default='60', help_text="Within SSRA, enter 0. If more than 60 miles, enter 60.")
    spz = models.CharField('SPZ', max_length=1, choices=SPZ_CHOICES, help_text="Special Protection Zone.")
    fpf = models.CharField('PDNo', max_length=3, blank=True, default='   ', help_text="ODF Protection Disrict number. Optional.")
    typeburn = models.CharField('Type', max_length=1, choices=TYPEBURN_CHOICES)
    reason = models.CharField('Reason', max_length=1, choices=REASON_CHOICES)
    regacres = models.IntegerField('Acres', help_text="Acres to be treated. For pile burning, enter acres from which material was accumulated. Maximum 9999 per registration.")
    landingtons = models.IntegerField('LTons', help_text="Total tons in landing or r-o-w piles on the unit. Enter 0 if none.")
    piletons = models.IntegerField('PTons', help_text="Total tons in unit piles. Exclude landings and right-of-way. Use PNW-GTR-364 or PCOST to estimate. Enter 0 if none.")
    loadmethod = models.CharField('LoadMethod', max_length=2, choices=LOADMETHOD_CHOICES, help_text="NONPILE is T,P#,L, or M. PILE is A,R, or O.")
    fuelspecies = models.CharField('Species', max_length=1, choices=FUELSPECIES_CHOICES)
    fuelclass1 = models.IntegerField('BU fuels 0-1/4"', help_text="Broadcast/underburn 0-1/4\" fuels in tons/ac. Enter 0 if none.")
    fuelclass2 = models.IntegerField('BU fuels 1/4"-1"', help_text="Broadcast/underburn 1/4\"-1\" fuels in tons/ac. Enter 0 if none.")
    fuelclass3 = models.IntegerField('BU fuels 1"-3"',  help_text="Broadcast/underburn 1\"-3\" fuels in tons/ac. Enter 0 if none.")
    fuelclass4 = models.IntegerField('BU fuels 3"-9"', help_text="Broadcast/underburn 3\"-9\" fuels in tons/ac. Enter 0 if none.")
    fuelclass5 = models.IntegerField('BU fuels 9"-20"', help_text="Broadcast/underburn 9\"-20\" fuels in tons/ac. Enter 0 if none.")
    fuelclass6 = models.IntegerField('BU fuels 20+"', help_text="Broadcast/underburn 20+\" fuels. in tons/ac. Enter 0 if none.")
    duffdepth = models.IntegerField('Duff depth', help_text="In tenths of inches.")
    harvestd = models.CharField('Harvest spec', max_length=1, choices=HARVESTD_CHOICES)
    cutdate = models.DateField('Cut date', default='YYYY-MM-DD', help_text="Date when 70% complete. Enter 1900-01-01 if none.")
    livefuelstype = models.CharField('Live Fuels Type', max_length=1, blank=True, null=True, choices=LIVEFUELSTYPE_CHOICES)
    livefuelscoveragepercent = models.IntegerField('Live Fuels Coverage Percent', blank=True, null=True, help_text="Live fuels coverage. Enter 0 if none.")
    livefuelsheight = models.IntegerField('Live Fuels Height', blank=True, null=True, help_text="Live fuels height in 10ths of feet. Enter 0 if none.")
    livefuelstonsperacre = models.IntegerField('Live Fuels Tons Per Acre', blank=True, null=True, help_text="Live fuels tons/ac. Enter 0 if none.")
    rottenstumpsdiameter = models.IntegerField('Rotten Stumps Diameter', blank=True, null=True, help_text="Rotten stump diameter in inches.")
    rottenstumpsheight = models.IntegerField('Rotten Stumps Height', blank=True, null=True, help_text="Rotten stumps height in feet.")
    rottenstumpsdensityperacre = models.IntegerField('Rotten Stumps Density Per Acre', blank=True, null=True, help_text="Stumps per acre.")
    rottendeadsurfacefuel3to9 = models.IntegerField('Rotten Dead Surface Fuel 3 to 9',  blank=True, null=True, help_text="Tons per acre.")
    rottendeadsurfacefuel9to20 = models.IntegerField('Rotten Dead Surface Fuel 9 to 20', blank=True, null=True, help_text="Tons per acre.")
    rottendeadsurfacefuel20 = models.IntegerField('Rotten Dead Surface Fuel 20+', blank=True, null=True, help_text="Tons per acre.")
    littertype = models.CharField('Litter Type', max_length=1, blank=True, null=True, choices=LITTER_CHOICES)
    littercoverage = models.IntegerField('Litter Coverage Percent', blank=True, null=True, help_text="Litter coverage. Enter 0 if none.")
    litterdepth = models.IntegerField('Litter Depth', blank=True, null=True, help_text="Litter depth in 10ths of inches. Enter 0 if none.")

    class Meta:
        db_table = 'django_fastrax_reg'
        verbose_name = _('burn registration')
        verbose_name_plural = _('burn registrations')
        ordering = ('sn',)

    def __unicode__(self):
        return u"%s" % (self.sn)

    def __str__(self):
        return u"%s" % (self.sn)

    def get_absolute_url(self):
        return "/%s/" % self.sn

class SmokePlan(models.Model):
    author = models.ForeignKey(User, on_delete=models.PROTECT, to_field="id", related_name="plan_user")
    entered = models.DateTimeField('Created', auto_now_add=True)
    sn = models.ForeignKey('SmokeRegister', on_delete=models.PROTECT, to_field="sn", related_name="plan_sn", help_text="Smoke number of registration.")
    suffix = models.CharField ('##', max_length=2, help_text = "Plan number. First ## on any registration is '01'.")
    snid = models.CharField('SN-##', max_length=15, unique=True, help_text="Smoke number with plan number appended.")
    acrestoburn = models.IntegerField('Acres', help_text="Acres to burn this plan. May not be total acres in unit.")
    landingtons = models.IntegerField('LTons', help_text="Landing tons to be burned this plan. Enter 0 if none.")
    piletons = models.IntegerField('PTons', help_text="Pile tons to be burned this plan. Enter 0 if none.")
    b_u_tonsperacre = models.IntegerField('BUTons/a', help_text="Broadcast and underburn tons/acre to be burned this plan. Enter 0 if none.")
    ignitiondate = models.DateField('Date', default='YYYY-MM-DD', help_text="Planned ignition date.")
    ignitiontime = models.TimeField('Time', default='HH:MM', help_text="Planned ignition time.")
    plan_date = models.DateField('Planned', auto_now_add=True)

    class Meta:
        db_table = 'django_fastrax_plan'
        verbose_name = _('daily burn plan')
        verbose_name_plural = _('daily burn plans')
        ordering = ('plan_date',)

    def __unicode__(self):
        return u"%s-%s" % (self.sn, self.suffix)

    def __str__(self):
        return u"%s-%s" % (self.sn, self.suffix)

    def get_absolute_url(self):
        return "/%s/%s/" % (self.sn, self.suffix)

NO_CHOICES = (
    ('L', 'Smoke Management Plan limitations'),
    ('M', 'meteorology not in burn prescription'),
    ('R', 'lack of available resources'),
    ('P', 'resources reassigned to other priorities'),
    ('S', 'shortened Rx burn season'),
    ('O', 'other'),
)

class SmokeResult(models.Model):
    author = models.ForeignKey(User, on_delete=models.PROTECT, to_field="id", related_name="result_user")
    entered = models.DateTimeField('Entered', auto_now_add=True)
    modified = models.DateTimeField('Modified', auto_now=True)
    snid = models.OneToOneField('SmokePlan', on_delete=models.PROTECT, related_name="result_snid")
    notaccomplished = models.BooleanField('Not accomplished?', help_text="Still need to zero out required fields for now.")
    acresburned = models.IntegerField('Acres', help_text="Acres burned (blackened). May be more or less than planned. Enter 0 if none.")
    landingtonned = models.IntegerField('LTons', help_text="Landing tons burned this plan. Enter 0 if none.")
    piletonned = models.IntegerField('PTons', help_text="Pile tons burned this plan. Enter 0 if none.")
    b_u_tonsperacred = models.IntegerField('BUTons/a', help_text="Broadcast and underburn tons per acre burned this plan. Enter 0 if none.")
    ignitiondated = models.DateField('Date', default='YYYY-MM-DD', help_text="Actual ignition date.")
    ignitiontimed = models.TimeField('Time', default='HH:MM', help_text="Actual ignition time.")
    ignitionmethod = models.CharField('Method', max_length=1, choices=IGNITION_CHOICES, help_text="NA for pile burns.")
    ignitionduration = models.IntegerField('Duration', help_text="Minutes from first ignition to finish. Include breaks in total. Enter 0 for pile burns.")
    rapidignition = models.BooleanField('Rapid ignition?', help_text="")
    smokeintrusion = models.BooleanField('Smoke intrusion?')
    weatherstation = models.CharField('Weather', max_length=4, blank=True, help_text="Enter initial 4-characters of RAWS name, last 4 digits of RAWS number, or UNIT for on-site observation. Not required for pile burns.")
    airtemperature = models.IntegerField('F', help_text="Air temperature in whole Farenheit degrees. Enter 0 for pile burns.")
    relativehumidity = models.IntegerField('RH', help_text="Percent relative humidity. Enter 0 for pile burns.")
    winddirection = models.CharField('Wind dir', max_length=2, choices=WINDDIR_CHOICES, help_text="NA for pile burns.")
    windspeed = models.IntegerField('Wind mph', help_text="Enter 0 for pile burns.")
    tenhour = models.IntegerField('10hr', help_text="Ten-hour moisture. Whole number for quarter- to one-inch fuels. Enter 0 for pile burns.")
    thousandhour = models.IntegerField('1000hr', help_text="Thousand-hour moisture. Whole number for 3- to 9-inch fuels. Enter 0 for pile burns.")
    thousandhourmethod = models.CharField('1000hrM', max_length=1, choices=THOUSANDHOUR_CHOICES, help_text="Thousand-hour method. NA for pile burns.")
    dayssincerain = models.IntegerField('Rain', help_text="Western Oregon = days since 0.50-inch rain in 48 hrs; Eastern Oregon = days since 0.25-inch rain in 48 hrs. Not required (enter 0) for pile burns.")
    snowoffmonth = models.CharField('Snow off month', max_length=2, choices=SNOWOFF_CHOICES, help_text="NA for pile burns.")
    result_date = models.DateField('Resulted', auto_now_add=True)
    no = models.CharField('Reason', max_length=1, choices=NO_CHOICES, help_text="Non-accomplishment reason.")
    why = models.TextField('Details', max_length=1024, blank=True, null=True, help_text="Non-accomplishment details.", )
    b_u_tonsburned = models.IntegerField('BroadcastTonsBurned', blank=True, null=True, help_text="NEW")
    shrubconsumption = models.IntegerField('ShrubConsumption', blank=True, null=True, help_text="NEW")
    duffmoisture = models.IntegerField('DuffFuelMoisture', blank=True, null=True, help_text="NEW")

    class Meta:
        db_table = 'django_fastrax_result'
        verbose_name = _('daily burn result')
        verbose_name_plural = _('daily burn results')
        ordering = ('result_date',)

    def __unicode__(self):
        return u"%s" % (self.snid)

    def __str__(self):
        return u"%s" % (self.snid)

    def get_absolute_url(self):
        return "/%s/%s/" % (self.snid.sn, self.snid.suffix)

class District(models.Model):
    tla = models.CharField('TLA', max_length=3, help_text="UberDistrict(or Forest) TLA.")
    name = models.CharField('District', unique=True, max_length=40, help_text="District name.")
    slug = models.CharField('Slug', unique=True, max_length=40, help_text="No spaces.")
    nnn = models.CharField('NNN', max_length=3, help_text="Three-digit district ID. Usually unique.")
    odfid = models.CharField('ODF406', max_length=5, help_text="Five-digit ODF ID.")
    tin = models.CharField('TIN', max_length=8, help_text="ODF TIN.")
    fedunit = models.CharField('Fed Unit', max_length=6, help_text="Six-digit Fed Unit Code.")
    address = models.CharField('Address', max_length=80, blank=True, null=True, help_text="Address.")
    city = models.CharField('City', max_length=80, blank=True, null=True, help_text="City.")
    state = models.CharField('State', max_length=2, blank=True, null=True, help_text="State.")
    zip4 = models.CharField('Zip', max_length=10, blank=True, null=True, help_text="Zip code.")
    tel = models.CharField('Telephone', max_length=10, blank=True, null=True, help_text="Telephone.")

    class Meta:
        db_table = 'django_fastrax_district'
        verbose_name = _('district')
        verbose_name_plural = _('districts')
        ordering = ('tla',)

    def __unicode__(self):
        return u"%s %s" % (self.tla, self.name)

    def __str__(self):
        return u"%s %s" % (self.tla, self.name)

    def get_absolute_url(self):
        return "/district/%s/%s/" % (self.tla.lower(), self.slug)

class PLSS(models.Model):
    trs = models.CharField(max_length=20)
    township = models.CharField('Township', max_length=4, help_text="Like ###D. Third digit: 1/4=2 1/2=5 3/4=7 Full=0.")
    range = models.CharField('Range', max_length=4, help_text="Like ###D. Third digit: 1/4=2 1/2=5 3/4=7 Full=0.")
    section = models.CharField('Section', max_length=2, help_text="Like ##.")
    x = models.CharField(max_length=20)
    y = models.CharField(max_length=20)
    mix = models.CharField(max_length=20)
    miy = models.CharField(max_length=20)
    max = models.CharField(max_length=20)
    may = models.CharField(max_length=20)
    #geometry = models.MultiPointField('PLSS',srid=4326)
    geometry = models.PolygonField('Geometry',srid=4326)
    #objects = models.GeoManager()

    class Meta:
        db_table = 'django_fastrax_plss'
        verbose_name = _('PLSS')
        verbose_name_plural = _('PLSSs')
        ordering = ('trs',)

    def __unicode__(self):
        return u"%s" % (self.trs)

    def __str__(self):
        return u"%s" % (self.trs)

class ODFSSRA(models.Model):
    name = models.CharField('SSRA Name', max_length=80, )
    slug = models.CharField('Slug', unique=True, max_length=80, help_text="No spaces.")
    geometry = models.PolygonField('Geometry',srid=4326)
    objects = GeoManager()

    class Meta:
        db_table = 'django_fastrax_odfssra'
        verbose_name = _('ODF SSRA')
        verbose_name_plural = _('ODF SSRAs')

    def __unicode__(self):
        return u"%s" % (self.name)

    def __str__(self):
        return u"%s" % (self.name)

class ODFSPZ(models.Model):
    name = models.CharField('SPZ Name', max_length=80, )
    slug = models.CharField('Slug', unique=True, max_length=80, help_text="No spaces.")
    geometry = models.PolygonField('Geometry',srid=4326)
    objects = GeoManager()

    class Meta:
        db_table = 'django_fastrax_odfspz'
        verbose_name = _('ODF SPZ')
        verbose_name_plural = _('ODF SPZs')

    def __unicode__(self):
        return u"%s" % (self.slug)

    def __str__(self):
        return u"%s" % (self.slug)

class ODFPD(models.Model):
    nnn = models.CharField('ODF id', max_length=3, help_text="ODF id.")
    name = models.CharField('PD Name', max_length=80, help_text="District name.")
    slug = models.CharField('Slug', unique=True, max_length=80, help_text="No spaces.")
    geometry = models.MultiPolygonField('Geometry',srid=4326)
    objects = GeoManager()

    class Meta:
        db_table = 'django_fastrax_odfpd'
        verbose_name = _('ODF protection district')
        verbose_name_plural = _('ODF protection districts')
        ordering = ('nnn',)

    def __unicode__(self):
        return u"%s" % (self.slug)

    def __str__(self):
        return u"%s" % (self.slug)

LMH = (
    ('L', 'Low'),
    ('M', 'Med'),
    ('H', 'High'),
)

PSA = (
    ('NW01', 'NW01'),
    ('NW02', 'NW02'),
    ('NW03', 'NW03'),
    ('NW04', 'NW04'),
    ('NW05', 'NW05'),
    ('NW06', 'NW06'),
    ('NW07', 'NW07'),
    ('NW08', 'NW08'),
    ('NW09', 'NW09'),
    ('NW10', 'NW10'),
    ('NW11', 'NW11'),
    ('NW12', 'NW12'),

)

PRE = (
    ('FD', 'Fire Director'),
    ('SFMO', 'State Fire Management Officer'),
)

FIN = (
    ('SD', 'State Director'),
    ('RF', 'Regional Forester'),
    ('DSD', 'Deputy State Director'),
    ('DRF', 'Deputy Regional Forester'),
)

fs = FileSystemStorage(location=settings.UFS)

def get_userpath(instance, filename):
    return str(instance.user.username + "/" + filename)

def make_uuid():
    return str(uuid.uuid4())

def get_path(instance, filename):
    ext = filename.split('.')[-1]
    #front = filename.split('.')[0]
    #front = str(unicodedata.normalize('NFKD', front).encode('ascii', 'ignore'))
    #front = re.sub('[^\w\s-]', '', front).strip().lower()
    #front = re.sub('[-\s]+', '-', front)
    #front = re.sub('^b', '', front)
    filename = "%s.%s" % (uuid.uuid4(), ext)
    #when = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    #filename = "%s-%s.%s" % (front, when, ext)
    #return os.path.join('uploads/logos', filename)
    return str(filename)

class PlusFour(models.Model):
    created = models.DateTimeField('Created', auto_now_add=True)
    modified = models.DateTimeField('Modified', auto_now=True)
    author = models.ForeignKey(User, on_delete=models.PROTECT, related_name="plusfour_author")
    district = models.ForeignKey('District', on_delete=models.PROTECT, to_field="id", related_name="plusfour_district")
    name = models.CharField('Project Name', max_length=30, help_text="")
    township = models.CharField('Township', max_length=4, default='000N', help_text="Third digit is partial section: 1/4=2 1/2=5 3/4=7 Full=0.")
    range = models.CharField('Range', max_length=4, default='000E', help_text="Third digit is partial section: 1/4=2 1/2=5 3/4=7 Full=0.")
    section = models.CharField('Section', max_length=2, default='00')
    acres = models.IntegerField('Acres', help_text="")
    objective = models.TextField('Prescribed Burn Objectives and Project Summary', max_length=1024, blank=True, null=True, help_text="Enter Prescribed Burn Plan Objectives and Summary", )
    ignitionstart = models.DateField('Planned Ignition Start Date', default='YYYY-MM-DD', help_text="")
    ignitionend = models.DateField('Planned Ignition Completion Date', default='YYYY-MM-DD', help_text="")
    mopdays = models.IntegerField('Number of days expected for Mop-up and Patrol', help_text="")
    mopend = models.DateField('Expected Completion Date', default='YYYY-MM-DD', help_text="")
    complexity = models.CharField('Final Complexity Alalysis Rating', max_length=1, choices=LMH, help_text="")
    compsum = models.TextField('Complexity Summary', max_length=1024, blank=True, null=True, help_text="Summary of risks that rated high and cannot be mitigated.", )
    risk = models.CharField('Risk Rating', max_length=1, choices=LMH, help_text="")
    risksum = models.TextField('Risk Summary', max_length=1024, blank=True, null=True, help_text="Summary of elements rated as high and associated mitigation measures.", )
    cons = models.CharField('Consequences Rating', max_length=1, choices=LMH, help_text="")
    conssum = models.TextField('Consequences Summary', max_length=1024, blank=True, null=True, help_text="Summary of elements rated as high and associated mitigation measures.", )
    technical = models.CharField('Technical Difficulties Rating', max_length=1, choices=LMH, help_text="")
    technicalsum = models.TextField('Technical Difficulties Summary', max_length=1024, blank=True, null=True, help_text="Summary of elements rated as high and associated mitigation measures.", )
    rn1 = models.BooleanField('Will local fire resources be sufficient for the duration of the project?', help_text="")
    rn2 = models.BooleanField('Will the use of local resources affect IA response on the forest or districts?', help_text="")
    rn3 = models.BooleanField('Will the local unit need support from outside fire resources for ignition?', help_text="")
    rn4 = models.BooleanField('Will the local unit need support from outside fire resources for mop-up?', help_text="")
    rn5 = models.BooleanField('Will the local unit need support from outside fire resources for patrol?', help_text="")
    rdetail = models.TextField('Resource Details', max_length=1024, blank=True, null=True, help_text="If yes to 3, 4, or 5 identify resources needed, their home unit and number of operational periods needed. List resource and type, home unit, expected operational periods needed, and release date.", )
    cn1 = models.BooleanField('Have contingency resources been identified for the duration of the project?', help_text="")
    cn2 = models.BooleanField('Are contingency resources available from your local unit or area?', help_text="")
    cn3 = models.BooleanField('If contingency resources are from another geographic area have they been notified and are they available to respond if needed?', help_text="")
    cdetail = models.TextField('Contingency Details', max_length=1024, blank=True, null=True, help_text="Identify contingency resources. List resource and type, home unit, expected response time.", )
    psa = models.CharField('PNW Predictive Service Area Identifier', max_length=4, choices=PSA, help_text="")
    forecast = models.TextField('Weather Forecast Summary for Ignition Period', max_length=1024, blank=True, null=True, help_text="",)
    plan = models.BooleanField('Are the burn plan environmental parameters within prescription?', help_text="")
    longrange = models.TextField('Long Range Forecast', max_length=1024, blank=True, null=True, help_text="", )
    are = models.BooleanField('Are there any indicators in the forecast that could affect the ability to mop-up and control prescribed fire within the timeframes identified above?', help_text="")
    measures = models.TextField('If yes, please describe any mitigation measures that would be put into place', max_length=1024, blank=True, null=True, help_text="", )
    lo = models.CharField('Line Officer Signature', max_length=200, help_text="")
    lodate = models.DateField('Signature Date', help_text="")
    dfmo = models.CharField('District Fire Management Officer Signature', max_length=200, blank=True, null=True, help_text="")
    dfmodate = models.DateField('Signature Date', blank=True, null=True, help_text="")
    gmacdate = models.DateField('This request has been reviewed by the PNW Geographic Multi-Agency Coordinating Group (GMAC). Review Date.', blank=True, null=True, help_text="")
    gmaccom = models.TextField('GMAC Comments', max_length=1024, blank=True, null=True, help_text="",)
    nmacdate = models.DateField('This request has been reviewed by the National Multi-Agency Coordinating Group (NMAC). Review Date.', blank=True, null=True, help_text="")
    nmaccom = models.TextField('NMAC Comments', max_length=1024, blank=True, null=True, help_text="",)
    preapp = models.NullBooleanField('Preliminary Approval', blank=True, null=True, help_text="")
    pre = models.CharField('Preliminary Approval Signature', max_length=200, blank=True, null=True, help_text="")
    predate = models.DateField('Signature Date', blank=True, null=True, help_text="")
    preoff = models.CharField('Preliminary Aapproval Office', max_length=4, choices=PRE, blank=True, null=True, help_text="")
    finapp = models.NullBooleanField('Final Approval', blank=True, null=True, help_text="")
    fin = models.CharField('Final Approval Signature', max_length=200, blank=True, null=True, help_text="")
    findate = models.DateField('Signature Date', blank=True, null=True, help_text="")
    finoff = models.CharField('Final Approval Office', max_length=4, choices=FIN, blank=True, null=True, help_text="")
    reqfile = models.FileField('File', storage=fs, upload_to=get_path, blank=True,)
    appfile = models.FileField('File', storage=fs, upload_to=get_path, blank=True,)
    remarks = models.TextField('Remarks', max_length=1024, blank=True, null=True, help_text="Enter comments you want to accompany this row of data.", )

    class Meta:
        db_table = 'django_fastrax_plusfour'
        verbose_name = _('plus four')
        verbose_name_plural = _('plus fours')
        ordering = ('-ignitionstart','-ignitionend','-findate','-predate','-nmacdate','-gmacdate','-dfmodate','-lodate',)

    def __unicode__(self):
        return u"%s" % (self.id)

    def get_absolute_url(self):
        return "/plusfour/%s/" % (self.id)

    @property
    def is_past(self):
        if datetime.date.today() > self.ignitionstart:
            return True
        return False

STATUS_CHOICES = (
    ('D', 'Debug'),
    ('I', 'Info'),
    ('S', 'Success'),
    ('W', 'Warning'),
    ('E', 'Error'),
)

class Logitem(models.Model):
    created = models.DateTimeField('Created', auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.PROTECT)
    status = models.CharField('Status', max_length=1, choices=STATUS_CHOICES)
    message = models.TextField('Message',)
    obj_model = models.CharField('Model', max_length=80, help_text="Object model.", )
    obj_id = models.CharField('Object', max_length=999, help_text="Object id.", )
    obj_in = models.TextField('Object In', blank=True, null=True, help_text="Serialized in.", )
    obj_out = models.TextField('Object Out', blank=True, null=True, help_text="Serialized out.", )

    class Meta:
        db_table = 'django_fastrax_logitem'
        verbose_name = _('log item')
        verbose_name_plural = _('log items')
        ordering = ('-created',)