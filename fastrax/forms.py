from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User
from django.http import *
from fastrax.models import *
import datetime
from django.contrib.admin import widgets
from guardian.shortcuts import assign
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

class SmokeRegisterForm(forms.ModelForm):
    sn = forms.CharField(label='SN', min_length=12, max_length=12, help_text="Smoke number. Natural fuels is YY+406+ODFID+NN, where ODFID is the district's 5-digit ODF id, and NN is a sequence. Revenue (timber sale) is YY+ODF+REVNO+NN, where ODF is the district's 3-digit ODF id, and REVNO is the revenue number. YY is always the current calendar year, and NN is a number from 01 to 99.")
    township = forms.CharField(label='Township', min_length=4, max_length=4, initial='000N',help_text="Enter Township 26 North as 260N. Third digit is fractional township/range as decimal: 1/4=2 1/2=5 3/4=7 Full=0.", widget=forms.TextInput(attrs={'size':'4'}))
    range = forms.CharField(label='Range', min_length=4, max_length=4, initial='000E', help_text="Enter Range 08 West as 080W. Third digit is fractional township/range as decimal: 1/4=2 1/2=5 3/4=7 Full=0.", widget=forms.TextInput(attrs={'size':'4'}))
    elevation = forms.IntegerField(label='Elev', help_text="Average elevation to nearest 100ft.", min_value=0, max_value=9999)
    slope = forms.IntegerField(label='Slope %', help_text="Average slope as percent.", min_value=0, max_value=99)
    regacres = forms.IntegerField(label='Acres', min_value=1, max_value=9999, help_text="Acres to be treated. For pile burning, enter acres from which material was accumulated. Maximum 9999 per registration.")
    landingtons = forms.IntegerField(label='LTons', min_value=0, max_value=9999, help_text="Total tons in landing or r-o-w piles on the unit. Enter 0 if none.")
    piletons = forms.IntegerField(label='PTons', min_value=0, max_value=9999, help_text="Total tons in unit piles. Exclude landings and right-of-way. Use PNW-GTR-364 or PCOST to estimate. Enter 0 if none.")
    fuelclass1 = forms.IntegerField(label='BU fuels 0-1/4"', min_value=0, max_value=99, help_text="Broadcast/underburn 0-1/4\" fuels in tons/ac. Enter 0 if none.")
    fuelclass2 = forms.IntegerField(label='BU fuels 1/4"-1"', min_value=0, max_value=99, help_text="Broadcast/underburn 1/4\"-1\" fuels in tons/ac. Enter 0 if none.")
    fuelclass3 = forms.IntegerField(label='BU fuels 1"-3"', min_value=0, max_value=99, help_text="Broadcast/underburn 1\"-3\" fuels in tons/ac. Enter 0 if none.")
    fuelclass4 = forms.IntegerField(label='BU fuels 3"-9"', min_value=0, max_value=99, help_text="Broadcast/underburn 3\"-9\" fuels in tons/ac. Enter 0 if none.")
    fuelclass5 = forms.IntegerField(label='BU fuels 9"-20"', min_value=0, max_value=999, help_text="Broadcast/underburn 9\"-20\" fuels in tons/ac. Enter 0 if none.")
    fuelclass6 = forms.IntegerField(label='BU fuels 20+"', min_value=0, max_value=999, help_text="Broadcast/underburn 20+\" fuels. in tons/ac. Enter 0 if none.")
    duffdepth = forms.IntegerField(label='Duff depth', min_value=0, max_value=999, help_text="In tenths of inches.")
    class Meta:
        model = SmokeRegister
        exclude = ['author']

numeric = RegexValidator(r'^[0-9]*$', 'Only numeric characters are allowed.')

class SmokeRegisterFormSN1(forms.ModelForm):
    sn = forms.CharField(label='SN', min_length=12, max_length=12, help_text="Smoke number. Natural fuels is YY+406+ODFID+NN, where ODFID is the district's 5-digit ODF id, and NN is a sequence. Revenue (timber sale) is YY+ODF+REVNO+NN, where ODF is the district's 3-digit ODF id, and REVNO is the revenue number. YY is always the current calendar year, and NN is a number from 01 to 99.")
    township = forms.CharField(label='Township', min_length=4, max_length=4, initial='000N',help_text="Enter Township 26 North as 260N. Third digit is fractional township/range as decimal: 1/4=2 1/2=5 3/4=7 Full=0.", widget=forms.TextInput(attrs={'size':'4'}))
    range = forms.CharField(label='Range', min_length=4, max_length=4, initial='000E', help_text="Enter Range 08 West as 080W. Third digit is fractional township/range as decimal: 1/4=2 1/2=5 3/4=7 Full=0.", widget=forms.TextInput(attrs={'size':'4'}))
    section = forms.CharField(label='Section', min_length=2, max_length=2, widget=forms.TextInput(attrs={'size':'2'}))
    elevation = forms.IntegerField(label='Elev', help_text="Average elevation to nearest 100ft.", min_value=0, max_value=9999, widget=forms.TextInput(attrs={'size':'4'}))
    slope = forms.IntegerField(label='Slope %', help_text="Average slope as percent.", min_value=0, max_value=99, widget=forms.TextInput(attrs={'size':'2'}))
    ssradistance = forms.IntegerField(label='Distance to SSRA', help_text="Within SSRA, enter 0. If more than 60 miles, enter 60.", min_value=0, max_value=60, widget=forms.TextInput(attrs={'size':'2'}))
    revenue = forms.CharField(label='RevNo', min_length=5, max_length=5, required=False, help_text="Revenue number. Last 5 digits of tax notification number; REQUIRED for revenue smoke. Leave blank for natural fuels smoke.", validators=[numeric], widget=forms.TextInput(attrs={'size':'5'}))
    regacres = forms.IntegerField(label='Acres', min_value=1, max_value=9999, help_text="Acres to be treated. For pile burning, enter acres from which material was accumulated. Maximum 9999 per registration.", widget=forms.TextInput(attrs={'size':'4'}))
    landingtons = forms.IntegerField(label='LTons', min_value=0, max_value=9999, help_text="Total tons in landing or r-o-w piles on the unit. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'4'}))
    piletons = forms.IntegerField(label='PTons', min_value=0, max_value=9999, help_text="Total tons in unit piles. Exclude landings and right-of-way. Use PNW-GTR-364 or PCOST to estimate. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'4'}))
    fuelclass1 = forms.IntegerField(label='BU fuels 0-1/4"', min_value=0, max_value=99, help_text="Broadcast/underburn 0-1/4\" fuels in tons/ac. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'2'}))
    fuelclass2 = forms.IntegerField(label='BU fuels 1/4"-1"', min_value=0, max_value=99, help_text="Broadcast/underburn 1/4\"-1\" fuels in tons/ac. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'2'}))
    fuelclass3 = forms.IntegerField(label='BU fuels 1"-3"', min_value=0, max_value=99, help_text="Broadcast/underburn 1\"-3\" fuels in tons/ac. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'2'}))
    fuelclass4 = forms.IntegerField(label='BU fuels 3"-9"', min_value=0, max_value=99, help_text="Broadcast/underburn 3\"-9\" fuels in tons/ac. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'2'}))
    fuelclass5 = forms.IntegerField(label='BU fuels 9"-20"', min_value=0, max_value=999, help_text="Broadcast/underburn 9\"-20\" fuels in tons/ac. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'3'}))
    fuelclass6 = forms.IntegerField(label='BU fuels 20+"', min_value=0, max_value=999, help_text="Broadcast/underburn 20+\" fuels. in tons/ac. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'3'}))
    duffdepth = forms.IntegerField(label='Duff depth', min_value=0, max_value=999, help_text="In tenths of inches.", widget=forms.TextInput(attrs={'size':'3'}))
    class Meta:
        model = SmokeRegister
        exclude = ['author', 'district', 'sequence']

class SmokeRegisterFormSN(forms.ModelForm):
    regname = forms.CharField(label='Name', max_length=30, help_text="Name this registration.", widget=forms.TextInput(attrs={'size':'30'}))
    township = forms.CharField(label='Township', min_length=4, max_length=4, initial='000N',help_text="Enter Township 26 North as 260N. Third digit is fractional township/range as decimal: 1/4=2 1/2=5 3/4=7 Full=0.", widget=forms.TextInput(attrs={'size':'4'}))
    range = forms.CharField(label='Range', min_length=4, max_length=4, initial='000E', help_text="Enter Range 08 West as 080W. Third digit is fractional township/range as decimal: 1/4=2 1/2=5 3/4=7 Full=0.", widget=forms.TextInput(attrs={'size':'4'}))
    section = forms.CharField(label='Section', min_length=2, max_length=2, widget=forms.TextInput(attrs={'size':'2'}))
    elevation = forms.IntegerField(label='Elev', help_text="Average elevation to nearest 100ft.", min_value=0, max_value=9999, widget=forms.TextInput(attrs={'size':'4'}))
    slope = forms.IntegerField(label='Slope %', help_text="Average slope as percent.", min_value=0, max_value=99, widget=forms.TextInput(attrs={'size':'2'}))
    ssradistance = forms.IntegerField(label='Distance to SSRA', help_text="Within SSRA, enter 0. If more than 60 miles, enter 60.", min_value=0, max_value=60, widget=forms.TextInput(attrs={'size':'2'}))
    revenue = forms.CharField(label='RevNo', min_length=5, max_length=5, required=False, help_text="Revenue number. Last 5 digits of tax notification number; REQUIRED for revenue smoke. Leave blank for natural fuels smoke.", validators=[numeric], widget=forms.TextInput(attrs={'size':'5'}))
    fpf = forms.CharField(label='PDNo', min_length=3, max_length=3, help_text="ODF Protection Disrict number. Required.", widget=forms.TextInput(attrs={'size':'3'}))
    regacres = forms.IntegerField(label='Acres', min_value=1, max_value=9999, help_text="Acres to be treated. For pile burning, enter acres from which material was accumulated. Maximum 9999 per registration.", widget=forms.TextInput(attrs={'size':'4'}))
    landingtons = forms.IntegerField(label='LTons', required=True, min_value=0, max_value=9999, help_text="Total tons in landing or r-o-w piles on the unit. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'4'}))
    piletons = forms.IntegerField(label='PTons', required=True, min_value=0, max_value=9999, help_text="Total tons in unit piles. Exclude landings and right-of-way. Use PNW-GTR-364 or PCOST to estimate. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'4'}))
    fuelclass1 = forms.IntegerField(label='BU fuels 0-1/4"', required=True, min_value=0, max_value=99, help_text="Broadcast/underburn 0-1/4\" fuels in tons/ac. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'2'}))
    fuelclass2 = forms.IntegerField(label='BU fuels 1/4"-1"', required=True, min_value=0, max_value=99, help_text="Broadcast/underburn 1/4\"-1\" fuels in tons/ac. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'2'}))
    fuelclass3 = forms.IntegerField(label='BU fuels 1"-3"', required=True, min_value=0, max_value=99, help_text="Broadcast/underburn 1\"-3\" fuels in tons/ac. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'2'}))
    fuelclass4 = forms.IntegerField(label='BU fuels 3"-9"', required=True, min_value=0, max_value=99, help_text="Broadcast/underburn 3\"-9\" fuels in tons/ac. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'2'}))
    fuelclass5 = forms.IntegerField(label='BU fuels 9"-20"', required=True, min_value=0, max_value=999, help_text="Broadcast/underburn 9\"-20\" fuels in tons/ac. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'3'}))
    fuelclass6 = forms.IntegerField(label='BU fuels 20+"', required=True, min_value=0, max_value=999, help_text="Broadcast/underburn 20+\" fuels. in tons/ac. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'3'}))
    duffdepth = forms.IntegerField(label='Duff depth', min_value=0, max_value=999, help_text="In tenths of inches.", widget=forms.TextInput(attrs={'size':'3'}))
    class Meta:
        model = SmokeRegister
        exclude = ['sn','author','district','sequence']

    def clean(self):
        cleaned_data = self.cleaned_data
        t = cleaned_data.get("township")
        r = cleaned_data.get("range")
        s = cleaned_data.get("section")
        if t and r and s:
            try:
                plss = PLSS.objects.get(
                    Q(township=t.upper()),
                    Q(range=r.upper()),
                    Q(section=s.zfill(2))
                    )
            except ObjectDoesNotExist:
                plss = None
                msg = u"PLSS not found. Enter a valid township, range, and section."
                self._errors["township"] = self.error_class([msg])
                self._errors["range"] = self.error_class([msg])
                self._errors["section"] = self.error_class([msg])
        else:
            msg = u"PLSS not found. Enter a valid township, range, and section."
            self._errors["township"] = self.error_class([msg])
            self._errors["range"] = self.error_class([msg])
            self._errors["section"] = self.error_class([msg])
        fpf = cleaned_data.get("fpf")
        if fpf.endswith('XX'):
            msg = u"Please use the correct ODF Protection District number."
            self._errors["fpf"] = self.error_class([msg])
            #raise forms.ValidationError("Please use the correct ODF Protection District number.")

        piletons = cleaned_data.get("piletons")
        piletons = int(piletons or 0)
        landingtons = cleaned_data.get("landingtons")
        landingtons = int(landingtons or 0)
        fuelclass1 = cleaned_data.get("fuelclass1")
        fuelclass2 = cleaned_data.get("fuelclass2")
        fuelclass3 = cleaned_data.get("fuelclass3")
        fuelclass4 = cleaned_data.get("fuelclass4")
        fuelclass5 = cleaned_data.get("fuelclass5")
        fuelclass6 = cleaned_data.get("fuelclass6")
        butons = int(fuelclass1 or 0) + int(fuelclass2 or 0) + int(fuelclass3 or 0) + int(fuelclass4 or 0) + int(fuelclass5 or 0) + int(fuelclass6 or 0)
        if piletons + landingtons + butons <= 0: 
            msg = u"Please enter pile, landing, or broadcast fuel loading tonnage."
            self._errors["piletons"] = self.error_class([msg])
            self._errors["landingtons"] = self.error_class([msg])
            self._errors["fuelclass1"] = self.error_class([msg])
        return cleaned_data

class SmokeRegisterEditForm(forms.ModelForm):
    regname = forms.CharField(label='Name', max_length=30, help_text="Name this registration.", widget=forms.TextInput(attrs={'size':'30'}))
    township = forms.CharField(label='Township', min_length=4, max_length=4, initial='000N',help_text="Enter Township 26 North as 260N. Third digit is fractional township/range as decimal: 1/4=2 1/2=5 3/4=7 Full=0.", widget=forms.TextInput(attrs={'size':'4'}))
    range = forms.CharField(label='Range', min_length=4, max_length=4, initial='000E', help_text="Enter Range 08 West as 080W. Third digit is fractional township/range as decimal: 1/4=2 1/2=5 3/4=7 Full=0.", widget=forms.TextInput(attrs={'size':'4'}))
    section = forms.CharField(label='Section', min_length=2, max_length=2, widget=forms.TextInput(attrs={'size':'2'}))
    elevation = forms.IntegerField(label='Elev', help_text="Average elevation to nearest 100ft.", min_value=0, max_value=9999, widget=forms.TextInput(attrs={'size':'4'}))
    slope = forms.IntegerField(label='Slope %', help_text="Average slope as percent.", min_value=0, max_value=99, widget=forms.TextInput(attrs={'size':'2'}))
    ssradistance = forms.IntegerField(label='Distance to SSRA', help_text="Within SSRA, enter 0. If more than 60 miles, enter 60.", min_value=0, max_value=60, widget=forms.TextInput(attrs={'size':'2'}))
    revenue = forms.CharField(label='RevNo', min_length=5, max_length=5, required=False, help_text="Revenue number. Last 5 digits of tax notification number; REQUIRED for revenue smoke. Leave blank for natural fuels smoke.", validators=[numeric], widget=forms.TextInput(attrs={'size':'5'}))
    #fpf = forms.CharField(label='PDNo', min_length=3, max_length=3, help_text="ODF Protection Disrict number. Required.", widget=forms.TextInput(attrs={'size':'3'}))
    regacres = forms.IntegerField(label='Acres', min_value=1, max_value=9999, help_text="Acres to be treated. For pile burning, enter acres from which material was accumulated. Maximum 9999 per registration.", widget=forms.TextInput(attrs={'size':'4'}))
    landingtons = forms.IntegerField(label='LTons', min_value=0, max_value=9999, help_text="Total tons in landing or r-o-w piles on the unit. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'4'}))
    piletons = forms.IntegerField(label='PTons', min_value=0, max_value=9999, help_text="Total tons in unit piles. Exclude landings and right-of-way. Use PNW-GTR-364 or PCOST to estimate. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'4'}))
    fuelclass1 = forms.IntegerField(label='BU fuels 0-1/4"', min_value=0, max_value=99, help_text="Broadcast/underburn 0-1/4\" fuels in tons/ac. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'2'}))
    fuelclass2 = forms.IntegerField(label='BU fuels 1/4"-1"', min_value=0, max_value=99, help_text="Broadcast/underburn 1/4\"-1\" fuels in tons/ac. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'2'}))
    fuelclass3 = forms.IntegerField(label='BU fuels 1"-3"', min_value=0, max_value=99, help_text="Broadcast/underburn 1\"-3\" fuels in tons/ac. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'2'}))
    fuelclass4 = forms.IntegerField(label='BU fuels 3"-9"', min_value=0, max_value=99, help_text="Broadcast/underburn 3\"-9\" fuels in tons/ac. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'2'}))
    fuelclass5 = forms.IntegerField(label='BU fuels 9"-20"', min_value=0, max_value=999, help_text="Broadcast/underburn 9\"-20\" fuels in tons/ac. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'3'}))
    fuelclass6 = forms.IntegerField(label='BU fuels 20+"', min_value=0, max_value=999, help_text="Broadcast/underburn 20+\" fuels. in tons/ac. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'3'}))
    duffdepth = forms.IntegerField(label='Duff depth', min_value=0, max_value=999, help_text="In tenths of inches.", widget=forms.TextInput(attrs={'size':'3'}))
    class Meta:
        model = SmokeRegister
        exclude = ['sn','fpf','author','district','sequence']

    def clean(self):
        cleaned_data = self.cleaned_data
        t = cleaned_data.get("township")
        r = cleaned_data.get("range")
        s = cleaned_data.get("section")
        if t and r and s:
            try:
                plss = PLSS.objects.get(
                    Q(township=t.upper()),
                    Q(range=r.upper()),
                    Q(section=s.zfill(2))
                    )
            except ObjectDoesNotExist:
                plss = None
                msg = u"PLSS not found. Enter a valid township, range, and section."
                self._errors["township"] = self.error_class([msg])
                self._errors["range"] = self.error_class([msg])
                self._errors["section"] = self.error_class([msg])
        else:
            msg = u"PLSS not found. Enter a valid township, range, and section."
            self._errors["township"] = self.error_class([msg])
            self._errors["range"] = self.error_class([msg])
            self._errors["section"] = self.error_class([msg])
        return cleaned_data

class SmokeRegisterFormSN2(forms.ModelForm):
    township = forms.CharField(label='Township', min_length=4, max_length=4, initial='000N',help_text="Enter Township 26 North as 260N. Third digit is fractional township/range as decimal: 1/4=2 1/2=5 3/4=7 Full=0.", widget=forms.TextInput(attrs={'size':'4'}))
    range = forms.CharField(label='Range', min_length=4, max_length=4, initial='000E', help_text="Enter Range 08 West as 080W. Third digit is fractional township/range as decimal: 1/4=2 1/2=5 3/4=7 Full=0.", widget=forms.TextInput(attrs={'size':'4'}))
    section = forms.CharField(label='Section', min_length=2, max_length=2, widget=forms.TextInput(attrs={'size':'2'}))
    elevation = forms.IntegerField(label='Elev', help_text="Average elevation to nearest 100ft.", min_value=0, max_value=9999, widget=forms.TextInput(attrs={'size':'4'}))
    slope = forms.IntegerField(label='Slope %', help_text="Average slope as percent.", min_value=0, max_value=99, widget=forms.TextInput(attrs={'size':'2'}))
    revenue = forms.CharField(label='RevNo', min_length=5, max_length=5, required=False, help_text="Revenue number. Last 5 digits of tax notification number; REQUIRED for revenue smoke. Leave blank for natural fuels smoke.", validators=[numeric], widget=forms.TextInput(attrs={'size':'5'}))
    fpf = forms.CharField(label='PDNo', min_length=3, max_length=3, help_text="ODF Protection Disrict number. Required.", widget=forms.TextInput(attrs={'size':'3'}))
    regacres = forms.IntegerField(label='Acres', min_value=1, max_value=9999, help_text="Acres to be treated. For pile burning, enter acres from which material was accumulated. Maximum 9999 per registration.", widget=forms.TextInput(attrs={'size':'4'}))
    landingtons = forms.IntegerField(label='LTons', min_value=0, max_value=9999, help_text="Total tons in landing or r-o-w piles on the unit. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'4'}))
    piletons = forms.IntegerField(label='PTons', min_value=0, max_value=9999, help_text="Total tons in unit piles. Exclude landings and right-of-way. Use PNW-GTR-364 or PCOST to estimate. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'4'}))
    fuelclass1 = forms.IntegerField(label='BU fuels 0-1/4"', min_value=0, max_value=99, help_text="Broadcast/underburn 0-1/4\" fuels in tons/ac. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'2'}))
    fuelclass2 = forms.IntegerField(label='BU fuels 1/4"-1"', min_value=0, max_value=99, help_text="Broadcast/underburn 1/4\"-1\" fuels in tons/ac. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'2'}))
    fuelclass3 = forms.IntegerField(label='BU fuels 1"-3"', min_value=0, max_value=99, help_text="Broadcast/underburn 1\"-3\" fuels in tons/ac. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'2'}))
    fuelclass4 = forms.IntegerField(label='BU fuels 3"-9"', min_value=0, max_value=99, help_text="Broadcast/underburn 3\"-9\" fuels in tons/ac. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'2'}))
    fuelclass5 = forms.IntegerField(label='BU fuels 9"-20"', min_value=0, max_value=999, help_text="Broadcast/underburn 9\"-20\" fuels in tons/ac. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'3'}))
    fuelclass6 = forms.IntegerField(label='BU fuels 20+"', min_value=0, max_value=999, help_text="Broadcast/underburn 20+\" fuels. in tons/ac. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'3'}))
    duffdepth = forms.IntegerField(label='Duff depth', min_value=0, max_value=999, help_text="In tenths of inches.", widget=forms.TextInput(attrs={'size':'3'}))
    class Meta:
        model = SmokeRegister
        exclude = ['sn','author','district','sequence','ssradistance']

    def clean(self):
        cleaned_data = self.cleaned_data
        t = cleaned_data.get("township")
        r = cleaned_data.get("range")
        s = cleaned_data.get("section")
        if t and r and s:
            try:
                plss = PLSS.objects.get(
                    Q(township=t.upper()),
                    Q(range=r.upper()),
                    Q(section=s.zfill(2))
                    )
            except ObjectDoesNotExist:
                plss = None
                msg = u"PLSS not found. Enter a valid township, range, and section."
                self._errors["township"] = self.error_class([msg])
                self._errors["range"] = self.error_class([msg])
                self._errors["section"] = self.error_class([msg])
        else:
            msg = u"PLSS not found. Enter a valid township, range, and section."
            self._errors["township"] = self.error_class([msg])
            self._errors["range"] = self.error_class([msg])
            self._errors["section"] = self.error_class([msg])
        fpf = cleaned_data.get("fpf")
        if fpf.endswith('XX'):
            msg = u"Please use the correct ODF Protection District number."
            self._errors["fpf"] = self.error_class([msg])
            #raise forms.ValidationError("Please use the correct ODF Protection District number.")

        return cleaned_data

class SmokeRegisterLikeForm(forms.ModelForm):
    #sn = forms.CharField(label='SN', min_length=12, max_length=12, help_text="Smoke number. Natural fuels is YY+406+ODFID+NN, where ODFID is the district's 5-digit ODF id, and NN is a sequence. Revenue (timber sale) is YY+ODF+REVNO+NN, where ODF is the district's 3-digit ODF id, and REVNO is the revenue number. YY is always the current calendar year, and NN is a number from 01 to 99.")
    township = forms.CharField(label='Township', min_length=4, max_length=4, initial='000N',help_text="Enter Township 26 North as 260N. Third digit is fractional township/range as decimal: 1/4=2 1/2=5 3/4=7 Full=0.", widget=forms.TextInput(attrs={'size':'4'}))
    range = forms.CharField(label='Range', min_length=4, max_length=4, initial='000E', help_text="Enter Range 08 West as 080W. Third digit is fractional township/range as decimal: 1/4=2 1/2=5 3/4=7 Full=0.", widget=forms.TextInput(attrs={'size':'4'}))
    section = forms.CharField(label='Section', min_length=2, max_length=2, widget=forms.TextInput(attrs={'size':'2'}))
    elevation = forms.IntegerField(label='Elev', help_text="Average elevation to nearest 100ft.", min_value=0, max_value=9999, widget=forms.TextInput(attrs={'size':'4'}))
    slope = forms.IntegerField(label='Slope %', help_text="Average slope as percent.", min_value=0, max_value=99, widget=forms.TextInput(attrs={'size':'2'}))
    ssradistance = forms.IntegerField(label='Distance to SSRA', help_text="Within SSRA, enter 0. If more than 60 miles, enter 60.", min_value=0, max_value=60, widget=forms.TextInput(attrs={'size':'2'}))
    revenue = forms.CharField(label='RevNo', min_length=5, max_length=5, required=False, help_text="Revenue number. Last 5 digits of tax notification number; REQUIRED for revenue smoke. Leave blank for natural fuels smoke.", validators=[numeric], widget=forms.TextInput(attrs={'size':'5'}))
    fpf = forms.CharField(label='PDNo', min_length=3, max_length=3, required=True, help_text="ODF Protection Disrict number. Required.", widget=forms.TextInput(attrs={'size':'3'}))
    regacres = forms.IntegerField(label='Acres', min_value=1, max_value=9999, help_text="Acres to be treated. For pile burning, enter acres from which material was accumulated. Maximum 9999 per registration.", widget=forms.TextInput(attrs={'size':'4'}))
    landingtons = forms.IntegerField(label='LTons', required=True, min_value=0, max_value=9999, help_text="Total tons in landing or r-o-w piles on the unit. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'4'}))
    piletons = forms.IntegerField(label='PTons', required=True, min_value=0, max_value=9999, help_text="Total tons in unit piles. Exclude landings and right-of-way. Use PNW-GTR-364 or PCOST to estimate. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'4'}))
    fuelclass1 = forms.IntegerField(label='BU fuels 0-1/4"', required=True, min_value=0, max_value=99, help_text="Broadcast/underburn 0-1/4\" fuels in tons/ac. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'2'}))
    fuelclass2 = forms.IntegerField(label='BU fuels 1/4"-1"', required=True, min_value=0, max_value=99, help_text="Broadcast/underburn 1/4\"-1\" fuels in tons/ac. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'2'}))
    fuelclass3 = forms.IntegerField(label='BU fuels 1"-3"', required=True, min_value=0, max_value=99, help_text="Broadcast/underburn 1\"-3\" fuels in tons/ac. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'2'}))
    fuelclass4 = forms.IntegerField(label='BU fuels 3"-9"', required=True, min_value=0, max_value=99, help_text="Broadcast/underburn 3\"-9\" fuels in tons/ac. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'2'}))
    fuelclass5 = forms.IntegerField(label='BU fuels 9"-20"', required=True, min_value=0, max_value=999, help_text="Broadcast/underburn 9\"-20\" fuels in tons/ac. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'3'}))
    fuelclass6 = forms.IntegerField(label='BU fuels 20+"', required=True, min_value=0, max_value=999, help_text="Broadcast/underburn 20+\" fuels. in tons/ac. Enter 0 if none.", widget=forms.TextInput(attrs={'size':'3'}))
    duffdepth = forms.IntegerField(label='Duff depth', min_value=0, max_value=999, help_text="In tenths of inches.", widget=forms.TextInput(attrs={'size':'3'}))
    class Meta:
        model = SmokeRegister
        exclude = ['sn', 'author', 'district', 'sequence']

    def clean(self):
        cleaned_data = self.cleaned_data
        t = cleaned_data.get("township")
        r = cleaned_data.get("range")
        s = cleaned_data.get("section")
        if t and r and s:
            try:
                plss = PLSS.objects.get(
                    Q(township=t.upper()),
                    Q(range=r.upper()),
                    Q(section=s.zfill(2))
                    )
            except ObjectDoesNotExist:
                plss = None
                msg = u"PLSS not found. Enter a valid township, range, and section."
                self._errors["township"] = self.error_class([msg])
                self._errors["range"] = self.error_class([msg])
                self._errors["section"] = self.error_class([msg])
        else:
            msg = u"PLSS not found. Enter a valid township, range, and section."
            self._errors["township"] = self.error_class([msg])
            self._errors["range"] = self.error_class([msg])
            self._errors["section"] = self.error_class([msg])
        fpf = cleaned_data.get("fpf")
        if fpf:
            if fpf.endswith('XX'):
                msg = u"Please use the correct ODF Protection District number."
                self._errors["fpf"] = self.error_class([msg])
                #raise forms.ValidationError("Please use the correct ODF Protection District number.")
        else:
                msg = u"Please use the correct ODF Protection District number."	
                self._errors["fpf"] = self.error_class([msg])
        piletons = cleaned_data.get("piletons")
        piletons = int(piletons or 0)
        landingtons = cleaned_data.get("landingtons")
        landingtons = int(landingtons or 0)
        fuelclass1 = cleaned_data.get("fuelclass1")
        fuelclass2 = cleaned_data.get("fuelclass2")
        fuelclass3 = cleaned_data.get("fuelclass3")
        fuelclass4 = cleaned_data.get("fuelclass4")
        fuelclass5 = cleaned_data.get("fuelclass5")
        fuelclass6 = cleaned_data.get("fuelclass6")
        butons = int(fuelclass1 or 0) + int(fuelclass2 or 0) + int(fuelclass3 or 0) + int(fuelclass4 or 0) + int(fuelclass5 or 0) + int(fuelclass6 or 0)
        if piletons + landingtons + butons <= 0: 
            msg = u"Please enter pile, landing, or broadcast fuel loading tonnage."
            self._errors["piletons"] = self.error_class([msg])
            self._errors["landingtons"] = self.error_class([msg])
            self._errors["fuelclass1"] = self.error_class([msg])
        return cleaned_data

class SmokePlanForm(forms.ModelForm):
    acrestoburn = forms.IntegerField(label='Acres', min_value=1, max_value=9999, help_text="Acres to burn this plan. May be less than unit acres.")
    landingtons = forms.IntegerField(label='LTons', min_value=0, max_value=9999, help_text="Landing tons to be burned this plan. Enter 0 if none.")
    piletons = forms.IntegerField(label='PTons', min_value=0, max_value=9999, help_text="Pile tons to be burned this plan. Enter 0 if none.")
    b_u_tonsperacre = forms.IntegerField(label='BUTons/a', min_value=0, max_value=100, help_text="Broadcast and underburn tons/acre to be burned this plan. Enter 0 if none.")
    class Meta:
        model = SmokePlan
        exclude = ['author']

class SmokePlanFormSN2(forms.ModelForm):
    acrestoburn = forms.IntegerField(label='Acres', min_value=1, max_value=9999, help_text="Acres to burn this plan.", widget=forms.TextInput(attrs={'size':'4'}))
    landingtons = forms.IntegerField(label='LTons', min_value=0, max_value=9999, help_text="Landing tons to burn this plan. 0 if none.", widget=forms.TextInput(attrs={'size':'4'}))
    piletons = forms.IntegerField(label='PTons', min_value=0, max_value=9999, help_text="Pile tons to burn this plan. 0 if none.", widget=forms.TextInput(attrs={'size':'4'}))
    b_u_tonsperacre = forms.IntegerField(label='BUTons/a', min_value=0, max_value=100, help_text="Broadcast or underburn tons/acre to burn this plan. 0 if none.", widget=forms.TextInput(attrs={'size':'3'}))
    class Meta:
        model = SmokePlan
        exclude = ['author', 'sn', 'suffix', 'snid']

    def __init__(self, regacres, *args, **kwargs):
        self.regacres = regacres
        super(SmokePlanFormSN2, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = self.cleaned_data
        acrestoburn = cleaned_data.get("acrestoburn")
        regacres = self.regacres
        if acrestoburn > regacres:
            msg = u"Plan acres greater than registered acres."
            self._errors["acrestoburn"] = self.error_class([msg])
            #raise forms.ValidationError("Please use the correct ODF Protection District number.")
        elif acrestoburn == 0:
            msg = u"Can't plan 0 acres."
            self._errors["acrestoburn"] = self.error_class([msg])

        piletons = cleaned_data.get("piletons")
        landingtons = cleaned_data.get("landingtons")
        butons = cleaned_data.get("b_u_tonsperacre")
        if piletons + landingtons + butons <= 0: 
            msg = u"Please enter pile, landing, or broadcast fuel loading tonnage."
            self._errors["piletons"] = self.error_class([msg])
            self._errors["landingtons"] = self.error_class([msg])
            self._errors["b_u_tonsperacre"] = self.error_class([msg])
        return cleaned_data

class SmokePlanFormSN3(forms.ModelForm):
    acrestoburn = forms.IntegerField(label='Acres', min_value=1, max_value=9999, help_text="Acres to burn this plan.", widget=forms.TextInput(attrs={'size':'4'}))
    landingtons = forms.IntegerField(label='LTons', min_value=0, max_value=9999, help_text="Landing tons to burn this plan. 0 if none.", widget=forms.TextInput(attrs={'size':'4'}))
    piletons = forms.IntegerField(label='PTons', min_value=0, max_value=9999, help_text="Pile tons to burn this plan. 0 if none.", widget=forms.TextInput(attrs={'size':'4'}))
    b_u_tonsperacre = forms.IntegerField(label='BUTons/a', min_value=0, max_value=100, help_text="Broadcast or underburn tons/acre to burn this plan. 0 if none.", widget=forms.TextInput(attrs={'size':'3'}))
    class Meta:
        model = SmokePlan
        exclude = ['author', 'sn', 'suffix', 'snid']

class SmokeResultForm(forms.ModelForm):
    acresburned = forms.IntegerField(label='Acres', min_value=0, max_value=9999, help_text="Acres burned (blackened). May be more or less than planned. Enter 0 if none.")
    landingtonned = forms.IntegerField(label='LTons', min_value=0, max_value=9999, help_text="Landing tons burned this plan. Enter 0 if none.")
    piletonned = forms.IntegerField(label='PTons', min_value=0, max_value=9999, help_text="Pile tons burned this plan. Enter 0 if none.")
    b_u_tonsperacred = forms.IntegerField(label='BUTons/a', help_text="Broadcast and underburn tons per acre burned this plan. Enter 0 if none.", min_value=0, max_value=99)
    ignitionduration = forms.IntegerField(label='Duration', min_value=0, max_value=999, help_text="Minutes from first ignition to finish. Include breaks in total. Enter 0 for pile burns.")
    airtemperature = forms.IntegerField(label='F', min_value=0, max_value=99, help_text="Air temperature in whole Farenheit degrees. Enter 0 for pile burns.")
    relativehumidity = forms.IntegerField(label='RH', min_value=0, max_value=99, help_text="Percent relative humidity. Enter 0 for pile burns.")
    windspeed = forms.IntegerField(label='Wind mph', min_value=0, max_value=99, help_text="Enter 0 for pile burns.")
    tenhour = forms.IntegerField(label='10hr', min_value=0, max_value=99, help_text="Ten-hour moisture. Whole number for quarter- to one-inch fuels. Enter 0 for pile burns.")
    thousandhour = forms.IntegerField(label='1000hr', min_value=0, max_value=99, help_text="Thousand-hour moisture. Whole number for 3- to 9-inch fuels. Enter 0 for pile burns.")
    dayssincerain = forms.IntegerField(label='Rain', min_value=0, max_value=999, help_text="Western Oregon = days since 0.50-inch rain in 48 hrs; Eastern Oregon = days since 0.25-inch rain in 48 hrs. Not required (enter 0) for pile burns.")
    no = forms.ChoiceField(label='Reason', choices=NO_CHOICES, help_text="", widget=forms.Select(attrs={'class':'form-control input-sm', }),)
    why = forms.CharField(label='Details', required = False, help_text="", widget=forms.Textarea(attrs={'class':'form-control input-sm', 'rows': 1, 'style': 'height: 44px;'}))
    class Meta:
        model = SmokeResult
        exclude = ['author']

class SmokeResultFormSN2(forms.ModelForm):
    acresburned = forms.IntegerField(label='Acres', min_value=0, max_value=9999, help_text="Acres burned (blackened). May be more or less than planned. Enter 0 if none.")
    landingtonned = forms.IntegerField(label='LTons', min_value=0, max_value=9999, help_text="Landing tons burned this plan. Enter 0 if none.")
    piletonned = forms.IntegerField(label='PTons', min_value=0, max_value=9999, help_text="Pile tons burned this plan. Enter 0 if none.")
    b_u_tonsperacred = forms.IntegerField(label='BUTons/a', help_text="Broadcast and underburn tons per acre burned this plan. Enter 0 if none.", min_value=0, max_value=99)
    ignitionduration = forms.IntegerField(label='Duration', min_value=0, max_value=999, help_text="Minutes from first ignition to finish. Include breaks in total. Enter 0 for pile burns.")
    airtemperature = forms.IntegerField(label='F', min_value=0, max_value=99, help_text="Air temperature in whole Farenheit degrees. Enter 0 for pile burns.")
    relativehumidity = forms.IntegerField(label='RH', min_value=0, max_value=99, help_text="Percent relative humidity. Enter 0 for pile burns.")
    windspeed = forms.IntegerField(label='Wind mph', min_value=0, max_value=99, help_text="Enter 0 for pile burns.")
    tenhour = forms.IntegerField(label='10hr', min_value=0, max_value=99, help_text="Ten-hour moisture. Whole number for quarter- to one-inch fuels. Enter 0 for pile burns.")
    thousandhour = forms.IntegerField(label='1000hr', min_value=0, max_value=99, help_text="Thousand-hour moisture. Whole number for 3- to 9-inch fuels. Enter 0 for pile burns.")
    dayssincerain = forms.IntegerField(label='Rain', min_value=0, max_value=999, help_text="Western Oregon = days since 0.50-inch rain in 48 hrs; Eastern Oregon = days since 0.25-inch rain in 48 hrs. Not required (enter 0) for pile burns.")
    no = forms.ChoiceField(label='Reason', choices=NO_CHOICES, help_text="", widget=forms.Select(attrs={'class':'form-control input-sm', }),)
    why = forms.CharField(label='Details', required = False, help_text="", widget=forms.Textarea(attrs={'class':'form-control input-sm', 'rows': 1, 'style': 'height: 44px;'}))
    class Meta:
        model = SmokeResult
        exclude = ['author', 'notaccomplished', 'snid']

    def __init__(self, regacres, *args, **kwargs):
        self.regacres = regacres
        super(SmokeResultFormSN2, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = self.cleaned_data
        acresburned = cleaned_data.get("acresburned")
        regacres = self.regacres
        if acresburned > regacres:
            msg = u"Result acres greater than registered acres."
            self._errors["acresburned"] = self.error_class([msg])
            #raise forms.ValidationError("Please use the correct ODF Protection District number.")

        piletons = cleaned_data.get("piletonned")
        landingtons = cleaned_data.get("landingtonned")
        butons = cleaned_data.get("b_u_tonsperacred")
        if acresburned >= 1 and piletons + landingtons + butons <= 0: 
            msg = u"Please enter pile, landing, or broadcast fuel loading tonnage."
            self._errors["piletons"] = self.error_class([msg])
            self._errors["landingtons"] = self.error_class([msg])
            self._errors["b_u_tonsperacre"] = self.error_class([msg])
        return cleaned_data

class SmokeResultFormSN3(forms.ModelForm):
    acresburned = forms.IntegerField(label='Acres', min_value=0, max_value=9999, help_text="Acres burned (blackened). May be more or less than planned.", widget=forms.TextInput(attrs={'size':'4'}))
    landingtonned = forms.IntegerField(label='LTons', min_value=0, max_value=9999, help_text="Landing tons burned. 0 if none.", widget=forms.TextInput(attrs={'size':'4'}))
    piletonned = forms.IntegerField(label='PTons', min_value=0, max_value=9999, help_text="Pile tons burned. 0 if none.", widget=forms.TextInput(attrs={'size':'4'}))
    b_u_tonsperacred = forms.IntegerField(label='BUTons/a', help_text="Broadcast and underburn tons per acre burned. 0 if none.", min_value=0, max_value=99, widget=forms.TextInput(attrs={'size':'2'}))
    ignitionduration = forms.IntegerField(label='Duration', min_value=0, max_value=999, help_text="Minutes from first ignition to finish. 0 for pile burns.", widget=forms.TextInput(attrs={'size':'3'}))
    weatherstation = forms.CharField(label='Weather', help_text="Enter initial 4-characters of RAWS name, last 4 digits of RAWS number, or UNIT for on-site observation. NA for pile burns.", widget=forms.TextInput(attrs={'size':'4'}))
    airtemperature = forms.IntegerField(label='F', min_value=0, max_value=99, help_text="Air temperature in whole Farenheit degrees. 0 for pile burns.", widget=forms.TextInput(attrs={'size':'2'}))
    relativehumidity = forms.IntegerField(label='RH', min_value=0, max_value=99, help_text="Percent relative humidity. 0 for pile burns.", widget=forms.TextInput(attrs={'size':'2'}))
    windspeed = forms.IntegerField(label='Wind mph', min_value=0, max_value=99, help_text="0 for pile burns.", widget=forms.TextInput(attrs={'size':'2'}))
    tenhour = forms.IntegerField(label='10hr moisture', min_value=0, max_value=99, help_text="Whole number for 1/4\"-1\" fuels. 0 for pile burns.", widget=forms.TextInput(attrs={'size':'2'}))
    thousandhour = forms.IntegerField(label='1000hr moisture', min_value=0, max_value=99, help_text="Whole number for 3\"-9\" fuels. 0 for pile burns.", widget=forms.TextInput(attrs={'size':'2'}))
    dayssincerain = forms.IntegerField(label='Rain', min_value=0, max_value=999, help_text="Western Oregon = days since 0.50-inch rain in 48 hrs; Eastern Oregon = days since 0.25-inch rain in 48 hrs. 0 for pile burns.", widget=forms.TextInput(attrs={'size':'3'}))
    no = forms.ChoiceField(label='Reason', choices=NO_CHOICES, help_text="", widget=forms.Select(attrs={'class':'form-control input-sm', }),)
    why = forms.CharField(label='Details', required = False, help_text="", widget=forms.Textarea(attrs={'class':'form-control input-sm', 'rows': 1, 'style': 'height: 44px;'}))
    class Meta:
        model = SmokeResult
        exclude = ['author', 'notaccomplished', 'snid']

    def clean(self):
        cleaned_data = self.cleaned_data
        acresburned = cleaned_data.get("acresburned")
        #regacres = self.regacres
        #if acresburned > regacres:
        #    msg = u"Result acres greater than registered acres."
        #    self._errors["acresburned"] = self.error_class([msg])
            #raise forms.ValidationError("Please use the correct ODF Protection District number.")

        piletons = cleaned_data.get("piletonned")
        landingtons = cleaned_data.get("landingtonned")
        butons = cleaned_data.get("b_u_tonsperacred")
        if acresburned >= 1 and piletons + landingtons + butons <= 0: 
            msg = u"Please enter pile, landing, or broadcast fuel loading tonnage."
            self._errors["piletonned"] = self.error_class([msg])
            self._errors["landingtonned"] = self.error_class([msg])
            self._errors["b_u_tonsperacred"] = self.error_class([msg])
        elif acresburned == 0 and piletons + landingtons + butons > 0:
            msg = u"When acres burned is 0, all tonnages should be zero."
            self._errors["piletonned"] = self.error_class([msg])
            self._errors["landingtonned"] = self.error_class([msg])
            self._errors["b_u_tonsperacred"] = self.error_class([msg])
        return cleaned_data


class NoResultFormSN2(forms.ModelForm):
    no = forms.ChoiceField(label='Reason', choices=NO_CHOICES, help_text="", widget=forms.Select(attrs={'class':'form-control input-sm', }),)
    why = forms.CharField(label='Details', required = False, help_text="", widget=forms.Textarea(attrs={'class':'form-control input-sm', 'rows': 1, 'style': 'height: 44px;'}))

    class Meta:
        model = SmokeResult
        exclude = ['author', 'notaccomplished', 'snid', 'acresburned', 'landingtonned', 'piletonned', 'b_u_tonsperacred', 'ignitiondated', 'ignitiontimed', 'ignitionmethod', 'smokeintrusion', 'rapidignition', 'ignitionduration', 'weatherstation','airtemperature', 'relativehumidity', 'winddirection', 'windspeed', 'tenhour', 'thousandhour', 'thousandhourmethod', 'dayssincerain', 'snowoffmonth']

class AdvancedForm(forms.ModelForm):
    author = forms.ModelChoiceField(queryset=User.objects.all())
    district = forms.ModelChoiceField(queryset=District.objects.all())
    revenue = forms.CharField(label='RevNo', validators=[numeric], help_text="Revenue number. Optional.")
    sn = forms.CharField(label='SN', max_length=12, help_text="Smoke number. NATURAL IS YY+406+ODFID+NN. COMMERCIAL IS YY+ODF+REVNO+NN.")
    sequence = forms.IntegerField(label='Plan Sequence', min_value=0, max_value=99, help_text = "Initially 01.")
    regname = forms.CharField(label='Name', max_length=30)
    township = forms.CharField(label='Township', help_text="Like ###D. Third digit: 1/4=2 1/2=5 3/4=7 Full=0.")
    range = forms.CharField(label='Range', help_text="Like ###D. Third digit: 1/4=2 1/2=5 3/4=7 Full=0.")
    section = forms.CharField(label='Section', help_text="Like ##.")
    county = forms.ChoiceField(label="County", choices=COUNTY_CHOICES)
    elevation = forms.IntegerField(min_value=0, max_value=11239, help_text="Average elevation to nearest 100ft.")
    slope = forms.IntegerField(label='Slope %', min_value=0, max_value=99, help_text="Average slope as percent. Like ###.")
    ownership = forms.ChoiceField(label="Ownership", choices=OWNERSHIP_CHOICES)
    ssradistance = forms.CharField(label="dSSRA", help_text="Within SSRA, enter 0. If more than 60 miles, enter 60.")
    spz = forms.ChoiceField(choices=SPZ_CHOICES, help_text="Special Protection Zone.")
    fpf = forms.CharField(label='PDNo', help_text="ODF Protection Disrict number. Optional.")
    typeburn = forms.ChoiceField(choices=TYPEBURN_CHOICES)
    reason = forms.ChoiceField(choices=REASON_CHOICES)
    regacres = forms.IntegerField(label='Acres', min_value=1, max_value=9999, help_text="Acres to be treated. For pile burning, use acres from which material was accumulated.")
    landingtons = forms.IntegerField(label='LTons', min_value=0, max_value=9999, help_text="Landing & R/W Pile tons. Total tons in landing or r-o-w piles on the unit.")
    piletons = forms.IntegerField(label='PTons', min_value=0, max_value=9999, help_text="Pile tons. Total tons in unit piles. Exclude landings and right-of-way. Use PNW-GTR-364 or PCOST to estimate.")
    loadmethod = forms.ChoiceField(label='LoadMethod', choices=LOADMETHOD_CHOICES, help_text="NONPILE is T,P#,L, or M. PILE is A,R, or O.")
    fuelspecies = forms.ChoiceField(label='Species', choices=FUELSPECIES_CHOICES)
    fuelclass1 = forms.IntegerField(label='0-1/4"', min_value=0, max_value=99, help_text="0-1/4\" fuel tons/acre. Do not include duff.")
    fuelclass2 = forms.IntegerField(label='1/4"-1"', min_value=0, max_value=99, help_text="1/4\"-1\" fuel tons/acre. Do not include duff.")
    fuelclass3 = forms.IntegerField(label='1"-3"', min_value=0, max_value=99, help_text="1\"-3\" fuel tons/acre. Do not include duff.")
    fuelclass4 = forms.IntegerField(label='3"-9"', min_value=0, max_value=99, help_text="3\"-9\" fuel tons/acre. Do not include duff.")
    fuelclass5 = forms.IntegerField(label='9"-20"', min_value=0, max_value=999, help_text="9\"-20\" fuel tons/acre. Do not include duff.")
    fuelclass6 = forms.IntegerField(label='20+"', min_value=0, max_value=999, help_text="20+\" fuel tons/acre. Do not include duff.")
    duffdepth = forms.IntegerField(label='Duff', min_value=0, max_value=999, help_text="Duff depth in tenths-inches.")
    harvestd = forms.ChoiceField(choices=HARVESTD_CHOICES)
    cutdate = forms.DateField(label='Cut date', help_text="Date when 70% complete.")
    class Meta:
        model = SmokeRegister
        exclude =[]

from django.utils.timezone import utc

timenow = datetime.datetime.utcnow().replace(tzinfo=utc)

YN = (
    ('TRUE', 'Yes'),
    ('FALSE', 'No'),
)


class PlusFourForm(forms.ModelForm):
    district = forms.ModelChoiceField(queryset=District.objects.all(), widget=forms.Select(attrs={'class':'form-control input-sm'}))
    name = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control input-sm', 'placeholder':'Project Name'}))
    township = forms.CharField(min_length=4, max_length=4, initial='000N', widget=forms.TextInput(attrs={'class':'form-control input-sm', 'size':'4'}))
    range = forms.CharField(min_length=4, max_length=4, initial='000E', widget=forms.TextInput(attrs={'class':'form-control input-sm', 'size':'4'}))
    section = forms.CharField(min_length=2, max_length=2, widget=forms.TextInput(attrs={'class':'form-control input-sm', 'size':'2'}))
    acres = forms.IntegerField(min_value=1, max_value=999, widget=forms.TextInput(attrs={'class':'form-control input-sm','size':'4'}))
    objective = forms.CharField( widget=forms.Textarea(attrs={'class':'form-control input-sm', 'rows': 2}))
    ignitionstart = forms.DateField(label='Planned Ignition Start Date', widget=forms.DateInput(attrs={'class':'form-control input-sm', }),)
    ignitionend = forms.DateField(label='Planned Ignition Completion Date', widget=forms.DateInput(attrs={'class':'form-control input-sm', }),)
    mopdays = forms.IntegerField(label='Number of days expected for Mop-up and Patrol', widget=forms.TextInput(attrs={'class':'form-control input-sm','size':'4'}))
    mopend = forms.DateField(label='Expected Completion Date', widget=forms.DateInput(attrs={'class':'form-control input-sm', }),)
    complexity = forms.ChoiceField(label='Final Complexity Alalysis Rating', choices=LMH, widget=forms.Select(attrs={'class':'form-control input-sm', }),)
    compsum = forms.CharField(label='Complexity Summary', required = False, widget=forms.Textarea(attrs={'class':'form-control input-sm', 'rows': 2}))
    risk = forms.ChoiceField(label='Risk Rating', choices=LMH, widget=forms.Select(attrs={'class':'form-control input-sm', }),)
    risksum = forms.CharField(label='Risk Summary', required = False, widget=forms.Textarea(attrs={'class':'form-control input-sm', 'rows': 2}))
    cons = forms.ChoiceField(label='Consequences Rating', choices=LMH, widget=forms.Select(attrs={'class':'form-control input-sm', }),)
    conssum = forms.CharField(label='Consequences Summary', required = False, widget=forms.Textarea(attrs={'class':'form-control input-sm', 'rows': 2}))
    technical = forms.ChoiceField(label='Technical Difficulties Rating', choices=LMH, widget=forms.Select(attrs={'class':'form-control input-sm', }),)
    technicalsum = forms.CharField(label='Technical Difficulties Summary', required = False, widget=forms.Textarea(attrs={'class':'form-control input-sm', 'rows': 2}))
    rn1 = forms.BooleanField(label='Will local fire resources be sufficient for the duration of the project?', required = False, widget=forms.NullBooleanSelect(attrs={'class':'form-control input-sm', }),)
    rn2 = forms.BooleanField(label='Will the use of local resources affect IA response on the forest or districts?', required = False, widget=forms.NullBooleanSelect(attrs={'class':'form-control input-sm', }),)
    rn3 = forms.BooleanField(label='Will the local unit need support from outside fire resources for ignition?', required = False, widget=forms.NullBooleanSelect(attrs={'class':'form-control input-sm', }),)
    rn4 = forms.BooleanField(label='Will the local unit need support from outside fire resources for mop-up?', required = False, widget=forms.NullBooleanSelect(attrs={'class':'form-control input-sm', }),)
    rn5 = forms.BooleanField(label='Will the local unit need support from outside fire resources for patrol?', required = False, widget=forms.NullBooleanSelect(attrs={'class':'form-control input-sm', }),)
    rdetail = forms.CharField(label='Resource Details', required = False, widget=forms.Textarea(attrs={'class':'form-control input-sm', 'rows': 2}))
    cn1 = forms.BooleanField(label='Have contingency resources been identified for the duration of the project?', required = False, widget=forms.NullBooleanSelect(attrs={'class':'form-control input-sm', }),)
    cn2 = forms.BooleanField(label='Are contingency resources available from your local unit or area?', required = False, widget=forms.NullBooleanSelect(attrs={'class':'form-control input-sm', }),)
    cn3 = forms.BooleanField(label='If contingency resources are from another geographic area have they been notified and are they available to respond if needed?', required = False, widget=forms.NullBooleanSelect(attrs={'class':'form-control input-sm', }),)
    cdetail = forms.CharField(label='Contingency Details', required = False, widget=forms.Textarea(attrs={'class':'form-control input-sm', 'rows': 2}))
    psa = forms.ChoiceField(label='PNW Predictive Service Area Identifier', choices=PSA, widget=forms.Select(attrs={'class':'form-control input-sm', }),)
    forecast = forms.CharField(label='Weather Forecast Summary for Ignition Period', required = False, widget=forms.Textarea(attrs={'class':'form-control input-sm', 'rows': 2}))
    plan = forms.BooleanField(label='Are the burn plan environmental parameters within prescription?', required = False, widget=forms.NullBooleanSelect(attrs={'class':'form-control input-sm', }),)
    longrange = forms.CharField(label='Long Range Forecast', required = False, widget=forms.Textarea(attrs={'class':'form-control input-sm', 'rows': 2}))
    are = forms.BooleanField(label='Are there any indicators in the forecast that could affect the ability to mop-up and control prescribed fire within the timeframes identified above?', required = False, widget=forms.NullBooleanSelect(attrs={'class':'form-control input-sm', }),)
    measures = forms.CharField(label='If yes, please describe any mitigation measures that would be put into place', required = False, widget=forms.Textarea(attrs={'class':'form-control input-sm', 'rows': 2}))
    lo = forms.CharField(label='Line Officer Signature', widget=forms.TextInput(attrs={'class':'form-control input-sm', 'placeholder':'Line Officer Signature'}))
    lodate = forms.DateField(label='Signature Date', widget=forms.DateInput(attrs={'class':'form-control input-sm', }),)
    dfmo = forms.CharField(label='DFMO Signature', required = False, widget=forms.TextInput(attrs={'class':'form-control input-sm', 'placeholder':'DFMO Signature'}))
    dfmodate = forms.DateField(label='Signature Date', required = False, widget=forms.DateInput(attrs={'class':'form-control input-sm', }),)
    reqfile = forms.FileField(label='File Attachment',  required = False, widget=forms.ClearableFileInput(attrs={'class':'form-control input-sm', }))

    class Meta:
        model = PlusFour
        exclude = ['author','gmacdate','gmaccom','nmacdate','nmaccom','preapp','pre','predate','preoff','finapp','fin','findate','finoff','appfile','remarks',]
        #fields = []

    #def save(self, commit=True):
        #obj = super(PlusFourForm, self).save(commit=False)
        #try:
        #author = User.objects.get(id=obj.author.id)
        #if commit:
        #    obj.save()
        #    if not author.has_perm('change_plusfour', obj):
        #        assign('change_plusfour', author, obj)
        #    if not author.has_perm('delete_plusfour', obj):
        #        assign('delete_plusfour', author, obj)
        #except:
        #    author = None
        #    if commit:
        #        obj.save()
        #return obj

class PlusFourStatusForm(forms.ModelForm):
    #district = forms.ModelChoiceField(queryset=District.objects.all(), widget=forms.Select(attrs={'class':'form-control input-sm', 'readonly': True}))
    #name = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control input-sm', 'placeholder':'Project Name', 'readonly': True}))
    #township = forms.CharField(min_length=4, max_length=4, initial='000N', widget=forms.TextInput(attrs={'class':'form-control input-sm', 'size':'4', 'readonly': True}))
    #range = forms.CharField(min_length=4, max_length=4, initial='000E', widget=forms.TextInput(attrs={'class':'form-control input-sm', 'size':'4', 'readonly': True}))
    #section = forms.CharField(min_length=2, max_length=2, widget=forms.TextInput(attrs={'class':'form-control input-sm', 'size':'2', 'readonly': True}))
    #acres = forms.IntegerField(min_value=1, max_value=999, widget=forms.TextInput(attrs={'class':'form-control input-sm','size':'4', 'readonly': True}))
    #objective = forms.CharField( widget=forms.Textarea(attrs={'class':'form-control input-sm', 'rows': 2, 'readonly': True}))
    #ignitionstart = forms.DateField(label='Planned Ignition Start Date', widget=forms.DateInput(attrs={'class':'form-control input-sm', 'readonly': True}),)
    #ignitionend = forms.DateField(label='Planned Ignition Completion Date', widget=forms.DateInput(attrs={'class':'form-control input-sm', 'readonly': True}),)
    #mopdays = forms.IntegerField(label='Number of days expected for Mop-up and Patrol', widget=forms.TextInput(attrs={'class':'form-control input-sm','size':'4', 'readonly': True}))
    #mopend = forms.DateField(label='Expected Completion Date', widget=forms.DateInput(attrs={'class':'form-control input-sm', 'readonly': True}),)
    #complexity = forms.ChoiceField(label='Final Complexity Alalysis Rating', choices=LMH, widget=forms.Select(attrs={'class':'form-control input-sm', 'readonly': True}),)
    #compsum = forms.CharField(label='Complexity Summary', required = False, widget=forms.Textarea(attrs={'class':'form-control input-sm', 'rows': 2, 'readonly': True}))
    #risk = forms.ChoiceField(label='Risk Rating', choices=LMH, widget=forms.Select(attrs={'class':'form-control input-sm', 'readonly': True}),)
    #risksum = forms.CharField(label='Risk Summary', required = False, widget=forms.Textarea(attrs={'class':'form-control input-sm', 'rows': 2, 'readonly': True}))
    #cons = forms.ChoiceField(label='Consequences Rating', choices=LMH, widget=forms.Select(attrs={'class':'form-control input-sm', 'readonly': True}),)
    #conssum = forms.CharField(label='Consequences Summary', required = False, widget=forms.Textarea(attrs={'class':'form-control input-sm', 'rows': 2, 'readonly': True}))
    #technical = forms.ChoiceField(label='Technical Difficulties Rating', choices=LMH, widget=forms.Select(attrs={'class':'form-control input-sm', 'readonly': True}),)
    #technicalsum = forms.CharField(label='Technical Difficulties Summary', required = False, widget=forms.Textarea(attrs={'class':'form-control input-sm', 'rows': 2, 'readonly': True}))
    #rn1 = forms.BooleanField(label='Will local fire resources be sufficient for the duration of the project?', required = False, widget=forms.NullBooleanSelect(attrs={'class':'form-control input-sm', 'readonly': True}),)
    #rn2 = forms.BooleanField(label='Will the use of local resources affect IA response on the forest or districts?', required = False, widget=forms.NullBooleanSelect(attrs={'class':'form-control input-sm', 'readonly': True}),)
    #rn3 = forms.BooleanField(label='Will the local unit need support from outside fire resources for ignition?', required = False, widget=forms.NullBooleanSelect(attrs={'class':'form-control input-sm', 'readonly': True}),)
    #rn4 = forms.BooleanField(label='Will the local unit need support from outside fire resources for mop-up?', required = False, widget=forms.NullBooleanSelect(attrs={'class':'form-control input-sm', 'readonly': True}),)
    #rn5 = forms.BooleanField(label='Will the local unit need support from outside fire resources for patrol?', required = False, widget=forms.NullBooleanSelect(attrs={'class':'form-control input-sm', 'readonly': True}),)
    #rdetail = forms.CharField(label='Resource Details', required = False, widget=forms.Textarea(attrs={'class':'form-control input-sm', 'rows': 2, 'readonly': True}))
    #cn1 = forms.BooleanField(label='Have contingency resources been identified for the duration of the project?', required = False, widget=forms.NullBooleanSelect(attrs={'class':'form-control input-sm', 'readonly': True}),)
    #cn2 = forms.BooleanField(label='Are contingency resources available from your local unit or area?', required = False, widget=forms.NullBooleanSelect(attrs={'class':'form-control input-sm', 'readonly': True}),)
    #cn3 = forms.BooleanField(label='If contingency resources are from another geographic area have they been notified and are they available to respond if needed?', required = False, widget=forms.NullBooleanSelect(attrs={'class':'form-control input-sm', 'readonly': True}),)
    #cdetail = forms.CharField(label='Contingency Details', required = False, widget=forms.Textarea(attrs={'class':'form-control input-sm', 'rows': 2, 'readonly': True}))
    #psa = forms.ChoiceField(label='PNW Predictive Service Area Identifier', choices=PSA, widget=forms.Select(attrs={'class':'form-control input-sm', 'readonly': True}),)
    #forecast = forms.CharField(label='Weather Forecast Summary for Ignition Period', required = False, widget=forms.Textarea(attrs={'class':'form-control input-sm', 'rows': 2, 'readonly': True}))
    #plan = forms.BooleanField(label='Are the burn plan environmental parameters within prescription?', required = False, widget=forms.NullBooleanSelect(attrs={'class':'form-control input-sm', 'readonly': True}),)
    #longrange = forms.CharField(label='Long Range Forecast', required = False, widget=forms.Textarea(attrs={'class':'form-control input-sm', 'rows': 2, 'readonly': True}))
    #are = forms.BooleanField(label='Are there any indicators in the forecast that could affect the ability to mop-up and control prescribed fire within the timeframes identified above?', required = False, widget=forms.NullBooleanSelect(attrs={'class':'form-control input-sm', 'readonly': True}),)
    #measures = forms.CharField(label='If yes, please describe any mitigation measures that would be put into place', required = False, widget=forms.Textarea(attrs={'class':'form-control input-sm', 'rows': 2, 'readonly': True}))
    #lo = forms.CharField(label='Line Officer Signature', widget=forms.TextInput(attrs={'class':'form-control input-sm', 'placeholder':'Line Officer Signature', 'readonly': True}))
    #lodate = forms.DateField(label='Signature Date', widget=forms.DateInput(attrs={'class':'form-control input-sm', 'readonly': True}),)
    #dfmo = forms.CharField(label='DFMO Signature', required = False, widget=forms.TextInput(attrs={'class':'form-control input-sm', 'readonly': True, 'placeholder':'DFMO Signature'}))
    #dfmodate = forms.DateField(label='Signature Date', required = False, widget=forms.DateInput(attrs={'class':'form-control input-sm', 'readonly': True }),)
    gmacdate = forms.DateField(label='GMAC Date', required = False, widget=forms.DateInput(attrs={'class':'form-control input-sm', }),)
    gmaccom = forms.CharField(label='GMAC Comments', required = False, widget=forms.Textarea(attrs={'class':'form-control input-sm', 'rows': 2}))
    nmacdate = forms.DateField(label='NMAC Date', required = False, widget=forms.DateInput(attrs={'class':'form-control input-sm', }),)
    nmaccom = forms.CharField(label='NMAC Comments', required = False, widget=forms.Textarea(attrs={'class':'form-control input-sm', 'rows': 2}))
    #reqfile = forms.FileField(label='File Attachment',  required = False, widget=forms.ClearableFileInput(attrs={'class':'form-control input-sm', 'readonly': True}))
    #preapp = forms.NullBooleanField(label='Preliminary Approval', required = False, widget=forms.CheckboxInput(attrs={'class':'form-control input-sm',}),)
    pre = forms.CharField(label='Preliminary Approval Signature', required = False, widget=forms.TextInput(attrs={'class':'form-control input-sm', 'placeholder':'Preliminary Approval Signature'}))
    preoff = forms.ChoiceField(label='Preliminary Approval Officer', required = False, choices=PRE, widget=forms.Select(attrs={'class':'form-control input-sm', }),)
    predate = forms.DateField(label='Signature Date', required = False, widget=forms.DateInput(attrs={'class':'form-control input-sm', }),)
    finapp = forms.NullBooleanField(label='Final Approval', required = False, widget=forms.NullBooleanSelect(attrs={'class':'form-control input-sm',}),)
    fin = forms.CharField(label='Final Approval Signature', required = False, widget=forms.TextInput(attrs={'class':'form-control input-sm', 'placeholder':'Final Approval Signature'}))
    finoff = forms.ChoiceField(label='Final Approval Officer', required = False, choices=FIN, widget=forms.Select(attrs={'class':'form-control input-sm', }),)
    findate = forms.DateField(label='Signature Date', required = False, widget=forms.DateInput(attrs={'class':'form-control input-sm', }),)
    appfile = forms.FileField(label='File Attachment', required = False, widget=forms.ClearableFileInput(attrs={'class':'form-control input-sm', }))
    class Meta:
        model = PlusFour
        #exclude = ['author','remarks','preapp',]
        exclude = ['author','remarks','preapp','district','name','township','range','section','acres','objective','ignitionstart','ignitionend','mopdays','mopend','complexity','compsum','risk','risksum','cons','conssum','technical','technicalsum','rn1','rn2','rn3','rn4','rn5','rdetail','cn1','cn2','cn3','cdetail','psa','forecast','plan','longrange','are','measures','lo','lodate','dfmo','dfmodate','reqfile',]
        #fields = []


    def clean(self):
        cleaned_data = self.cleaned_data
        oid = self.instance.pk
        obj = PlusFour.objects.get(id__exact=oid)
        cleaned_data['district'] = obj.district
        cleaned_data['name'] = obj.name
        cleaned_data['township'] = obj.township
        cleaned_data['range'] = obj.range
        cleaned_data['section'] = obj.section
        cleaned_data['acres'] = obj.acres
        cleaned_data['objective'] = obj.objective
        cleaned_data['ignitionstart'] = obj.ignitionstart
        cleaned_data['ignitionend'] = obj.ignitionend
        cleaned_data['mopdays'] = obj.mopdays
        cleaned_data['complexity'] = obj.complexity
        cleaned_data['compsum'] = obj.compsum
        cleaned_data['risk'] = obj.risk
        cleaned_data['risksum'] = obj.risksum
        cleaned_data['cons'] = obj.cons
        cleaned_data['conssum'] = obj.conssum
        cleaned_data['technical'] = obj.technical
        cleaned_data['technicalsum'] = obj.technicalsum
        cleaned_data['rn1'] = obj.rn1
        cleaned_data['rn2'] = obj.rn2
        cleaned_data['rn3'] = obj.rn3
        cleaned_data['rn4'] = obj.rn4
        cleaned_data['rn5'] = obj.rn5
        cleaned_data['rdetail'] = obj.rdetail
        cleaned_data['cn1'] = obj.cn1
        cleaned_data['cn2'] = obj.cn2
        cleaned_data['cn3'] = obj.cn3
        cleaned_data['cdetail'] = obj.cdetail
        cleaned_data['psa'] = obj.psa
        cleaned_data['forecast'] = obj.forecast
        cleaned_data['plan'] = obj.plan
        cleaned_data['longrange'] = obj.longrange
        cleaned_data['are'] = obj.are
        cleaned_data['measures'] = obj.measures
        cleaned_data['lo'] = obj.lo
        cleaned_data['lodate'] = obj.lodate
        cleaned_data['dfmo'] = obj.dfmo
        cleaned_data['dfmodate'] = obj.dfmodate
        #cleaned_data['gmacdate'] = obj.gmacdate
        #cleaned_data['gmaccom'] = obj.gmaccom
        cleaned_data['reqfile'] = obj.reqfile
        #cleaned_data['tobase'] = Airbase.objects.get(id=tobase)
        #cleaned_data['fmso'] = 'f'
        return cleaned_data
