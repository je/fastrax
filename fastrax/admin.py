from django import forms
from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from leaflet.admin import LeafletGeoAdmin
from django.forms.widgets import TextInput
from django.contrib.gis.db import models
#from olwidget.admin import GeoModelAdmin
from guardian.admin import GuardedModelAdmin
from fastrax.models import *
from django.utils.translation import ugettext_lazy as _

class SmokeRegisterAdmin(admin.ModelAdmin):
    list_display = ('sn', 'regname', 'district', 'regacres', 'township', 'range', 'section', 'spz', 'regdate', 'author')
    ordering = ['-regdate']
    list_per_page = 50
    search_fields = ('sn', 'regname')
    date_hierarchy = 'regdate'
    list_filter = ('author', 'district')
    list_display_links = ('sn',)
    list_editable = ('regacres', 'township', 'range', 'section','spz')
    fieldsets = (
        (_('Identity'), {'fields': (('author', 'district'), ('revenue', 'sn', 'sequence'), ('regname',), ('township', 'range', 'section'), ('county', 'elevation', 'slope'), ('ownership', 'ssradistance', 'spz', 'fpf'))}),
        (_('Activity'), {'fields': (('typeburn', 'reason'), ('regacres', 'landingtons', 'piletons', 'loadmethod'))}),
        (_('Fuel Observation'), {'fields': (('fuelspecies', 'harvestd', 'cutdate'), ('fuelclass1', 'fuelclass2', 'fuelclass3', 'fuelclass4', 'fuelclass5', 'fuelclass6', 'duffdepth'))}),
    )
    save_as = True

admin.site.register(SmokeRegister, SmokeRegisterAdmin)

class SmokePlanAdmin(admin.ModelAdmin):
    list_display = ('author','snid', 'suffix','acrestoburn', 'landingtons', 'piletons', 'b_u_tonsperacre', 'ignitiondate', 'ignitiontime', 'plan_date', 'author')
    ordering = ['-plan_date']
    list_per_page = 50
    search_fields = ('snid',)
    date_hierarchy = 'plan_date'
    list_filter = ('author',)
    list_editable = ('snid', 'suffix', 'acrestoburn', 'landingtons', 'piletons', 'b_u_tonsperacre', 'ignitiondate', 'ignitiontime')
    prepopulated_fields = {"snid": ("sn","suffix")}
    save_as = True

admin.site.register(SmokePlan, SmokePlanAdmin)

class SmokeResultAdmin(admin.ModelAdmin):
    list_display = ('snid', 'acresburned', 'landingtonned', 'piletonned', 'b_u_tonsperacred', 'ignitiondated', 'ignitiontimed', 'result_date', 'author')
    ordering = ['-result_date']
    list_per_page = 50
    search_fields = ('snid',)
    date_hierarchy = 'result_date'
    list_filter = ('author', 'notaccomplished')
    list_editable = ('acresburned', 'landingtonned', 'piletonned', 'b_u_tonsperacred', 'ignitiondated', 'ignitiontimed')
    save_as = True

admin.site.register(SmokeResult, SmokeResultAdmin)

class DistrictAdmin(admin.ModelAdmin):
    list_display = ('state', 'tla', 'name', 'slug', 'tin', 'fedunit', 'nnn', 'odfid')
    list_display_links = ('tla',)
    ordering = ['tla']
    list_per_page = 50
    list_filter = ('state','tla',)
    list_editable = ('state', 'name', 'slug', 'tin', 'fedunit', 'nnn', 'odfid')
    save_as = True

admin.site.register(District, DistrictAdmin)

class PLSSAdmin(LeafletGeoAdmin):
    list_display = ('trs','x','y','mix','miy','max','may')
    list_display_links = ('trs',)
    search_fields = ('trs',)
    ordering = ('trs',)
    save_as = True
    list_select_related = True
    fieldsets = (
      ('Attributes', {'fields': (('trs',),('township', 'range', 'section'),), 'classes': ('show','extrapretty')}),
      ('Coordinates', {'fields': ('x','y',), 'classes': ('wide')}),
      ('Bounding Coordinates', {'fields': ('mix','miy','max','may',), 'classes': ('wide')}),
      ('Editable Map View', {'fields': ('geometry',), 'classes': ('show', 'wide')}),
    )

admin.site.register(PLSS,PLSSAdmin)

class ODFSSRAAdmin(LeafletGeoAdmin):
    list_display = ('name',)
    list_display_links = ('name',)
    search_fields = ('name',)
    ordering = ('name',)
    save_as = True
    list_select_related = True
    fieldsets = (
      ('Identity', {'fields': ('name','slug',), 'classes': ('show','extrapretty')}),
      ('Editable Map View', {'fields': ('geometry',), 'classes': ('show', 'wide')}),
    )

admin.site.register(ODFSSRA,ODFSSRAAdmin)

class ODFSPZAdmin(LeafletGeoAdmin):
    list_display = ('name','slug',)
    list_display_links = ('name',)
    search_fields = ('name',)
    ordering = ('name',)
    save_as = True
    list_select_related = True
    fieldsets = (
      ('Identity', {'fields': ('name','slug',), 'classes': ('show','extrapretty')}),
      ('Editable Map View', {'fields': ('geometry',), 'classes': ('show', 'wide')}),
    )

admin.site.register(ODFSPZ,ODFSPZAdmin)

class ODFPDAdmin(LeafletGeoAdmin):
#class ODFPDAdmin(admin.ModelAdmin):
    list_display = ('nnn','name','slug',)
    list_display_links = ('name',)
    search_fields = ('name',)
    ordering = ('name',)
    save_as = True
    list_select_related = True
    display_raw = True
    ## formfield_overrides = {
    ##    models.MultiPolygonField: {'widget': TextInput() }
    ## }
    ## map_srid = 4326
    ## formfield_overrides = {
    ##    models.MultiPolygonField: {'widget': TextArea(attrs={'map_srid': '4326'})}
    ##}
    fieldsets = (
      ('Identity', {'fields': ('nnn','name','slug',), 'classes': ('show','extrapretty')}),
      ('Editable Map View', {'fields': ('geometry',), 'classes': ('show', 'wide')}),
    )

admin.site.register(ODFPD,ODFPDAdmin)

class LogitemAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    list_display = ('message', 'status', 'created', 'author',)
    #ordering = ['created', ]
    list_per_page = 50
    list_filter = ('status', 'obj_model', 'author', )
    #list_display_links = ('name',)
    save_as = True

admin.site.register(Logitem,LogitemAdmin)

class PlusFourAdmin(GuardedModelAdmin):
    list_display = ('name', 'district', 'created', 'author')
    ordering = ['-created']
    list_per_page = 50
    search_fields = ('name',)
    date_hierarchy = 'created'
    list_filter = ('district',)
    list_display_links = ('name',)
    save_as = True

admin.site.register(PlusFour, PlusFourAdmin)
