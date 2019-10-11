from django.template import Context, loader, RequestContext
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q, F, Max, Min, Count, Avg, Sum
from django.contrib import messages
from fastrax.models import *
from fastrax.forms import *
from django.contrib.auth.models import User, Group
import datetime
from datetime import timedelta
from django.forms.models import inlineformset_factory
from django.forms.formsets import formset_factory
#from o_fastrax.place import models
#from o_fastrax.place.models import *
from ftplib import FTP
import urllib
from xml.dom import minidom
from django.contrib.gis import geos
from django.contrib.gis.geos import *
from django.contrib.gis.measure import D
#from django.contrib.gis.maps.google import GPolygon, GPolyline
from google.overlays import GPolygon
from decimal import Decimal
from dateutil.relativedelta import relativedelta
import calendar
from django.urls import reverse_lazy
from django.core.mail import send_mail, send_mass_mail
from django.core.mail import EmailMultiAlternatives
from guardian.shortcuts import assign, get_users_with_perms, get_objects_for_user, remove_perm
from guardian.utils import clean_orphan_obj_perms
from django.utils.decorators import method_decorator
from django.contrib.auth.signals import user_logged_in
import settings

def update_user_login(sender, user, **kwargs):
    m = 'User %s login successful.' % (user)
    #messages.success(m)
    l = Logitem(author=user, status='S', message=m, obj_model='Session', obj_id='', obj_in='', obj_out='',)
    l.save()
    #user.userlogin_set.create(timestamp=timezone.now())
    #user.save()

user_logged_in.connect(update_user_login)


def index(request):
    latest_reg_list = SmokeRegister.objects.all().order_by('-entered')[:6]
    latest_plan_list = SmokePlan.objects.all().order_by('-entered')[:6]
    latest_result_list = SmokeResult.objects.all().order_by('-entered')[:6]
    return render(request,'fastrax/index.html', {'latest_reg_list': latest_reg_list, 'latest_plan_list': latest_plan_list, 'latest_result_list': latest_result_list},)

def search(request):
    query = request.GET['q']
    reg_list = SmokeRegister.objects.filter(regname__icontains=query).annotate(black=Sum('plan_sn__result_snid__acresburned'))
    for object in reg_list:
        if object.black == None:
            object.color = 'black'
        elif object.black < object.regacres:
            object.color = 'green'
        elif object.black >= object.regacres:
            object.color = 'red'
    template = loader.get_template('fastrax/search.html')
    context = { 'query': query, 'reg_list': reg_list }
    response = template.render(context)
    return HttpResponse(response)

from vanilla import CreateView, DeleteView, ListView, UpdateView, DetailView

class ListPlusFour(ListView):
    model = PlusFour

class PrintPlusFour(DetailView):
    model = PlusFour

class CreatePlusFour(CreateView):
    model = PlusFour
    form_class = PlusFourForm
    success_url = reverse_lazy('list_plusfour')

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.author = self.request.user
        obj.save()
        assign('change_plusfour', obj.author, obj)
        assign('delete_plusfour', obj.author, obj)
        #obj.user_list = get_users_with_perms(obj, with_group_user=False)
        if obj.lo and obj.dfmo:
            msg = 'Burn request <a class=\'alert-link\' href=\'/plusfour/%s/\'>%s</a> added. Duty officer notified.' % (obj.id, obj.name)
            messages.success(self.request, msg)
            l = Logitem(author=self.request.user, status='S', message=msg, obj_model='Plusfour', obj_id=obj.id, obj_in='', obj_out='',)
            l.save()
            group = Group.objects.get(name='fastrax-ro-fuels')
            user_list = group.user_set.all()
            mtxt = 'Burn request %s [{{ request.site.domain }}/plusfour/%s/] added and forwarded to the Duty Officer.' % (obj.name, obj.id)
            mhtm = 'Burn request <a class=\'alert-link\' href=\'{{ request.site.domain }}/plusfour/%s/\'>%s</a> added and forwarded to the Duty Officer.' % (obj.id, obj.name)
            for user in user_list:
                msg = EmailMultiAlternatives('New burn request', mtxt, settings.ADMIN_EMAIL, [user.email])
                msg.attach_alternative(mhtm, "text/html")
                msg.send()
        else:
            msg = 'Burn request <a class=\'alert-link\' href=\'/plusfour/%s/\'>%s</a> added. Add Line Officer and DFMO signatures to forward to the Duty Officer. ' % (obj.id, obj.name)
            messages.success(self.request, msg)
            l = Logitem(author=self.request.user, status='S', message=msg, obj_model='Plusfour', obj_id=obj.id, obj_in='', obj_out='',)
            l.save()
        return HttpResponseRedirect('/plusfour/%s/' % (obj.id))

# user and finapp checks in template
class UpdatePlusFour(UpdateView):
    model = PlusFour
    form_class = PlusFourForm
    success_url = reverse_lazy('list_plusfour')

    #@method_decorator(permission_required('fastrax.change_plusfour',
    #    (PlusFour, 'pk', 'pk')))
    #def dispatch(self, *args, **kwargs):
    #    return super(UpdatePlusFour, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.save()
        if obj.lo and obj.dfmo:
            msg = 'Burn request <a class=\'alert-link\' href=\'/plusfour/%s/\'>%s</a> updated. Duty officer notified.' % (obj.id, obj.name)
            messages.success(self.request, msg)
            l = Logitem(author=self.request.user, status='S', message=msg, obj_model='Plusfour', obj_id=obj.id, obj_in='', obj_out='',)
            l.save()
            group = Group.objects.get(name='fastrax-ro-fuels')
            user_list = group.user_set.all()
            mtit = 'Burn request %s updated' % (obj.name)
            mtxt = 'Burn request %s [{{ request.site.domain }}/plusfour/%s/] updated. Duty officer notified.' % (obj.name, obj.id)
            mhtm = 'Burn request <a class=\'alert-link\' href=\'{{ request.site.domain }}/plusfour/%s/\'>%s</a> updated. Duty officer notified.' % (obj.id, obj.name)
            for user in user_list:
                msg = EmailMultiAlternatives(mtit, mtxt, settings.ADMIN_EMAIL, [user.email])
                msg.attach_alternative(mhtm, "text/html")
                msg.send()
        else:
            msg = 'Burn request <a class=\'alert-link\' href=\'/plusfour/%s/\'>%s</a> updated. Add Line Officer and DFMO signatures to forward to the Duty Officer. ' % (obj.id, obj.name)
            messages.success(self.request, msg)
            l = Logitem(author=self.request.user, status='S', message=msg, obj_model='Plusfour', obj_id=obj.id, obj_in='', obj_out='',)
            l.save()
        return HttpResponseRedirect('/plusfour/%s/' % (obj.id))

# group check in url
# user and finapp checks in template
class StatusPlusFour(UpdateView):
    model = PlusFour
    form_class = PlusFourStatusForm
    success_url = reverse_lazy('list_plusfour')

    def form_valid(self, form):
        obj = form.save(commit=False)
        #airbase = PlusFour.objects.get(pk=obj.pk)
        #user_list = get_users_with_perms(airbase)
        #msg = '%s > %s > %s' % (obj.pk, airbase.author.email, user_list)
        #messages.info(self.request, msg)
        if obj.finapp is not None:
            msg = 'Burn request <a class=\'alert-link\' href=\'/plusfour/%s/\'>%s</a> status updated. Requesting users notified.' % (obj.id, obj.name)
            messages.success(self.request, msg)
            l = Logitem(author=self.request.user, status='S', message=msg, obj_model='Plusfour', obj_id=obj.id, obj_in='', obj_out='',)
            l.save()
            airbase = PlusFour.objects.get(pk=obj.pk)
            #user_list = get_users_with_perms(airbase)
            user_list = User.objects.filter(id=airbase.author.id)
            mtit = 'Burn request %s status updated' % (obj.name)
            mtxt = 'Burn request %s [{{ request.site.domain }}/plusfour/%s/] status updated. Requesting users notified.' % (obj.name, obj.id)
            mhtm = 'Burn request <a class=\'alert-link\' href=\'{{ request.site.domain }}/plusfour/%s/\'>%s</a> status updated. Requesting users notified.' % (obj.id, obj.name)
            for user in user_list:
                msg = EmailMultiAlternatives(mtit, mtxt, settings.ADMIN_EMAIL, [user.email])
                msg.attach_alternative(mhtm, "text/html")
                msg.send()
        else:
            msg = 'Burn request <a class=\'alert-link\' href=\'/plusfour/%s/\'>%s</a> status updated. Change the approval status to \'denied\' or \'approved\' to close this request and notify requesting users. ' % (obj.id, obj.name)
            messages.success(self.request, msg)
            l = Logitem(author=self.request.user, status='S', message=msg, obj_model='Plusfour', obj_id=obj.id, obj_in='', obj_out='',)
            l.save()
        obj.save()
        return HttpResponseRedirect('/plusfour/%s/' % (obj.id))

# needs user check
# needs dfmo or finapp check (submitted, no delete)
# no template
class DeletePlusFour(DeleteView):
    model = PlusFour
    success_url = reverse_lazy('list_plusfour')

### vanilla fastrax

class ListSmokeRegister(ListView):
    model = SmokeRegister
    #template_name = 'fastrax/smokeregister_list.html'

    def get_queryset(self):
        adate = datetime.datetime.now().year
        ayear = adate - 2
        iyear = datetime.date(ayear,1,1)
        regr_list = SmokeRegister.objects.filter(
            Q(regdate__gte=iyear)
            ).order_by('sn')
        black_list = SmokeRegister.objects.filter(
            Q(regdate__gte=iyear)
            ).annotate(black=Sum('plan_sn__result_snid__acresburned')).filter(Q(black__lt=F('regacres')) | Q(black=None)).order_by('sn')
        for object in black_list:
            if object.black == None:
                object.color = 'black'
            elif object.black < object.regacres:
                object.color = 'green'
            elif object.black >= object.regacres:
                object.color = 'red'
        reg_list = black_list
        plan_list = SmokePlan.objects.exclude(result_snid__result_date__isnull=False).order_by('sn', 'suffix')
        pland_list = SmokePlan.objects.all()
        result_list = SmokeResult.objects.all()
        now = datetime.datetime.today()  
        first_month = datetime.datetime(now.year, now.month, 1)
        previous_months = (first_month - relativedelta(months = months) for months in range(0, 24, 1))
        themonths = previous_months
        e=[]
        cumu = regr_list.count()
        cump = pland_list.count()
        cumr = result_list.count()
        cumrt = result_list.count()
        maxcount = 0
        maxplan = 0
        maxresult = 0
        for month in themonths:
            iyear = month.year
            imonth = month.month
            entry_count = SmokeRegister.objects.filter(
                Q(regdate__year=iyear),
                Q(regdate__month=imonth)
                ).annotate(black=Sum('plan_sn__result_snid__acresburned')).filter(Q(black__lt=F('regacres')) | Q(black=None)).count()
            if entry_count >= maxcount:
                maxcount = entry_count
            plan_count = SmokePlan.objects.filter(
                Q(plan_date__year=iyear),
                Q(plan_date__month=imonth)
                ).count()
            if plan_count >= maxplan:
                maxplan = plan_count
            result_count = SmokeResult.objects.filter(
                Q(result_date__year=iyear),
                Q(result_date__month=imonth)
                ).count()
            if result_count >= maxresult:
                maxresult = result_count
            dict = {'month': month, 'count': entry_count, 'cumu': cumu, 'countp': plan_count, 'cump': cump, 'countr': result_count, 'cumr': cumr }
            e.append(dict)
            cumu = cumu - entry_count
            cump = cump - plan_count
            cumr = cumr - result_count
            maxplan = max(maxplan,maxresult)
        entry_dates = e
        if self.request.user.has_perm('fastrax.add_event'):
            return reg_list
        else:
            return reg_list
            #return SmokeRegister.objects.filter(regdate__gte=iyear)

class DetailSmokeRegister(DetailView):
    model = SmokeRegister
    lookup_field = 'sn'

    def get_context_data(self, **kwargs):
        context = super(DetailSmokeRegister, self).get_context_data(**kwargs)

        today = datetime.date.today()
        adate = datetime.datetime.now().year # this year numeric
        ayear = adate - 2 # 2 years ago
        iyear = datetime.date(ayear,1,1) # if reg before this DATE, expire it 

        sn = self.kwargs['sn']
        reg = SmokeRegister.objects.get(sn__exact=sn)
        try:
            plss = PLSS.objects.get(
                Q(township=reg.township.upper()),
                Q(range=reg.range.upper()),
                Q(section=reg.section.zfill(2))
                )
        except:
            plss = None
        c = calendar.monthcalendar(reg.regdate.year, reg.regdate.month)
        reg.first_week = c[0]
        reg.third_week = c[2]
        reg.fourth_week = c[3]
        if reg.first_week[calendar.TUESDAY]:
            reg.meeting_date = reg.third_week[calendar.TUESDAY]
        else:
            reg.meeting_date = reg.fourth_week[calendar.TUESDAY]
        reg.deaddate = datetime.date(reg.regdate.year, reg.regdate.month, reg.meeting_date)
        if reg.deaddate <= reg.regdate:
            reg.deaddate = reg.regdate + timedelta(days=14)
        reg.deadline = datetime.date(reg.deaddate.year, reg.deaddate.month, reg.deaddate.day)
        toedit = False
        toplan = False
        if reg.deadline >= today:
            toedit = True
        if iyear <= reg.regdate:
            toplan = True

        context['deadline'] = reg.deadline
        context['toedit'] = toedit
        context['toplan'] = toplan
        context['plss'] = plss

        return context


class CreateSmokeRegister(CreateView):
    model = SmokeRegister
    form_class = SmokeRegisterForm
    success_url = reverse_lazy('list_smokeregister')

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.author = self.request.user
        obj.save()
        assign('change_smokeregister', obj.author, obj)
        assign('delete_smokeregister', obj.author, obj)
        msg = 'Smoke Registration <a class=\'alert-link\' href=\'/%s/\'>%s</a> added. ' % (obj.sn, obj.name)
        messages.success(self.request, msg)
        l = Logitem(author=self.request.user, status='S', message=msg, obj_model='SmokeRegister', obj_id=obj.id, obj_in='', obj_out='',)
        l.save()
        return HttpResponseRedirect('/%s/' % (obj.sn))

# user and finapp checks in template
class UpdateSmokeRegister(UpdateView):
    model = SmokeRegister
    lookup_field = 'sn'
    form_class = SmokeRegisterForm
    success_url = reverse_lazy('list_smokeregister')

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.save()
        msg = 'Smoke Registration <a class=\'alert-link\' href=\'/%s/\'>%s</a> updated. ' % (obj.sn, obj.name)
        messages.success(self.request, msg)
        l = Logitem(author=self.request.user, status='S', message=msg, obj_model='SmokeRegister', obj_id=obj.id, obj_in='', obj_out='',)
        l.save()
        return HttpResponseRedirect('/%s/' % (obj.sn))

# needs user check
# needs dfmo or finapp check (submitted, no delete)
# no template
class DeleteSmokeRegister(DeleteView):
    model = SmokeRegister
    lookup_field = 'sn'
    success_url = reverse_lazy('list_smokeregister')


class DistrictListSmokeRegister(ListView):
    model = SmokeRegister
    #lookup_field = 'district'
    #template_name = 'fastrax/smokeregister_list.html'

    def get_queryset(self):
        adate = datetime.datetime.now().year
        ayear = adate - 2
        iyear = datetime.date(ayear,1,1)
        ddistrict = District.objects.filter(slug=self.kwargs['slug'])[:1]
        regr_list = SmokeRegister.objects.filter(
            Q(regdate__gte=iyear),
            Q(district__slug__iexact=self.kwargs['slug'])
            ).order_by('sn')
        black_list = SmokeRegister.objects.filter(
            Q(regdate__gte=iyear),
            Q(district__slug__iexact=self.kwargs['slug'])
            ).annotate(black=Sum('plan_sn__result_snid__acresburned')).filter(Q(black__lt=F('regacres')) | Q(black=None)).order_by('sn')
        for object in black_list:
            if object.black == None:
                object.color = 'black'
            elif object.black < object.regacres:
                object.color = 'green'
            elif object.black >= object.regacres:
                object.color = 'red'
        reg_list = black_list
        plan_list = SmokePlan.objects.filter(
            Q(sn__district__slug__iexact=self.kwargs['slug'])
            ).exclude(result_snid__result_date__isnull=False).order_by('sn', 'suffix')
        pland_list = SmokePlan.objects.filter(
            Q(sn__district__slug__iexact=self.kwargs['slug'])
            )
        result_list = SmokeResult.objects.filter(
            Q(snid__sn__district__slug__iexact=self.kwargs['slug'])
            )
        now = datetime.datetime.today()  
        first_month = datetime.datetime(now.year, now.month, 1)
        previous_months = (first_month - relativedelta(months = months) for months in range(0, 24, 1))
        themonths = previous_months
        e=[]
        cumu = regr_list.count()
        cump = pland_list.count()
        cumr = result_list.count()
        cumrt = result_list.count()
        maxcount = 0
        maxplan = 0
        maxresult = 0
        for month in themonths:
            iyear = month.year
            imonth = month.month
            entry_count = SmokeRegister.objects.filter(
                Q(regdate__year=iyear),
                Q(regdate__month=imonth),
                Q(district__slug__iexact=self.kwargs['slug'])
                ).annotate(black=Sum('plan_sn__result_snid__acresburned')).filter(Q(black__lt=F('regacres')) | Q(black=None)).count()
            if entry_count >= maxcount:
                maxcount = entry_count
            plan_count = SmokePlan.objects.filter(
                Q(plan_date__year=iyear),
                Q(plan_date__month=imonth),
                Q(sn__district__slug__iexact=self.kwargs['slug'])
                ).count()
            if plan_count >= maxplan:
                maxplan = plan_count
            result_count = SmokeResult.objects.filter(
                Q(result_date__year=iyear),
                Q(result_date__month=imonth),
                Q(snid__sn__district__slug__iexact=self.kwargs['slug'])
                ).count()
            if result_count >= maxresult:
                maxresult = result_count
            dict = {'month': month, 'count': entry_count, 'cumu': cumu, 'countp': plan_count, 'cump': cump, 'countr': result_count, 'cumr': cumr }
            e.append(dict)
            cumu = cumu - entry_count
            cump = cump - plan_count
            cumr = cumr - result_count
            maxplan = max(maxplan,maxresult)
        entry_dates = e
        if self.request.user.has_perm('fastrax.add_event'):
            return reg_list
        else:
            return reg_list
            #return SmokeRegister.objects.filter(regdate__gte=iyear).filter(district__slug=self.kwargs['slug'])


    def get_context_data(self, **kwargs):
        context = super(DistrictListSmokeRegister, self).get_context_data(**kwargs)
        district = District.objects.get(slug=self.kwargs['slug'])
        context['district'] = district

        return context

### fastrax main

@login_required
@permission_required('fastrax.add_smokeregister')
def register(request):
    if request.method == 'POST':
        form = SmokeRegisterForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.author = request.user
            obj.sequence = 99
            obj.save()
            return HttpResponseRedirect('/')
    else:
        form = SmokeRegisterForm()

    return render(request,'fastrax/fastrax_form.html', {
        'form': form,
    },)

@login_required
@permission_required('fastrax.add_smokeregister')
def tndnregister1(request, tn, dn):
    adate = datetime.datetime.now().year
    ayear = adate - 1
    iyear = datetime.date(ayear,1,1)
    dreg_list = SmokeRegister.objects.filter(
        Q(regdate__gte=iyear),
        Q(district__slug__iexact=dn)
        ).order_by('sn')
    if request.method == 'POST':
        dtla = District.objects.filter(tla=tn)[:1]
        ddistrict = District.objects.filter(slug=dn)[:1]
        reg_list = SmokeRegister.objects.filter(district__slug__iexact=dn).order_by('sn')
        did = u"%s" % (ddistrict[0].pk)
        form = SmokeRegisterFormSN1(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.author = request.user
            obj.district = ddistrict[0]
            obj.sequence = 1
            obj.save()
            return HttpResponseRedirect('/%s/' % (obj.sn))
            #return HttpResponseRedirect('/district/%s/%s/' % (tn, dn))
    else:
        dtla = District.objects.filter(tla=tn)[:1]
        ddistrict = District.objects.filter(slug=dn)[:1]
        reg_list = SmokeRegister.objects.filter(district__slug__iexact=dn).order_by('sn')
        did = u"%s" % (ddistrict[0].pk)
        data_dict = {'district': did}
        form = SmokeRegisterFormSN1(initial=data_dict)

    return render(request,'fastrax/tndnregister1.html', {
        'form': form, 'reg_list': reg_list, 'dreg_list': dreg_list, 'ddistrict': ddistrict, 'dtla': dtla
    },)

@login_required
@permission_required('fastrax.add_smokeregister')
def tndnregister(request, tn, dn):
    adate = datetime.datetime.now().year
    yy = datetime.datetime.now().strftime("%y")
    ayear = adate - 1
    iyear = datetime.date(ayear,1,1)
    dreg_list = SmokeRegister.objects.filter(
        Q(regdate__gte=iyear),
        Q(district__slug__iexact=dn)
        ).order_by('sn')
    if request.method == 'POST':
        dtla = District.objects.filter(tla=tn)[:1]
        ddistrict = District.objects.filter(slug=dn)[:1]
        reg_list = SmokeRegister.objects.filter(
            Q(regdate__gte=iyear),
            Q(district__slug__iexact=dn)
            ).order_by('sn')
        did = u"%s" % (ddistrict[0].pk)
        form = SmokeRegisterFormSN(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.author = request.user
            obj.district = ddistrict[0]
            if obj.revenue:
                #sn = 10 + 999 + revenue + 01
                odf = ddistrict[0].nnn
                if odf.endswith('XX'):
                    odf = obj.fpf
                revenue = obj.revenue
                base = u"%s%3s%05s" % (yy, odf, revenue)
                base_list = SmokeRegister.objects.filter(sn__startswith=base).order_by('sn')
                seq = 1
                if base_list:
                    seq = base_list.count()
                    #seq = base_list[0].sn[10:12]
                    seq = int(seq)+1
                    seq = int(str(seq)[-2:])
                obj.sn = u"%s%3s%05s%02d" % (yy, odf, revenue, seq)
                sn_list = SmokeRegister.objects.filter(sn__iexact=obj.sn).order_by('sn')
                if sn_list:
                    base_list = SmokeRegister.objects.filter(sn__startswith=base).order_by('-sn')[:1]
                    seq = 1
                    if base_list:
                        seq = base_list.count()
                        seq = base_list[0].sn[10:12]
                        seq = int(seq)+1
                        seq = int(str(seq)[-2:])
                    obj.sn = u"%s%3s%05s%02d" % (yy, odf, revenue, seq)
                
            else:
                #sn = 10 + 406 + 99900 + 01
                odf = 406
                odfid = ddistrict[0].odfid
                odfid = int(odfid)
                base = u"%s%3s%05d" % (yy, odf, odfid)
                base_list = SmokeRegister.objects.filter(sn__startswith=base).order_by('sn')
                seq = 1
                if base_list:
                    #seq = base_list[0].sn[10:12]
                    seq = base_list.count()
                    if seq != 99:
                        seq = int(seq)+1
                    seq = int(str(seq)[-2:])
                obj.sn = u"%s%3s%05d%02d" % (yy, odf, odfid, seq)
                hold1 = obj.sn
                #obj.regname = u"%s%3s%05d%02d" % (yy, odf, odfid, seq)
                #obj.sn = 'TESTTEST0000' #104060110099
                sn_list = SmokeRegister.objects.filter(sn__iexact=obj.sn).order_by('sn')
                if sn_list: # 0001-0000 skipped numbers
                    base_list = SmokeRegister.objects.filter(sn__startswith=base).order_by('-sn')[:1]
                    seq = 1
                    if base_list:
                        seq = base_list[0].sn[10:12]
                        if seq != 99:
                            seq = int(seq)+1
                        seq = int(str(seq)[-2:])
                    obj.sn = u"%s%3s%05d%02d" % (yy, odf, odfid, seq)
                    #obj.regname = u"%s%3s%05d%02d" % (yy, odf, odfid, seq)
                    #obj.regname = hold1
                    #obj.sn = 'TESTTEST0001' #1040601100100 - seq of 100 to long, slice it
                    sn_list = SmokeRegister.objects.filter(sn__iexact=obj.sn).order_by('sn')
                    if sn_list: # 0101-0100 second hundred
                        odfid = ddistrict[0].odfid
                        odfid = int(odfid)+1
                        base = u"%s%3s%05d" % (yy, odf, odfid)
                        base_list = SmokeRegister.objects.filter(sn__startswith=base).order_by('-sn')
                        seq = 1
                        if base_list:
                            seq = base_list.count()
                            #seq = base_list[0].sn[10:12]
                            if seq != 99:
                                seq = int(seq)+1
                            seq = int(str(seq)[-2:])
                        obj.sn = u"%s%3s%05d%02d" % (yy, odf, odfid, seq)
                        #obj.regname = u"%s%3s%05d%02d" % (yy, odf, odfid, seq)
                        #obj.regname = hold1
                        #obj.sn = 'TESTTEST0002' #10406 110101 - missing leading zero in odfid, pad it
                        sn_list = SmokeRegister.objects.filter(sn__iexact=obj.sn).order_by('sn')
                        if sn_list: # 0201-0200 third hundred
                            odfid = ddistrict[0].odfid
                            odfid = int(odfid)+1
                            base = u"%s%3s%05d" % (yy, odf, odfid)
                            base_list = SmokeRegister.objects.filter(sn__startswith=base).order_by('-sn')
                            seq = 1
                            if base_list:
                                seq = base_list.count()
                                #seq = base_list[0].sn[10:12]
                                if seq != 99:
                                    seq = int(seq)+1
                                seq = int(str(seq)[-2:])
                            obj.sn = u"%s%3s%05d%02d" % (yy, odf, odfid, seq)
                            sn_list = SmokeRegister.objects.filter(sn__iexact=obj.sn).order_by('sn')
                            if sn_list: #0301-0300 fourth hundred
                                odfid = ddistrict[0].odfid
                                odfid = int(odfid)+1
                                base = u"%s%3s%05d" % (yy, odf, odfid)
                                base_list = SmokeRegister.objects.filter(sn__startswith=base).order_by('-sn')
                                seq = 1
                                if base_list:
                                    seq = base_list.count()
                                    #seq = base_list[0].sn[10:12]
                                    if seq != 99:
                                        seq = int(seq)+1
                                    seq = int(str(seq)[-2:])
                                obj.sn = u"%s%3s%05s%02d" % (yy, odf, odfid, seq)
            obj.sequence = 66
            obj.save() #dupfail
            return HttpResponseRedirect('/%s/' % (obj.sn))
    else:
        dtla = District.objects.filter(tla=tn)[:1]
        ddistrict = District.objects.filter(slug=dn)[:1]
        reg_list = SmokeRegister.objects.filter(
            Q(regdate__gte=iyear),
            Q(district__slug__iexact=dn)
            ).order_by('sn')
        did = u"%s" % (ddistrict[0].pk)
        dfpf = u"%s" % (ddistrict[0].nnn)
        data_dict = {'district': did, 'fpf': dfpf}
        form = SmokeRegisterFormSN(initial=data_dict)

    return render(request,'fastrax/tndnregister.html', {
        'form': form, 'reg_list': reg_list, 'dreg_list': dreg_list, 'ddistrict': ddistrict, 'dtla': dtla
    },)

def snalt(request, sn):
    reg_list = SmokeRegister.objects.filter(sn__exact=sn).order_by('sn')[:1]
    plan_list = SmokePlan.objects.filter(
        Q(sn__exact=sn)
        ).order_by('suffix')
    result_list = SmokeResult.objects.filter(
        Q(snid__sn__exact=sn)
        ).order_by('snid')
    return render(request,'fastrax/snalt.html', {'reg_list': reg_list, 'plan_list': plan_list, 'result_list': result_list})

def sn(request, sn):
    reg_list = SmokeRegister.objects.filter(sn__exact=sn).order_by('sn')[:1]
    regco = reg_list[0].get_county_display()
    regt = u"%s" % (reg_list[0].township.upper())
    regr = u"%s" % (reg_list[0].range.upper())
    regs = u"%s" % (reg_list[0].section.zfill(2))
    regspz = reg_list[0].get_spz_display()
    regreason = reg_list[0].get_reason_display()
    regtype = reg_list[0].get_typeburn_display()
    reglm = reg_list[0].get_loadmethod_display()
    regspecies = reg_list[0].get_fuelspecies_display()
    reghd = reg_list[0].get_harvestd_display()
    #co = County.objects.filter(
    #    Q(name__exact=regco),
    #    Q(state__exact='Oregon')
    #    ).order_by('name')[:1]
    trsr = PLSS.objects.filter(
        Q(township__exact=regt),
        Q(range__exact=regr),
        Q(section__iexact=regs)
        ).order_by('township')[:1]
    plan_list = SmokePlan.objects.filter(
        Q(sn__exact=sn)
        ).order_by('suffix')
    result_list = SmokeResult.objects.filter(
        Q(snid__sn__exact=sn)
        ).order_by('snid')
    for reg in reg_list:
        # Compute the dates for each week that overlaps the month
        c = calendar.monthcalendar(reg.regdate.year, reg.regdate.month)
        reg.first_week = c[0]
        reg.third_week = c[2]
        reg.fourth_week = c[3]
        #reg.ct = calendar.TUESDAY
        if reg.first_week[calendar.TUESDAY]:
            reg.meeting_date = reg.third_week[calendar.TUESDAY]
        else:
            reg.meeting_date = reg.fourth_week[calendar.TUESDAY]
        reg.deaddate = datetime.date(reg.regdate.year, reg.regdate.month, reg.meeting_date)
        if reg.deaddate <= reg.regdate:
            reg.deaddate = reg.regdate + timedelta(days=14)
        reg.deadline = datetime.datetime(reg.deaddate.year, reg.deaddate.month, reg.deaddate.day)
        reg.now = datetime.datetime.now()
    return render(request,'fastrax/sn.html', {'reg_list': reg_list, 'plan_list': plan_list, 'result_list': result_list, 'regco': regco, 'regspz': regspz, 'regreason': regreason, 'regtype': regtype, 'regspecies': regspecies, 'reghd': reghd, 'reglm': reglm, 'trsr': trsr },)

def sndyn(request, sn):
    reg_list = SmokeRegister.objects.filter(sn__exact=sn).order_by('sn')[:1]
    regco = reg_list[0].get_county_display()
    regt = u"%s" % (reg_list[0].township.upper())
    regr = u"%s" % (reg_list[0].range.upper())
    regs = u"%s" % (reg_list[0].section.zfill(2))
    regspz = reg_list[0].get_spz_display()
    regreason = reg_list[0].get_reason_display()
    regtype = reg_list[0].get_typeburn_display()
    reglm = reg_list[0].get_loadmethod_display()
    regspecies = reg_list[0].get_fuelspecies_display()
    reghd = reg_list[0].get_harvestd_display()
    #co = County.objects.filter(
    #   Q(name__exact=regco),
    #   Q(state__exact='Oregon')
    #   ).order_by('name')[:1]
    trsr = PLSS.objects.filter(
        Q(township__exact=regt),
        Q(range__exact=regr),
        Q(section__iexact=regs)
        ).order_by('township')[:1]
    plan_list = SmokePlan.objects.filter(
        Q(sn__exact=sn)
        ).order_by('suffix')
    result_list = SmokeResult.objects.filter(
        Q(snid__sn__exact=sn)
        ).order_by('snid')
    for reg in reg_list:
        # Compute the dates for each week that overlaps the month
        c = calendar.monthcalendar(reg.regdate.year, reg.regdate.month)
        reg.first_week = c[0]
        reg.third_week = c[2]
        reg.fourth_week = c[3]
        #reg.ct = calendar.TUESDAY
        if reg.first_week[calendar.TUESDAY]:
            reg.meeting_date = reg.third_week[calendar.TUESDAY]
        else:
            reg.meeting_date = reg.fourth_week[calendar.TUESDAY]
        reg.deaddate = datetime.date(reg.regdate.year, reg.regdate.month, reg.meeting_date)
        if reg.deaddate <= reg.regdate:
            reg.deaddate = reg.regdate + timedelta(days=14)
        reg.deadline = datetime.datetime(reg.deaddate.year, reg.deaddate.month, reg.deaddate.day)
        reg.now = datetime.datetime.now()
    return render(request,'fastrax/sndyn.html', {'reg_list': reg_list, 'plan_list': plan_list, 'result_list': result_list, 'regco': regco, 'regspz': regspz, 'regreason': regreason, 'regtype': regtype, 'regspecies': regspecies, 'reghd': reghd, 'reglm': reglm, 'trsr': trsr },)

@login_required
@permission_required('fastrax.add_smokeregister')
def snedit(request, sn):
    adate = datetime.datetime.now().year
    yy = datetime.datetime.now().strftime("%y")
    ayear = adate - 1
    iyear = datetime.date(ayear,1,1)
    reg = SmokeRegister.objects.get(sn__exact=sn)
    #regco = reg.get_county_display()
    regt = u"%s" % (reg.township.upper())
    regr = u"%s" % (reg.range.upper())
    regs = u"%s" % (reg.section.zfill(2))
    trsr = PLSS.objects.filter(
        Q(township__exact=regt),
        Q(range__exact=regr),
        Q(section__iexact=regs)
        ).order_by('township')[:1]

    # Compute the dates for each week that overlaps the month
    c = calendar.monthcalendar(reg.regdate.year, reg.regdate.month)
    reg.first_week = c[0]
    reg.third_week = c[2]
    reg.fourth_week = c[3]
    #reg.ct = calendar.TUESDAY
    if reg.first_week[calendar.TUESDAY]:
        reg.meeting_date = reg.third_week[calendar.TUESDAY]
    else:
        reg.meeting_date = reg.fourth_week[calendar.TUESDAY]
    reg.deaddate = datetime.date(reg.regdate.year, reg.regdate.month, reg.meeting_date)
    if reg.deaddate <= reg.regdate:
        reg.deaddate = reg.regdate + timedelta(days=14)
    reg.deadline = datetime.datetime(reg.deaddate.year, reg.deaddate.month, reg.deaddate.day)
    reg.now = datetime.datetime.now()
    if reg.author == request.user and reg.deadline >= datetime.datetime.now() or request.user.is_superuser:
        if request.method == 'POST':
            form = SmokeRegisterEditForm(request.POST, instance=reg)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.fpf = reg.fpf
                obj.sequence = 51
                obj.save()
                return HttpResponseRedirect('/%s/' % (obj.sn))
        else:
            form = SmokeRegisterEditForm(instance=reg)
    else:
        form = 'None'
    return render(request,'fastrax/snedit.html', {
        'form': form, 'reg': reg, 'trsr': trsr
    },)

@login_required
@permission_required('fastrax.add_smokeregister')
def snregisterlike(request, sn):
    adate = datetime.datetime.now().year
    yy = datetime.datetime.now().strftime("%y")
    ayear = adate - 1
    iyear = datetime.date(ayear,1,1)
    reg_list = SmokeRegister.objects.filter(sn__exact=sn).order_by('sn')[:1]
    regt = u"%s" % (reg_list[0].township.upper())
    regr = u"%s" % (reg_list[0].range.upper())
    regs = u"%s" % (reg_list[0].section.zfill(2))
    regdist = reg_list[0].district.slug
    regtla = reg_list[0].district.tla
    tn = u"%s" % (regtla)
    dn = u"%s" % (regdist)
    trsr = PLSS.objects.filter(
        Q(township__exact=regt),
        Q(range__exact=regr),
        Q(section__iexact=regs)
        ).order_by('township')[:1]
    dtla = District.objects.filter(tla=tn)[:1]
    ddistrict = District.objects.filter(slug=dn)[:1]
    did = u"%s" % (ddistrict[0].pk)
    regcounty = u"%s" % (reg_list[0].county)
    regpdno = u"%s" % (reg_list[0].fpf)
    regrevno = u"%s" % (reg_list[0].revenue)
    regown = u"%s" % (reg_list[0].ownership)
    regspz = u"%s" % (reg_list[0].spz)
    regduff = u"%s" % (reg_list[0].duffdepth)
    regreason = u"%s" % (reg_list[0].reason)
    regsn = u"%s" % (reg_list[0].sn)
    reghd = u"%s" % (reg_list[0].harvestd)
    regspecies = u"%s" % (reg_list[0].fuelspecies)
    regname = u"%s" % (reg_list[0].regname)
    regelev = u"%s" % (reg_list[0].elevation)
    regslope = u"%s" % (reg_list[0].slope)
    regdssra = u"%s" % (reg_list[0].ssradistance)
    regcutdate = u"%s" % (reg_list[0].cutdate)
    dreg_list = SmokeRegister.objects.filter(
        Q(regdate__gte=iyear),
        Q(district__slug__iexact=dn)
        ).order_by('sn')
    data_dict = {'district': did, 'township': regt, 'range': regr, 'section': regs, 'county': regcounty, 'elevation': regelev, 'slope': regslope, 'ssradistance': regdssra, 'ownership': regown, 'spz': regspz, 'reason': regreason, 'duffdepth': regduff, 'fuelspecies': regspecies, 'harvestd': reghd, 'sn': regsn, 'cutdate': regcutdate, 'fpf': regpdno, 'revenue': regrevno, 'regname': regname}
    if request.method == 'POST':
        form = SmokeRegisterLikeForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.author = request.user
            obj.district = ddistrict[0]
            if obj.revenue:
                #sn = 10 + 999 + revenue + 01
                odf = ddistrict[0].nnn
                if odf.endswith('XX'):
                    odf = obj.fpf
                revenue = obj.revenue
                base = u"%s%3s%05s" % (yy, odf, revenue)
                base_list = SmokeRegister.objects.filter(sn__startswith=base).order_by('sn')
                seq = 1
                if base_list:
                    seq = base_list.count()
                    #seq = base_list[0].sn[10:12]
                    seq = int(seq)+1
                    seq = int(str(seq)[-2:])
                obj.sn = u"%s%3s%05s%02d" % (yy, odf, revenue, seq)
                sn_list = SmokeRegister.objects.filter(sn__iexact=obj.sn).order_by('sn')
                if sn_list:
                    base_list = SmokeRegister.objects.filter(sn__startswith=base).order_by('-sn')[:1]
                    seq = 1
                    if base_list:
                        seq = base_list.count()
                        seq = base_list[0].sn[10:12]
                        seq = int(seq)+1
                        seq = int(str(seq)[-2:])
                    obj.sn = u"%s%3s%05s%02d" % (yy, odf, revenue, seq)
                
            else:
                #sn = 10 + 406 + 99900 + 01
                odf = 406
                odfid = ddistrict[0].odfid
                odfid = int(odfid)
                base = u"%s%3s%05d" % (yy, odf, odfid)
                base_list = SmokeRegister.objects.filter(sn__startswith=base).order_by('sn')
                seq = 1
                if base_list:
                    #seq = base_list[0].sn[10:12]
                    seq = base_list.count()
                    if seq != 99:
                        seq = int(seq)+1
                    seq = int(str(seq)[-2:])
                obj.sn = u"%s%3s%05d%02d" % (yy, odf, odfid, seq)
                hold1 = obj.sn
                #obj.regname = u"%s%3s%05d%02d" % (yy, odf, odfid, seq)
                #obj.sn = 'TESTTEST0000' #104060110099
                sn_list = SmokeRegister.objects.filter(sn__iexact=obj.sn).order_by('sn')
                if sn_list: # 0001-0000 skipped numbers
                    base_list = SmokeRegister.objects.filter(sn__startswith=base).order_by('-sn')[:1]
                    seq = 1
                    if base_list:
                        seq = base_list[0].sn[10:12]
                        if seq != 99:
                            seq = int(seq)+1
                        seq = int(str(seq)[-2:])
                    obj.sn = u"%s%3s%05d%02d" % (yy, odf, odfid, seq)
                    #obj.regname = u"%s%3s%05d%02d" % (yy, odf, odfid, seq)
                    #obj.regname = hold1
                    #obj.sn = 'TESTTEST0001' #1040601100100 - seq of 100 to long, slice it
                    sn_list = SmokeRegister.objects.filter(sn__iexact=obj.sn).order_by('sn')
                    if sn_list: # 0101-0100 second hundred
                        odfid = ddistrict[0].odfid
                        odfid = int(odfid)+1
                        base = u"%s%3s%05d" % (yy, odf, odfid)
                        base_list = SmokeRegister.objects.filter(sn__startswith=base).order_by('-sn')
                        seq = 1
                        if base_list:
                            seq = base_list.count()
                            #seq = base_list[0].sn[10:12]
                            if seq != 99:
                                seq = int(seq)+1
                            seq = int(str(seq)[-2:])
                        obj.sn = u"%s%3s%05d%02d" % (yy, odf, odfid, seq)
                        #obj.regname = u"%s%3s%05d%02d" % (yy, odf, odfid, seq)
                        #obj.regname = hold1
                        #obj.sn = 'TESTTEST0002' #10406 110101 - missing leading zero in odfid, pad it
                        sn_list = SmokeRegister.objects.filter(sn__iexact=obj.sn).order_by('sn')
                        if sn_list: # 0201-0200 third hundred
                            odfid = ddistrict[0].odfid
                            odfid = int(odfid)+1
                            base = u"%s%3s%05d" % (yy, odf, odfid)
                            base_list = SmokeRegister.objects.filter(sn__startswith=base).order_by('-sn')
                            seq = 1
                            if base_list:
                                seq = base_list.count()
                                #seq = base_list[0].sn[10:12]
                                if seq != 99:
                                    seq = int(seq)+1
                                seq = int(str(seq)[-2:])
                            obj.sn = u"%s%3s%05d%02d" % (yy, odf, odfid, seq)
                            sn_list = SmokeRegister.objects.filter(sn__iexact=obj.sn).order_by('sn')
                            if sn_list: #0301-0300 fourth hundred
                                odfid = ddistrict[0].odfid
                                odfid = int(odfid)+1
                                base = u"%s%3s%05d" % (yy, odf, odfid)
                                base_list = SmokeRegister.objects.filter(sn__startswith=base).order_by('-sn')
                                seq = 1
                                if base_list:
                                    seq = base_list.count()
                                    #seq = base_list[0].sn[10:12]
                                    if seq != 99:
                                        seq = int(seq)+1
                                    seq = int(str(seq)[-2:])
                                obj.sn = u"%s%3s%05s%02d" % (yy, odf, odfid, seq)
            obj.sequence = 66
            #return render(request,'fastrax/tndnregister_debug.html', {
            #    'form': form, 'base_list': base_list, 'sn_list': sn_list, 'seq': seq
            #},)
            obj.save() # dupfail
            return HttpResponseRedirect('/%s/' % (obj.sn))
    else:
        form = SmokeRegisterLikeForm(initial=data_dict)

    return render(request,'fastrax/snregisterlike.html', {
        'data_dict': data_dict, 'form': form, 'ddistrict': ddistrict, 'reg_list': reg_list, 'dreg_list': dreg_list, 'trsr': trsr
    },)

@login_required
@permission_required('fastrax.add_smokeplan')
def plan(request):
    if request.method == 'POST':
        form = SmokePlanForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.author = request.user
            obj.save()
            return HttpResponseRedirect('/')
    else:
        form = SmokePlanForm()

    return render(request,'fastrax/plan.html', {
        'form': form,
    },)

@login_required
@permission_required('fastrax.add_smokeplan')
def snplan(request, sn):
    reg_list = SmokeRegister.objects.filter(sn__exact=sn).order_by('sn')[:1]
    regco = reg_list[0].get_county_display()
    regt = u"%s" % (reg_list[0].township.upper())
    regr = u"%s" % (reg_list[0].range.upper())
    regs = u"%s" % (reg_list[0].section.zfill(2))
    regspz = reg_list[0].get_spz_display()
    regreason = reg_list[0].get_reason_display()
    regtype = reg_list[0].get_typeburn_display()
    reglm = reg_list[0].get_loadmethod_display()
    regspecies = reg_list[0].get_fuelspecies_display()
    reghd = reg_list[0].get_harvestd_display()
    #co = County.objects.filter(
    #   Q(name__exact=regco),
    #   Q(state__exact='Oregon')
    #   ).order_by('name')[:1]
    trsr = PLSS.objects.filter(
        Q(township__exact=regt),
        Q(range__exact=regr),
        Q(section__iexact=regs)
        ).order_by('township')[:1]
    plan_list = SmokePlan.objects.filter(
        Q(sn__exact=sn)
        ).order_by('suffix')
    result_list = SmokeResult.objects.filter(
        Q(snid__sn__exact=sn)
        ).order_by('snid')
    #countid = plan_list.count()
    #planid = countid+1
    #plansu = u"%02d" % (planid)
    data_dict = {'sn': sn}
    if request.method == 'POST':
        regacres = reg_list[0].regacres
        form = SmokePlanFormSN2(regacres, request.POST)
        if form.is_valid():
            countid = plan_list.count()
            planid = countid+1
            plansu = u"%02d" % (planid)
            snid = u"%s-%02d" % (sn, planid)
            obj = form.save(commit=False)
            obj.author = request.user
            obj.sn = reg_list[0]
            obj.suffix = plansu
            obj.snid = snid
            obj.save()
#            return SmokePlan.objects.create()
            return HttpResponseRedirect('/%s/' % sn )
    else:
        acrestoburn = u"%s" % (reg_list[0].regacres)
        piletons = u"%s" % (reg_list[0].piletons)
        landingtons = u"%s" % (reg_list[0].landingtons)
        b_u_tonsperacre = u"%s" % (reg_list[0].fuelclass1 + reg_list[0].fuelclass2 + reg_list[0].fuelclass3 + reg_list[0].fuelclass4 + reg_list[0].fuelclass5 + reg_list[0].fuelclass6)
        data_dict = { 'sn': sn, 'acrestoburn': acrestoburn, 'piletons': piletons, 'landingtons': landingtons, 'b_u_tonsperacre': b_u_tonsperacre }
        regacres = reg_list[0].regacres
        form = SmokePlanFormSN2(regacres, initial=data_dict)

    return render(request,'fastrax/snplan.html', {
        'form': form, 'reg_list': reg_list, 'plan_list': plan_list, 'result_list': result_list, 'data_dict': data_dict, 'regco': regco, 'regspz': regspz, 'regreason': regreason, 'regtype': regtype, 'regspecies': regspecies, 'reghd': reghd, 'reglm': reglm, 'trsr': trsr , 'regacres': regacres
    },)

@login_required
@permission_required('fastrax.add_smokeplan')
def snplan2(request, sn):
    reg_list = SmokeRegister.objects.filter(sn__exact=sn).order_by('sn')[:1]
    regco = reg_list[0].get_county_display()
    regt = u"%s" % (reg_list[0].township.upper())
    regr = u"%s" % (reg_list[0].range.upper())
    regs = u"%s" % (reg_list[0].section.zfill(2))
    regspz = reg_list[0].get_spz_display()
    regreason = reg_list[0].get_reason_display()
    regtype = reg_list[0].get_typeburn_display()
    reglm = reg_list[0].get_loadmethod_display()
    regspecies = reg_list[0].get_fuelspecies_display()
    reghd = reg_list[0].get_harvestd_display()
    #co = County.objects.filter(
    #   Q(name__exact=regco),
    #   Q(state__exact='Oregon')
    #   ).order_by('name')[:1]
    trsr = PLSS.objects.filter(
        Q(township__exact=regt),
        Q(range__exact=regr),
        Q(section__iexact=regs)
        ).order_by('township')[:1]
    plan_list = SmokePlan.objects.filter(
        Q(sn__exact=sn)
        ).order_by('suffix')
    result_list = SmokeResult.objects.filter(
        Q(snid__sn__exact=sn)
        ).order_by('snid')
    #countid = plan_list.count()
    #planid = countid+1
    #plansu = u"%02d" % (planid)
    data_dict = {'sn': sn}
    if request.method == 'POST':
        form = SmokePlanFormSN3(request.POST)
        if form.is_valid():
            countid = plan_list.count()
            planid = countid+1
            plansu = u"%02d" % (planid)
            snid = u"%s-%02d" % (sn, planid)
            obj = form.save(commit=False)
            obj.author = request.user
            obj.sn = reg_list[0]
            obj.suffix = plansu
            obj.snid = snid
            obj.save()
#            return SmokePlan.objects.create()
            return HttpResponseRedirect('/%s/' % sn )
    else:
        acrestoburn = u"%s" % (reg_list[0].regacres)
        piletons = u"%s" % (reg_list[0].piletons)
        landingtons = u"%s" % (reg_list[0].landingtons)
        b_u_tonsperacre = u"%s" % (reg_list[0].fuelclass1 + reg_list[0].fuelclass2 + reg_list[0].fuelclass3 + reg_list[0].fuelclass4 + reg_list[0].fuelclass5 + reg_list[0].fuelclass6)
        data_dict = { 'sn': sn, 'acrestoburn': acrestoburn, 'piletons': piletons, 'landingtons': landingtons, 'b_u_tonsperacre': b_u_tonsperacre }
        form = SmokePlanFormSN3(initial=data_dict)

    return render(request,'fastrax/snplan2.html', {
        'form': form, 'reg_list': reg_list, 'plan_list': plan_list, 'result_list': result_list, 'data_dict': data_dict, 'regco': regco, 'regspz': regspz, 'regreason': regreason, 'regtype': regtype, 'regspecies': regspecies, 'reghd': reghd, 'reglm': reglm, 'trsr': trsr 
    },)

def snpnalt(request, sn, pn):
    reg_list = SmokeRegister.objects.filter(sn__exact=sn).order_by('sn')[:1]
    plan_list = SmokePlan.objects.filter(
        Q(sn__exact=sn),
        Q(suffix__exact=pn)
        ).order_by('snid')[:1]
    result_list = SmokeResult.objects.filter(
        Q(snid__sn__exact=sn),
        Q(snid__suffix__exact=pn)
        )
    return render(request,'fastrax/snpnalt.html', {'reg_list': reg_list, 'plan_list': plan_list, 'result_list': result_list},)

def snpn(request, sn, pn):
    reg_list = SmokeRegister.objects.filter(sn__exact=sn).order_by('sn')[:1]
    regco = reg_list[0].get_county_display()
    regt = u"%s" % (reg_list[0].township.upper())
    regr = u"%s" % (reg_list[0].range.upper())
    regs = u"%s" % (reg_list[0].section.zfill(2))
    regspz = reg_list[0].get_spz_display()
    regreason = reg_list[0].get_reason_display()
    regtype = reg_list[0].get_typeburn_display()
    reglm = reg_list[0].get_loadmethod_display()
    regspecies = reg_list[0].get_fuelspecies_display()
    reghd = reg_list[0].get_harvestd_display()
    #co = County.objects.filter(
    #   Q(name__exact=regco),
    #   Q(state__exact='Oregon')
    #   ).order_by('name')[:1]
    trsr = PLSS.objects.filter(
        Q(township__exact=regt),
        Q(range__exact=regr),
        Q(section__iexact=regs)
        ).order_by('township')[:1]
    plan_list = SmokePlan.objects.filter(
        Q(sn__exact=sn),
        Q(suffix__exact=pn)
        ).order_by('snid')[:1]
    result_list = SmokeResult.objects.filter(
        Q(snid__sn__exact=sn),
        Q(snid__suffix__exact=pn)
        )
    if result_list:
        resigm = result_list[0].get_ignitionmethod_display()
        reswdr = result_list[0].get_winddirection_display()
        reskhr = result_list[0].get_thousandhourmethod_display()
        ressno = result_list[0].get_snowoffmonth_display()
    else:
        resigm = 0
        reswdr = 0
        reskhr = 0
        ressno = 0
    return render(request,'fastrax/snpn.html', {'reg_list': reg_list, 'plan_list': plan_list, 'result_list': result_list, 'regco': regco, 'regspz': regspz, 'regreason': regreason, 'regtype': regtype, 'regspecies': regspecies, 'reghd': reghd, 'reglm': reglm, 'trsr': trsr , 'resigm': resigm, 'reswdr': reswdr, 'reskhr': reskhr, 'ressno': ressno},)

@login_required
@permission_required('fastrax.add_smokeresult')
def result(request):
    if request.method == 'POST':
        form = SmokeResultForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.author = request.user
            obj.save()
            return HttpResponseRedirect('/')
    else:
        form = SmokeResultForm()

    return render(request,'fastrax/result.html', {
        'form': form,
    },)

def getsnid(self):
    u"%s-%s" % (self.sn, self.suffix)

@login_required
@permission_required('fastrax.add_smokeresult')
def snpnresult1(request, sn, pn):
    reg_list = SmokeRegister.objects.filter(sn__exact=sn).order_by('sn')[:1]
    regco = reg_list[0].get_county_display()
    regt = u"%s" % (reg_list[0].township.upper())
    regr = u"%s" % (reg_list[0].range.upper())
    regs = u"%s" % (reg_list[0].section.zfill(2))
    regspz = reg_list[0].get_spz_display()
    regreason = reg_list[0].get_reason_display()
    regtype = reg_list[0].get_typeburn_display()
    reglm = reg_list[0].get_loadmethod_display()
    regspecies = reg_list[0].get_fuelspecies_display()
    reghd = reg_list[0].get_harvestd_display()
    #co = County.objects.filter(
    #   Q(name__exact=regco),
    #   Q(state__exact='Oregon')
    #   ).order_by('name')[:1]
    trsr = PLSS.objects.filter(
        Q(township__exact=regt),
        Q(range__exact=regr),
        Q(section__iexact=regs)
        ).order_by('township')[:1]
    plan_list = SmokePlan.objects.filter(
        Q(sn__exact=sn),
        Q(suffix__exact=pn)
        ).order_by('snid')[:1]
    result_list = SmokeResult.objects.filter(
        Q(snid__sn__exact=sn),
        Q(snid__suffix__exact=pn)
        )
    snid = u"%s" % (plan_list[0].pk)
    data_dict = {'snid': snid}
    if request.method == 'POST':
        regacres = reg_list[0].regacres
        form = SmokeResultFormSN2(regacres, request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.author = request.user
            obj.notaccomplished = False
            obj.snid = plan_list[0]
            obj.save()
            return HttpResponseRedirect('/%s/' % sn )
    else:
        regacres = reg_list[0].regacres
        form = SmokeResultFormSN2(regacres, initial=data_dict)
    return render(request,'fastrax/snpnresult1.html', {
        'form': form, 'reg_list': reg_list, 'plan_list': plan_list, 'result_list': result_list, 'regco': regco, 'regspz': regspz, 'regreason': regreason, 'regtype': regtype, 'regspecies': regspecies, 'reghd': reghd, 'reglm': reglm, 'trsr': trsr },)

@login_required
@permission_required('fastrax.add_smokeresult')
def snpnresult(request, sn, pn):
    reg_list = SmokeRegister.objects.filter(sn__exact=sn).order_by('sn')[:1]
    regco = reg_list[0].get_county_display()
    regt = u"%s" % (reg_list[0].township.upper())
    regr = u"%s" % (reg_list[0].range.upper())
    regs = u"%s" % (reg_list[0].section.zfill(2))
    regspz = reg_list[0].get_spz_display()
    regreason = reg_list[0].get_reason_display()
    regtype = reg_list[0].get_typeburn_display()
    reglm = reg_list[0].get_loadmethod_display()
    regspecies = reg_list[0].get_fuelspecies_display()
    reghd = reg_list[0].get_harvestd_display()
    #co = County.objects.filter(
    #   Q(name__exact=regco),
    #   Q(state__exact='Oregon')
    #   ).order_by('name')[:1]
    trsr = PLSS.objects.filter(
        Q(township__exact=regt),
        Q(range__exact=regr),
        Q(section__iexact=regs)
        ).order_by('township')[:1]
    plan_list = SmokePlan.objects.filter(
        Q(sn__exact=sn),
        Q(suffix__exact=pn)
        ).order_by('snid')[:1]
    result_list = SmokeResult.objects.filter(
        Q(snid__sn__exact=sn),
        Q(snid__suffix__exact=pn)
        )
    snid = u"%s" % (plan_list[0].pk)
    if request.method == 'POST':
        form = SmokeResultFormSN3(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.author = request.user
            obj.notaccomplished = False
            obj.snid = plan_list[0]
            obj.save()
            return HttpResponseRedirect('/%s/' % sn )
    else:
        acresburned = u"%s" % (plan_list[0].acrestoburn)
        b_u_tonsperacred = u"%s" % (plan_list[0].b_u_tonsperacre)
        piletonned = u"%s" % (plan_list[0].piletons)
        landingtonned = u"%s" % (plan_list[0].landingtons)
        ignitiondated = u"%s" % (plan_list[0].ignitiondate)
        ignitiontimed = u"%s" % (plan_list[0].ignitiontime)
        data_dict = { 'snid': snid, 'acresburned': acresburned, 'piletonned': piletonned, 'landingtonned': landingtonned, 'b_u_tonsperacred': b_u_tonsperacred, 'ignitiondated': ignitiondated, 'ignitiontimed': ignitiontimed }
        if plan_list[0].piletons >= 1:
            ignitionmethod = ' '
            ignitionduration = 0
            weatherstation = 'NA'
            airtemperature = 0
            relativehumidity = 0
            winddirection = '  '
            windspeed = 0
            tenhour = 0
            thousandhour = 0
            thousandhourmethod = ' '
            dayssincerain = 0
            snowoffmonth = ' '
            data_dict = { 'snid': snid, 'acresburned': acresburned, 'piletonned': piletonned, 'landingtonned': landingtonned, 'b_u_tonsperacred': b_u_tonsperacred, 'ignitiondated': ignitiondated, 'ignitiontimed': ignitiontimed, 'ignitionmethod': ignitionmethod, 'ignitionduration': ignitionduration, 'weatherstation': weatherstation, 'airtemperature': airtemperature, 'relativehumidity': relativehumidity, 'winddirection': winddirection, 'windspeed': windspeed, 'tenhour': tenhour, 'thousandhour': thousandhour, 'thousandhourmethod': thousandhourmethod, 'dayssincerain': dayssincerain, 'snowoffmonth': snowoffmonth }
        form = SmokeResultFormSN3(initial=data_dict) # Unbound
    return render(request,'fastrax/snpnresult.html', {
        'form': form, 'reg_list': reg_list, 'plan_list': plan_list, 'result_list': result_list, 'regco': regco, 'regspz': regspz, 'regreason': regreason, 'regtype': regtype, 'regspecies': regspecies, 'reghd': reghd, 'reglm': reglm, 'trsr': trsr },)

@login_required
@permission_required('fastrax.add_smokeresult')
def snpnnoresult(request, sn, pn):
    reg_list = SmokeRegister.objects.filter(sn__exact=sn).order_by('sn')[:1]
    regco = reg_list[0].get_county_display()
    regt = u"%s" % (reg_list[0].township.upper())
    regr = u"%s" % (reg_list[0].range.upper())
    regs = u"%s" % (reg_list[0].section.zfill(2))
    regspz = reg_list[0].get_spz_display()
    regreason = reg_list[0].get_reason_display()
    regtype = reg_list[0].get_typeburn_display()
    reglm = reg_list[0].get_loadmethod_display()
    regspecies = reg_list[0].get_fuelspecies_display()
    reghd = reg_list[0].get_harvestd_display()
    #co = County.objects.filter(
    #   Q(name__exact=regco),
    #   Q(state__exact='Oregon')
    #   ).order_by('name')[:1]
    trsr = PLSS.objects.filter(
        Q(township__exact=regt),
        Q(range__exact=regr),
        Q(section__iexact=regs)
        ).order_by('township')[:1]
    plan_list = SmokePlan.objects.filter(
        Q(sn__exact=sn),
        Q(suffix__exact=pn)
        ).order_by('suffix')[:1]
    result_list = SmokeResult.objects.filter(
        Q(snid__sn__exact=sn),
        Q(snid__suffix__exact=pn)
        )
    snid = u"%s" % (plan_list[0].pk)
    data_dict = {'snid': snid}
    if request.method == 'POST':
        form = NoResultFormSN2(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.author = request.user
            obj.notaccomplished = True
            obj.snid = plan_list[0]
            obj.acresburned = 0
            obj.landingtonned = 0
            obj.piletonned = 0
            obj.b_u_tonsperacred = 0
            obj.ignitiondated = plan_list[0].ignitiondate
            obj.ignitiontimed = plan_list[0].ignitiontime
            obj.ignitionmethod = 'M'
            obj.ignitionduration = 0
            obj.rapidignition = False
            obj.smokeintrusion = False
            obj.airtemperature = 0
            obj.relativehumidity = 0
            obj.winddirection = '00'
            obj.windspeed = 0
            obj.tenhour = 0
            obj.thousandhour = 0
            obj.thousandhourmethod = 'N'
            obj.dayssincerain = 0
            obj.snowoffmonth = '00'
            obj.save()
            return HttpResponseRedirect('/%s/' % sn )# Redirect after POST
    else:
        data_dict = {'snid': snid, 'notaccomplished': True, 'acresburned': 0, 'landingtonned': 0, 'piletonned': 0, 'b_u_tonsperacred': 0, 'ignitiondated': '1900-01-01', 'ignitiontimed': '00:00', 'ignitionmethod': 'M', 'ignitionduration': 0, 'rapidignition': False, 'smokeintrusion': False, 'airtemperature': 0, 'relativehumidity': 0, 'winddirection': '00', 'windspeed': 0, 'tenhour': 0, 'thousandhour': 0, 'thousandhourmethod': 'N', 'dayssincerain': 0, 'snowoffmonth': '00'}
        form = NoResultFormSN2(initial=data_dict)

    return render(request,'fastrax/snpnnoresult.html', {
        'form': form, 'reg_list': reg_list, 'plan_list': plan_list, 'result_list': result_list, 'regco': regco, 'regspz': regspz, 'regreason': regreason, 'regtype': regtype, 'regspecies': regspecies, 'reghd': reghd, 'reglm': reglm, 'trsr': trsr , 'data_dict': data_dict
    },)

def odfdate(request, year, mo, da):
    dates_reg_list = SmokeRegister.objects.filter(
        Q(regdate__year=year),
        Q(regdate__month=mo),
        Q(regdate__day=da)
        ).order_by('sn')
    dates_plan_list = SmokePlan.objects.filter(
        Q(plan_date__year=year),
        Q(plan_date__month=mo),
        Q(plan_date__day=da)
        ).order_by('sn', 'suffix')
    dates_result_list = SmokeResult.objects.filter(
        Q(result_date__year=year),
        Q(result_date__month=mo),
        Q(result_date__day=da)
        ).order_by('snid__sn', 'snid__suffix')
    odfyear = year
    odfmo = mo
    odfda = da
    return render(request,'fastrax/odfdate.html', {'dates_reg_list': dates_reg_list, 'dates_plan_list': dates_plan_list, 'dates_result_list': dates_result_list, 'odfyear': odfyear, 'odfmo': odfmo, 'odfda': odfda})

def odfmonth(request, year, mo):
    dates_reg_list = SmokeRegister.objects.filter(
        Q(regdate__year=year),
        Q(regdate__month=mo)
        ).order_by('sn')
    dates_plan_list = SmokePlan.objects.filter(
        Q(plan_date__year=year),
        Q(plan_date__month=mo)
        ).order_by('sn', 'suffix')
    dates_result_list = SmokeResult.objects.filter(
        Q(result_date__year=year),
        Q(result_date__month=mo)
        ).order_by('snid__sn', 'snid__suffix')
    odfyear = year
    odfmo = mo
    return render(request,'fastrax/odfdate.html', {'dates_reg_list': dates_reg_list, 'dates_plan_list': dates_plan_list, 'dates_result_list': dates_result_list, 'odfyear': odfyear, 'odfmo': odfmo})

def odfyear(request, year):
    dates_reg_list = SmokeRegister.objects.filter(
        Q(regdate__year=year)
        ).order_by('sn')
    dates_plan_list = SmokePlan.objects.filter(
        Q(plan_date__year=year)
        ).order_by('sn', 'suffix')
    dates_result_list = SmokeResult.objects.filter(
        Q(result_date__year=year)
        ).order_by('snid__sn', 'snid__suffix')
    odfyear = year
    return render(request,'fastrax/odfdate.html', {'dates_reg_list': dates_reg_list, 'dates_plan_list': dates_plan_list, 'dates_result_list': dates_result_list, 'odfyear': odfyear})

def odfandate(request, year, mo, da):
    dates_reg_list = SmokeRegister.objects.filter(
        Q(regdate__year=year),
        Q(regdate__month=mo),
        Q(regdate__day=da)
        ).order_by('sn')
    dates_plan_list = SmokePlan.objects.filter(
        Q(plan_date__year=year),
        Q(plan_date__month=mo),
        Q(plan_date__day=da)
        ).order_by('sn', 'suffix')
    dates_result_list = SmokeResult.objects.filter(
        Q(result_date__year=year),
        Q(result_date__month=mo),
        Q(result_date__day=da)
        ).order_by('snid__sn', 'snid__suffix')
    odfyear = year
    odfmo = mo
    odfda = da
    return render(request,'fastrax/odfandate.html', {'dates_reg_list': dates_reg_list, 'dates_plan_list': dates_plan_list, 'dates_result_list': dates_result_list, 'odfyear': odfyear, 'odfmo': odfmo, 'odfda': odfda})

def odfanmonth(request, year, mo):
    dates_reg_list = SmokeRegister.objects.filter(
        Q(regdate__year=year),
        Q(regdate__month=mo)
        ).order_by('sn')
    dates_plan_list = SmokePlan.objects.filter(
        Q(plan_date__year=year),
        Q(plan_date__month=mo)
        ).order_by('sn', 'suffix')
    dates_result_list = SmokeResult.objects.filter(
        Q(result_date__year=year),
        Q(result_date__month=mo)
        ).order_by('snid__sn', 'snid__suffix')
    odfyear = year
    odfmo = mo
    return render(request,'fastrax/odfandate.html', {'dates_reg_list': dates_reg_list, 'dates_plan_list': dates_plan_list, 'dates_result_list': dates_result_list, 'odfyear': odfyear, 'odfmo': odfmo})

def odfanyear(request, year):
    dates_reg_list = SmokeRegister.objects.filter(
        Q(regdate__year=year)
        ).order_by('sn')
    dates_plan_list = SmokePlan.objects.filter(
        Q(plan_date__year=year)
        ).order_by('sn', 'suffix')
    dates_result_list = SmokeResult.objects.filter(
        Q(result_date__year=year)
        ).order_by('snid__sn', 'snid__suffix')
    odfyear = year
    return render(request,'fastrax/odfandate.html', {'dates_reg_list': dates_reg_list, 'dates_plan_list': dates_plan_list, 'dates_result_list': dates_result_list, 'odfyear': odfyear})

def odfdatetxt(request, year, mo, da):
    dates_reg_list = SmokeRegister.objects.filter(
        Q(regdate__year=year),
        Q(regdate__month=mo),
        Q(regdate__day=da)
        ).order_by('sn')
    dates_plan_list = SmokePlan.objects.filter(
        Q(plan_date__year=year),
        Q(plan_date__month=mo),
        Q(plan_date__day=da)
        ).order_by('sn', 'suffix')
    dates_result_list = SmokeResult.objects.filter(
        Q(result_date__year=year),
        Q(result_date__month=mo),
        Q(result_date__day=da)
        ).order_by('snid__sn', 'snid__suffix')
    odfyear = year
    odfmo = mo
    odfda = da
    result = render(request,'fastrax/odfdate.txt', {'dates_reg_list': dates_reg_list, 'dates_plan_list': dates_plan_list, 'dates_result_list': dates_result_list, 'odfyear': odfyear, 'odfmo': odfmo, 'odfda': odfda})
    return HttpResponse(result, content_type='text/plain') 

def odfmotxt(request, year, mo):
    dates_reg_list = SmokeRegister.objects.filter(
        Q(regdate__year=year),
        Q(regdate__month=mo)
        ).order_by('sn')
    dates_plan_list = SmokePlan.objects.filter(
        Q(plan_date__year=year),
        Q(plan_date__month=mo)
        ).order_by('sn', 'suffix')
    dates_result_list = SmokeResult.objects.filter(
        Q(result_date__year=year),
        Q(result_date__month=mo)
        ).order_by('snid__sn', 'snid__suffix')
    odfyear = year
    odfmo = mo
    return render(request,'fastrax/odfdate.txt', {'dates_reg_list': dates_reg_list, 'dates_plan_list': dates_plan_list, 'dates_result_list': dates_result_list, 'odfyear': odfyear, 'odfmo': odfmo})

def odfyrtxt(request, year):
    dates_reg_list = SmokeRegister.objects.filter(
        Q(regdate__year=year)
        ).order_by('sn')
    dates_plan_list = SmokePlan.objects.filter(
        Q(plan_date__year=year)
        ).order_by('sn', 'suffix')
    dates_result_list = SmokeResult.objects.filter(
        Q(result_date__year=year)
        ).order_by('snid__sn', 'snid__suffix')
    odfyear = year
    return render(request,'fastrax/odfdate.txt', {'dates_reg_list': dates_reg_list, 'dates_plan_list': dates_plan_list, 'dates_result_list': dates_result_list, 'odfyear': odfyear})

def odfjson(request, year, mo, da):
    if mo == '00':
        dates_result_list = SmokeResult.objects.filter(
            Q(result_date__year=year)
            ).exclude(
            Q(snid__plan_date__year=year)
            ).exclude(
            Q(snid__sn__regdate__year=year)
            ).exclude(
            Q(snid__snid__icontains='x')
            ).order_by('snid__sn', 'snid__suffix')
        dates_plan_list = SmokePlan.objects.filter(
            Q(plan_date__year=year)
            ).exclude(
            Q(sn__regdate__year=year)
            ).exclude(
            Q(sn__sn__icontains='x')
            ).order_by('sn', 'suffix')
        dates_reg_list = SmokeRegister.objects.filter(
            Q(regdate__year=year)
            ).exclude(
            sn__icontains='x'
            ).order_by('sn')
    elif da == '00':
        dates_result_list = SmokeResult.objects.filter(
            Q(result_date__year=year),
            Q(result_date__month=mo)
            ).exclude(
            Q(snid__plan_date__year=year),
            Q(snid__plan_date__month=mo)
            ).exclude(
            Q(snid__sn__regdate__year=year),
            Q(snid__sn__regdate__month=mo)
            ).exclude(
            Q(snid__snid__icontains='x')
            ).order_by('snid__sn', 'snid__suffix')
        dates_plan_list = SmokePlan.objects.filter(
            Q(plan_date__year=year),
            Q(plan_date__month=mo)
            ).exclude(
            Q(sn__regdate__year=year),
            Q(sn__regdate__month=mo)
            ).exclude(
            Q(sn__sn__icontains='x')
            ).order_by('sn', 'suffix')
        dates_reg_list = SmokeRegister.objects.filter(
            Q(regdate__year=year),
            Q(regdate__month=mo)
            ).exclude(
            sn__icontains='x'
            ).order_by('sn')
    else:
        dates_result_list = SmokeResult.objects.filter(
            Q(result_date__year=year),
            Q(result_date__month=mo),
            Q(result_date__day=da)
            ).exclude(
            Q(notaccomplished=True)
            ).exclude(
            Q(snid__snid__icontains='x')
            ).order_by('snid__sn', 'snid__suffix')
        dates_plan_list = SmokePlan.objects.filter(
            Q(plan_date__year=year),
            Q(plan_date__month=mo),
            Q(plan_date__day=da)
            ).exclude(
            Q(result_snid__result_date__year=year),
            Q(result_snid__result_date__month=mo),
            Q(result_snid__result_date__day=da)
            ).exclude(
            Q(result_snid__notaccomplished=True)
            ).exclude(
            Q(sn__sn__icontains='x')
            ).order_by('sn', 'suffix')
        dates_reg_list = SmokeRegister.objects.filter(
            Q(regdate__year=year),
            Q(regdate__month=mo),
            Q(regdate__day=da)
            ).exclude(
            sn__icontains='x'
            ).order_by('sn')
    for object in dates_result_list:
        try:
            snum = u"%s" % (object.snid__sn)
            sin = int(snum)
            object.error = ''
        except:
            object.error = 'BAD SN'
        try:
            plss = PLSS.objects.get(
                Q(township=object.snid.sn.township.upper()),
                Q(range=object.snid.sn.range.upper()),
                Q(section=object.snid.sn.section.zfill(2))
                )
            object.y = plss.y
            object.x = plss.x
        except:
            object.y = ''
            object.x = ''
        try:
            object.town=object.snid.sn.township.upper()
            if object.town[2] == '0':
                object.town = object.town[0:2] + object.town[3]
            elif object.town[2] != '0':
                object.town = object.town[0:2] + '.' + object.town[3]
        except:
            object.town = 'null'
        try:
            object.rang=object.snid.sn.range.upper()
            if object.rang[2] == '0':
                object.rang = object.rang[0:2] + object.rang[3]
            elif object.rang[2] != '0':
                object.rang = object.rang[0:2] + '.' + object.rang[3]
        except:
            object.rang = 'null'
    for object in dates_plan_list:
        try:
            snum = u"%s" % (object.sn)
            sin = int(snum)
            object.error = ''
        except:
            object.error = 'BAD SN'
        try:
            plss = PLSS.objects.get(
                Q(township=object.sn.township.upper()),
                Q(range=object.sn.range.upper()),
                Q(section=object.sn.section.zfill(2))
                )
            object.y = plss.y
            object.x = plss.x
        except:
            object.y = ''
            object.x = ''
        try:
            object.town=object.sn.township.upper()
            if object.town[2] == '0':
                object.town = object.town[0:2] + object.town[3]
            elif object.town[2] != '0':
                object.town = object.town[0:2] + '.' + object.town[3]
        except:
            object.town = 'null'
        try:
            object.range=object.sn.range.upper()
            if object.range[2] == '0':
                object.rang = object.rang[0:2] + object.rang[3]
            elif object.rang[2] != '0':
                object.rang = object.rang[0:2] + '.' + object.rang[3]
        except:
            object.rang = 'null'
    for object in dates_reg_list:
        try:
            snum = u"%s" % (object.sn)
            sin = int(snum)
            object.error = ''
        except:
            object.error = 'BAD SN'
        try:
            plss = PLSS.objects.get(
                Q(township=object.township.upper()),
                Q(range=object.range.upper()),
                Q(section=object.section.zfill(2))
                )
            object.y = plss.y
            object.x = plss.x
        except:
            object.y = ''
            object.x = ''
        try:
            object.town=object.township.upper()
            if object.town[2] == '0':
                object.town = object.town[0:2] + object.town[3]
            elif object.town[2] != '0':
                object.town = object.town[0:2] + '.' + object.town[3]
        except:
            object.town = 'null'
        try:
            object.rang=object.range.upper()
            if object.rang[2] == '0':
                object.rang = object.rang[0:2] + object.rang[3]
            elif object.rang[2] != '0':
                object.rang = object.rang[0:2] + '.' + object.rang[3]
        except:
            object.rang = 'null'
    odfyear = year
    odfmo = mo
    odfda = da
    result = render(request,'fastrax/odf.json', {'dates_reg_list': dates_reg_list, 'dates_plan_list': dates_plan_list, 'dates_result_list': dates_result_list})
    return HttpResponse(result, content_type='text/plain') 

def odfjsondaily(request):
    now = datetime.datetime.today() 
    year = now.year
    mo = now.month
    da = now.day
    hr = now.hour
    mi = now.minute
    dateyear = year
    datemo = mo
    dateda = da
    datehr = hr
    datemi = mi
    iyear = int(dateyear)
    imo = int(datemo)
    ida = int(dateda)
    ihr = int(datehr)
    imi = int(datemi)
    sun = datetime.datetime(iyear, imo, ida)
    starp = sun - datetime.timedelta(hours=13, minutes=0, seconds=0)
    storp = sun + datetime.timedelta(hours=24, minutes=0, seconds=0)
    #dates_reg_list = SmokeRegister.objects.filter(entered__range=(starp, storp)).order_by('entered')
    #dates_regu_list = SmokeRegister.objects.filter(modified__range=(starp, storp)).exclude(entered__range=(starp, storp)).order_by('modified')
    #dates_plan_list = SmokePlan.objects.filter(entered__range=(starp, storp)).order_by('entered')
    #dates_result_list = SmokeResult.objects.filter(entered__range=(starp, storp)).order_by('entered')
    #dates_resultu_list = SmokeResult.objects.filter(modified__range=(starp, storp)).exclude(entered__range=(starp, storp)).order_by('modified')
    dates_result_list = SmokeResult.objects.filter(
        Q(entered__range=(starp, storp))
        ).exclude(
        Q(snid__snid__icontains='x')
        ).exclude(
        Q(notaccomplished=True)
        ).order_by('snid__sn', 'snid__suffix')
    dates_plan_list = SmokePlan.objects.filter(
        Q(entered__range=(starp, storp))
        ).exclude(
        Q(result_snid__entered__range=(starp, storp))
        ).exclude(
        Q(result_snid__notaccomplished=True)
        ).exclude(
        Q(sn__sn__icontains='x')
        ).order_by('sn', 'suffix')
    dates_reg_list = SmokeRegister.objects.filter(
        Q(entered__range=(starp, storp))
        ).exclude(
        sn__icontains='x'
        ).order_by('sn')
    for object in dates_result_list:
        try:
            snum = u"%s" % (object.snid__sn)
            sin = int(snum)
            object.error = ''
        except:
            object.error = 'BAD SN'
        try:
            plss = PLSS.objects.get(
                Q(township=object.snid.sn.township.upper()),
                Q(range=object.snid.sn.range.upper()),
                Q(section=object.snid.sn.section.zfill(2))
                )
            object.y = plss.y
            object.x = plss.x
        except:
            object.y = ''
            object.x = ''
        try:
            object.town=object.snid.sn.township.upper()
            if object.town[2] == '0':
                object.town = object.town[0:2] + object.town[3]
            elif object.town[2] != '0':
                object.town = object.town[0:2] + '.' + object.town[3]
        except:
            object.town = 'null'
        try:
            object.rang=object.snid.sn.range.upper()
            if object.rang[2] == '0':
                object.rang = object.rang[0:2] + object.rang[3]
            elif object.rang[2] != '0':
                object.rang = object.rang[0:2] + '.' + object.rang[3]
        except:
            object.rang = 'null'
    for object in dates_plan_list:
        try:
            snum = u"%s" % (object.sn)
            sin = int(snum)
            object.error = ''
        except:
            object.error = 'BAD SN'
        try:
            plss = PLSS.objects.get(
                Q(township=object.sn.township.upper()),
                Q(range=object.sn.range.upper()),
                Q(section=object.sn.section.zfill(2))
                )
            object.y = plss.y
            object.x = plss.x
        except:
            object.y = ''
            object.x = ''
        try:
            object.town=object.sn.township.upper()
            if object.town[2] == '0':
                object.town = object.town[0:2] + object.town[3]
            elif object.town[2] != '0':
                object.town = object.town[0:2] + '.' + object.town[3]
        except:
            object.town = 'null'
        try:
            object.range=object.sn.range.upper()
            if object.range[2] == '0':
                object.rang = object.rang[0:2] + object.rang[3]
            elif object.rang[2] != '0':
                object.rang = object.rang[0:2] + '.' + object.rang[3]
        except:
            object.rang = 'null'
    for object in dates_reg_list:
        try:
            snum = u"%s" % (object.sn)
            sin = int(snum)
            object.error = ''
        except:
            object.error = 'BAD SN'
        try:
            plss = PLSS.objects.get(
                Q(township=object.township.upper()),
                Q(range=object.range.upper()),
                Q(section=object.section.zfill(2))
                )
            object.y = plss.y
            object.x = plss.x
        except:
            object.y = ''
            object.x = ''
        try:
            object.town=object.township.upper()
            if object.town[2] == '0':
                object.town = object.town[0:2] + object.town[3]
            elif object.town[2] != '0':
                object.town = object.town[0:2] + '.' + object.town[3]
        except:
            object.town = 'null'
        try:
            object.rang=object.range.upper()
            if object.rang[2] == '0':
                object.rang = object.rang[0:2] + object.rang[3]
            elif object.rang[2] != '0':
                object.rang = object.rang[0:2] + '.' + object.rang[3]
        except:
            object.rang = 'null'
    odfyear = year
    odfmo = mo
    odfda = da
    result = render(request,'fastrax/odfd.json', {'dates_reg_list': dates_reg_list, 'dates_plan_list': dates_plan_list, 'dates_result_list': dates_result_list, 'starp': starp, 'storp': storp })
    return HttpResponse(result, content_type='text/plain') 

def date(request, year, mo, da):
    dates_reg_list = SmokeRegister.objects.filter(
        Q(regdate__year=year),
        Q(regdate__month=mo),
        Q(regdate__day=da)
        ).annotate(black=Sum('plan_sn__result_snid__acresburned')).order_by('sn')
    for object in dates_reg_list:
        if object.black == None:
            object.color = 'black'
        elif object.black < object.regacres:
            object.color = 'green'
        elif object.black >= object.regacres:
            object.color = 'red'
    dates_plan_list = SmokePlan.objects.filter(
        Q(plan_date__year=year),
        Q(plan_date__month=mo),
        Q(plan_date__day=da)
        ).order_by('sn', 'suffix')
    dates_result_list = SmokeResult.objects.filter(
        Q(result_date__year=year),
        Q(result_date__month=mo),
        Q(result_date__day=da)
        ).order_by('snid__sn', 'snid__suffix')
    dateyear = year
    intyear = int(year)
    datemo = mo
    intmo = int(mo)
    dateda = da
    intda = int(da)
    last = 23
    first_month = datetime.datetime(intyear, intmo, intda, last)
    previous_months = (first_month - relativedelta(hours = hours) for hours in range(0, last, 1))
    themonths = previous_months
    e=[]
    cumu = dates_reg_list.count()
    cump = dates_plan_list.count()
    cumr = dates_result_list.count()
    maxcount = 0
    maxplan = 0
    maxresult = 0
    for month in themonths:
        iyear = month.year
        imonth = month.month
        idate = month.day
        ihour = month.hour
        entry_count = SmokeRegister.objects.filter(
            Q(regdate__year=iyear),
            Q(regdate__month=imonth),
            Q(regdate__day=idate),
            Q(entered__gte=datetime.datetime(iyear,imonth,idate,ihour,0)) & Q(entered__lte=datetime.datetime(iyear,imonth,idate,ihour,59))
            ).count()
        if entry_count >= maxcount:
            maxcount = entry_count
        plan_count = SmokePlan.objects.filter(
            Q(plan_date__year=iyear),
            Q(plan_date__month=imonth),
            Q(plan_date__day=idate),
            Q(entered__gte=datetime.datetime(iyear,imonth,idate,ihour,0)) & Q(entered__lte=datetime.datetime(iyear,imonth,idate,ihour,59))
            ).count()
        if plan_count >= maxplan:
            maxplan = plan_count
        result_count = SmokeResult.objects.filter(
            Q(result_date__year=iyear),
            Q(result_date__month=imonth),
            Q(result_date__day=idate),
            Q(entered__gte=datetime.datetime(iyear,imonth,idate,ihour,0)) & Q(entered__lte=datetime.datetime(iyear,imonth,idate,ihour,59))
            ).count()
        if result_count >= maxresult:
            maxresult = result_count
        dict = {'month': ihour, 'count': entry_count, 'cumu': cumu, 'countp': plan_count, 'cump': cump, 'countr': result_count, 'cumr': cumr }
        e.append(dict)
        cumu = cumu - entry_count
        cump = cump - plan_count
        cumr = cumr - result_count
        maxplan = max(maxplan,maxresult)
    entry_dates = e
    return render(request,'fastrax/date.html', {'entry_dates': entry_dates, 'maxcount': maxcount, 'maxplan': maxplan, 'dates_reg_list': dates_reg_list, 'dates_plan_list': dates_plan_list, 'dates_result_list': dates_result_list, 'dateyear': dateyear, 'datemo': datemo, 'dateda': dateda})

def month(request, year, mo):
    dates_reg_list = SmokeRegister.objects.filter(
        Q(regdate__year=year),
        Q(regdate__month=mo)
        ).annotate(black=Sum('plan_sn__result_snid__acresburned')).order_by('sn')
    for object in dates_reg_list:
        if object.black == None:
            object.color = 'black'
        elif object.black < object.regacres:
            object.color = 'green'
        elif object.black >= object.regacres:
            object.color = 'red'
    dates_plan_list = SmokePlan.objects.filter(
        Q(plan_date__year=year),
        Q(plan_date__month=mo)
        ).order_by('sn', 'suffix')
    dates_result_list = SmokeResult.objects.filter(
        Q(result_date__year=year),
        Q(result_date__month=mo)
        ).order_by('snid__sn', 'snid__suffix')
    dateyear = year
    intyear = int(year)
    datemo = mo
    intmo = int(mo)
    last = calendar.monthrange(intyear, intmo)[1]
    first_month = datetime.datetime(intyear, intmo, last)
    previous_months = (first_month - relativedelta(days = days) for days in range(0, last, 1))
    themonths = previous_months
    e=[]
    cumu = dates_reg_list.count()
    cump = dates_plan_list.count()
    cumr = dates_result_list.count()
    maxcount = 0
    maxplan = 0
    maxresult = 0
    for month in themonths:
        iyear = month.year
        imonth = month.month
        idate = month.day
        ihour = month.hour
        entry_count = SmokeRegister.objects.filter(
            Q(regdate__year=iyear),
            Q(regdate__month=imonth),
            Q(regdate__day=idate)
            ).count()
        if entry_count >= maxcount:
            maxcount = entry_count
        plan_count = SmokePlan.objects.filter(
            Q(plan_date__year=iyear),
            Q(plan_date__month=imonth),
            Q(plan_date__day=idate)
            ).count()
        if plan_count >= maxplan:
            maxplan = plan_count
        result_count = SmokeResult.objects.filter(
            Q(result_date__year=iyear),
            Q(result_date__month=imonth),
            Q(result_date__day=idate)
            ).count()
        if result_count >= maxresult:
            maxresult = result_count
        dict = {'month': idate, 'count': entry_count, 'cumu': cumu, 'countp': plan_count, 'cump': cump, 'countr': result_count, 'cumr': cumr }
        e.append(dict)
        cumu = cumu - entry_count
        cump = cump - plan_count
        cumr = cumr - result_count
        maxplan = max(maxplan,maxresult)
    entry_dates = e
    return render(request,'fastrax/date.html', {'entry_dates': entry_dates, 'maxcount': maxcount, 'maxplan': maxplan, 'dates_reg_list': dates_reg_list, 'dates_plan_list': dates_plan_list, 'dates_result_list': dates_result_list, 'dateyear': dateyear, 'datemo': datemo})

def year(request, year):
    dates_reg_list = SmokeRegister.objects.filter(
        Q(regdate__year=year)
        ).annotate(black=Sum('plan_sn__result_snid__acresburned')).order_by('sn')
    for object in dates_reg_list:
        if object.black == None:
            object.color = 'black'
        elif object.black < object.regacres:
            object.color = 'green'
        elif object.black >= object.regacres:
            object.color = 'red'
    dates_plan_list = SmokePlan.objects.filter(
        Q(plan_date__year=year)
        ).order_by('sn', 'suffix')
    dates_result_list = SmokeResult.objects.filter(
        Q(result_date__year=year)
        ).order_by('snid__sn', 'snid__suffix')
    dateyear = year
    intyear = int(year)
    first_month = datetime.datetime(intyear, 12, 31)
    previous_months = (first_month - relativedelta(months = months) for months in range(0, 12, 1))
    themonths = previous_months
    e=[]
    cumu = dates_reg_list.count()
    cump = dates_plan_list.count()
    cumr = dates_result_list.count()
    maxcount = 0
    maxplan = 0
    maxresult = 0
    for month in themonths:
        iyear = month.year
        imonth = month.month
        entry_count = SmokeRegister.objects.filter(
            Q(regdate__year=iyear),
            Q(regdate__month=imonth)
            ).count()
        if entry_count >= maxcount:
            maxcount = entry_count
        plan_count = SmokePlan.objects.filter(
            Q(plan_date__year=iyear),
            Q(plan_date__month=imonth)
            ).count()
        if plan_count >= maxplan:
            maxplan = plan_count
        result_count = SmokeResult.objects.filter(
            Q(result_date__year=iyear),
            Q(result_date__month=imonth)
            ).count()
        if result_count >= maxresult:
            maxresult = result_count
        dict = {'month': month, 'count': entry_count, 'cumu': cumu, 'countp': plan_count, 'cump': cump, 'countr': result_count, 'cumr': cumr }
        e.append(dict)
        cumu = cumu - entry_count
        cump = cump - plan_count
        cumr = cumr - result_count
        maxplan = max(maxplan,maxresult)
    entry_dates = e
    return render(request,'fastrax/date.html', {'entry_dates': entry_dates, 'maxcount': maxcount, 'maxplan': maxplan, 'dates_reg_list': dates_reg_list, 'dates_plan_list': dates_plan_list, 'dates_result_list': dates_result_list, 'dateyear': dateyear})

def yearproblems(request, year):
    dates_reg_list = SmokeRegister.objects.filter(
        Q(regdate__year=year)
        ).annotate(black=Sum('plan_sn__result_snid__acresburned')).order_by('sn')
    errors = 0
    offs = 0
    snxs = 0
    txxs = 0
    for object in dates_reg_list:
        if object.black == None:
            object.color = 'black'
        elif object.black < object.regacres:
            object.color = 'green'
        elif object.black >= object.regacres:
            object.color = 'red'
        try:
            snum = u"%s" % (object.sn)
            sin = int(snum)
            object.error = ''
        except:
            object.error = 'BAD SN'
        try:
            plss = PLSS.objects.get(
                Q(township=object.township.upper()),
                Q(range=object.range.upper()),
                Q(section=object.section.zfill(2))
                )
            object.y = plss.y
            object.x = plss.x
            sy = u"%s" % (object.y)
            sx = u"%s" % (object.x)
            oy = float(sy)
            ox = float(sx)
            pnt = geos.Point(ox, oy, srid=4326)
            try:
                odfpd = ODFPD.objects.filter(nnn='000').get(geometry__intersects=pnt)
                object.odfpd = odfpd.slug
            except ObjectDoesNotExist:
                object.odfpd = ''
                object.error = 'OFF PD'
        except:
            object.y = ''
            object.x = ''
            object.odfpd = ''
            object.error = 'BAD PLSS'
            if object.township[2] != '0' or object.range[2] != '0':
                object.error = 'NO FRACT'
            if object.township[3].upper() not in ['N','S'] or object.range[3].upper() not in ['E','W']:
                object.error = 'BAD DIRS'
            sect = int(object.section)
            if not 1 <= sect <= 36:
                object.error = 'BAD SECT'
        try:
            tons = object.landingtons + object.piletons + object.fuelclass1 + object.fuelclass2 + object.fuelclass3 + object.fuelclass4 + object.fuelclass5 + object.fuelclass6
            if tons == 0:
                object.error = '0-TON'
        except:
            pass
        if object.error == 'OFF PD':
            offs = offs + 1
        elif object.error == 'BAD SN':
            snxs = snxs + 1
        elif object.error == '0-TON':
            txxs = txxs + 1
        elif object.error != '':
            errors = errors + 1

    #dates_reg_list = dates_reg_list.exclude(error='')
    #dates_plan_list = SmokePlan.objects.filter(
    #    Q(plan_date__year=year)
    #    ).order_by('sn', 'suffix')
    #dates_result_list = SmokeResult.objects.filter(
    #    Q(result_date__year=year)
    #    ).order_by('snid__sn', 'snid__suffix')
    dateyear = year
    intyear = int(year)
    first_month = datetime.datetime(intyear, 12, 31)
    previous_months = (first_month - relativedelta(months = months) for months in range(0, 12, 1))
    themonths = previous_months
    e=[]
    cumu = dates_reg_list.count()
    #cump = dates_plan_list.count()
    #cumr = dates_result_list.count()
    maxcount = 0
    #maxplan = 0
    #maxresult = 0
    for month in themonths:
        iyear = month.year
        imonth = month.month
        entry_count = SmokeRegister.objects.filter(
            Q(regdate__year=iyear),
            Q(regdate__month=imonth)
            ).count()
        if entry_count >= maxcount:
            maxcount = entry_count
    #    plan_count = SmokePlan.objects.filter(
    #        Q(plan_date__year=iyear),
    #        Q(plan_date__month=imonth)
    #        ).count()
    #    if plan_count >= maxplan:
    #        maxplan = plan_count
    #    result_count = SmokeResult.objects.filter(
    #        Q(result_date__year=iyear),
    #        Q(result_date__month=imonth)
    #        ).count()
    #    if result_count >= maxresult:
    #        maxresult = result_count
        dict = {'month': month, 'count': entry_count, 'cumu': cumu }
        e.append(dict)
        cumu = cumu - entry_count
    #    cump = cump - plan_count
    #    cumr = cumr - result_count
    #    maxplan = max(maxplan,maxresult)
    entry_dates = e
    return render(request,'fastrax/dateproblems.html', {'entry_dates': entry_dates, 'maxcount': maxcount, 'dates_reg_list': dates_reg_list, 'dateyear': dateyear, 'errors': errors, 'offs': offs, 'snxs': snxs })

def yearoverage(request, year):
    dates_reg_list = SmokeRegister.objects.filter(
        Q(regdate__year=year)
        ).annotate(planned=Sum('plan_sn__acrestoburn')).annotate(black=Sum('plan_sn__result_snid__acresburned')).order_by('sn')
    errors = 0
    noplans = 0
    noig = 0
    under = 0
    tregcost = 0
    tplancost = 0
    ttotalcost = 0
    tover = 0
    trac = 0
    tplan = 0
    tblack = 0
    tunder = 0
    for object in dates_reg_list:
        if object.planned == None:
            object.regcost = object.regacres * 0.50
            object.plancost = 0
            object.over = object.regcost
            object.color = 'black'
            object.error = 'NO PLANS'
        elif object.black == None:
            object.regcost = object.regacres * 0.50
            object.plancost = 0
            object.over = object.regcost
            object.color = 'black'
            object.error = 'NO IGNITION'
        elif object.black < object.regacres:
            object.regcost = object.regacres * 0.50
            object.plancost = object.regacres * 3.10
            object.over = (object.regcost + object.plancost) - ((object.black * 0.50) + (object.black * 3.10))
            object.color = 'green'
            object.error = 'BLACK < REG'
        elif object.black >= object.regacres:
            object.regcost = 0
            object.plancost = object.regacres * 3.10
            object.over = (object.regcost + object.plancost) - ((object.black * 0.50) + (object.black * 3.10))
            object.color = 'red'
            object.error = ''
        if object.black != None:
            if object.black >= object.regacres:
                pass
            else:
                object.totalcost = object.regcost + object.plancost
                tregcost = tregcost + object.regcost
                tplancost = tplancost + object.plancost
                ttotalcost = ttotalcost + object.totalcost
                tover = tover + object.over
                trac = trac + object.regacres
                if object.black != None:
                    tblack = tblack + object.black
                    tunder = tunder + object.regacres - object.black
                else:
                    tunder = tunder + object.regacres
                if object.planned != None:
                    tplan = tplan + object.planned
        else:
            object.totalcost = object.regcost + object.plancost
            tregcost = tregcost + object.regcost
            tplancost = tplancost + object.plancost
            ttotalcost = ttotalcost + object.totalcost
            tover = tover + object.over
            trac = trac + object.regacres
            if object.black != None:
                tblack = tblack + object.black
                tunder = tunder + object.regacres - object.black
            else:
                tunder = tunder + object.regacres
            if object.planned != None:
                tplan = tplan + object.planned
        if object.error == 'NO PLANS':
            noplans = noplans + 1
        elif object.error == 'NO IGNITION':
            noig = noig + 1
        elif object.error == 'BLACK < REG':
            under = under + 1
        elif object.error != '':
            errors = errors + 1
    dateyear = year
    intyear = int(year)
    first_month = datetime.datetime(intyear, 12, 31)
    previous_months = (first_month - relativedelta(months = months) for months in range(0, 12, 1))
    themonths = previous_months
    e=[]
    cumu = dates_reg_list.count()
    maxcount = 0
    for month in themonths:
        iyear = month.year
        imonth = month.month
        entry_count = SmokeRegister.objects.filter(
            Q(regdate__year=iyear),
            Q(regdate__month=imonth)
            ).count()
        if entry_count >= maxcount:
            maxcount = entry_count
        dict = {'month': month, 'count': entry_count, 'cumu': cumu }
        e.append(dict)
        cumu = cumu - entry_count
    entry_dates = e
    return render(request,'fastrax/dateoverage.html', {'entry_dates': entry_dates, 'maxcount': maxcount, 'dates_reg_list': dates_reg_list, 'dateyear': dateyear, 'errors': errors, 'noplans': noplans, 'noig':  noig, 'under': under, 'tregcost': tregcost, 'tplancost': tplancost, 'ttotalcost': ttotalcost, 'tover': tover, 'trac': trac, 'tblack': tblack, 'tunder': tunder })

def yearbilling(request, year, tn):
    iyear = int(year)
    eyear = iyear-1
    adate = datetime.date(eyear, 10, 1)
    bdate = datetime.date(iyear, 9, 30)
    if tn == '':
        dates_reg_list = SmokeRegister.objects.filter(Q(regdate__range=(adate, bdate))|Q(plan_sn__result_snid__ignitiondated__range=(adate, bdate), plan_sn__result_snid__notaccomplished=False)).annotate(planned=Sum('plan_sn__acrestoburn'),lit=Min('plan_sn__result_snid__ignitiondated'),litacs=Sum('plan_sn__result_snid__acresburned')).filter(Q(regdate__range=(adate, bdate))|Q(lit__range=(adate, bdate))).order_by('district__tla','district__name') # charge regs
    elif tn == 'USFS':
        dates_reg_list = SmokeRegister.objects.filter(district__tin__startswith='F').filter(plan_sn__result_snid__notaccomplished=False).annotate(lit=Min('plan_sn__result_snid__ignitiondated')).filter(Q(regdate__range=(adate, bdate))|Q(lit__range=(adate, bdate))).order_by('district__tla','district__name') # charge regs
    elif tn == 'BLM':
        dates_reg_list = SmokeRegister.objects.filter(district__tin__startswith='B').filter(plan_sn__result_snid__notaccomplished=False).annotate(lit=Min('plan_sn__result_snid__ignitiondated')).filter(Q(regdate__range=(adate, bdate))|Q(lit__range=(adate, bdate))).order_by('district__tla','district__name') # charge regs
    else:
        dates_reg_list = SmokeRegister.objects.filter(district__tla__iexact=tn).filter(plan_sn__result_snid__notaccomplished=False).annotate(lit=Min('plan_sn__result_snid__ignitiondated')).filter(Q(regdate__range=(adate, bdate))|Q(lit__range=(adate, bdate))).order_by('district__tla','district__name') # charge regs
    #dates_result_list = SmokeResult.objects.filter(ignitiondated__range=(adate, bdate)).order_by('ignitiondated')
    #dates_lit_list = SmokeRegister.objects.filter(plan_sn__result_snid__ignitiondated__range=(adate, bdate), plan_sn__result_snid__notaccomplished=False).annotate(planned=Sum('plan_sn__acrestoburn'),lit=Min('plan_sn__result_snid__ignitiondated'),litacs=Sum('plan_sn__result_snid__acresburned')).filter(lit__range=(adate, bdate)).order_by('district')
    tregcost = 0
    tplancost = 0
    ttotalcost = 0
    trac = 0
    tplan = 0
    tblack = 0
    for object in dates_reg_list:
        if object.fuelspecies == 'J' or object.typeburn == 'S':
                object.regcost = 0
                object.plancost = 0
        else:
            if adate <= object.regdate <= bdate:
                object.regcost = object.regacres * 0.50
            else:
                object.regcost = 0
            if object.lit != None:
                if adate <= object.lit <= bdate:
                    object.plancost = object.regacres * 3.10
                else:
                    object.plancost = 0
            else:
                object.plancost = 0
        object.totalcost = object.regcost + object.plancost
        tregcost = tregcost + object.regcost
        tplancost = tplancost + object.plancost
        ttotalcost = ttotalcost + object.totalcost
        trac = trac + object.regacres
        #if object.litacs != None:
        #    tblack = tblack + object.litacs
        #if object.planned != None:
        #    tplan = tplan + object.planned
    dateyear = year
    intyear = int(year)
    first_month = datetime.datetime(intyear, 12, 31)
    previous_months = (first_month - relativedelta(months = months) for months in range(0, 12, 1))
    themonths = previous_months
    e=[]
    cumu = dates_reg_list.count()
    maxcount = 0
    for month in themonths:
        iyear = month.year
        imonth = month.month
        entry_count = SmokeRegister.objects.filter(
            Q(regdate__year=iyear),
            Q(regdate__month=imonth)
            ).count()
        if entry_count >= maxcount:
            maxcount = entry_count
        dict = {'month': month, 'count': entry_count, 'cumu': cumu }
        e.append(dict)
        cumu = cumu - entry_count
    entry_dates = e
    return render(request,'fastrax/datebilling.html', {'tla': tn, 'entry_dates': entry_dates, 'maxcount': maxcount, 'dates_reg_list': dates_reg_list, 'dateyear': dateyear, 'tregcost': tregcost, 'tplancost': tplancost, 'ttotalcost': ttotalcost, 'trac': trac, 'tblack': tblack })

def get_score(self):
    return sum(self.rating_set.values_list('rating', flat=True))

def monthsum(request, year, mo):
    iyear = int(year)
    imo = int(mo)
    dates_reg_list = SmokeRegister.objects.filter(
        Q(regdate__year=year),
        Q(regdate__month=mo)
        ).order_by('-regacres')
    dates_plan_list = SmokePlan.objects.filter(
        Q(ignitiondate__year=year),
        Q(ignitiondate__month=mo)
        ).order_by('ignitiondate')
    dates_result_list = SmokeResult.objects.filter(
        Q(ignitiondated__year=year),
        Q(ignitiondated__month=mo)
        ).order_by('ignitiondated')
    regcount = dates_reg_list.count()
    plancount = dates_plan_list.count()
    resultcount = dates_result_list.count()
    preacs = dates_reg_list.aggregate(Sum('regacres'))
    acscount = sum(preacs.values())
    preptons = dates_reg_list.aggregate(Sum('piletons'))
    ptonscount = sum(preptons.values())
    preltons = dates_reg_list.aggregate(Sum('landingtons'))
    ltonscount = sum(preltons.values())
    pretons = dates_reg_list.aggregate(Sum('fuelclass1'))
    tonscount = sum(pretons.values())
    ppreacs = dates_plan_list.aggregate(Sum('acrestoburn'))
    pacscount = sum(ppreacs.values())
    ppreptons = dates_plan_list.aggregate(Sum('piletons'))
    pptonscount = sum(ppreptons.values())
    ppreltons = dates_plan_list.aggregate(Sum('landingtons'))
    pltonscount = sum(ppreltons.values())
    ppretons = dates_plan_list.aggregate(Sum('b_u_tonsperacre'))
    ppretonscount = sum(ppretons.values())
    predistrict_list = District.objects.filter(Q(reg_district__regdate__year=iyear),Q(reg_district__regdate__month=imo)).annotate(regsmo=Count('reg_district'),acsmo=Sum('reg_district__regacres'),ptonsmo=Sum('reg_district__piletons'),ltonsmo=Sum('reg_district__landingtons'), tonsmo=Sum('reg_district__fuelclass1'))
    district_list = predistrict_list.exclude(regsmo='0').order_by('-regsmo')
    distcount = district_list.count()
    district2_list = predistrict_list.exclude(regsmo='0').order_by('-acsmo')
    district3_list = predistrict_list.exclude(regsmo='0').order_by('-tonsmo')
    preuser_list = User.objects.filter(Q(reg_user__regdate__year=iyear),Q(reg_user__regdate__month=imo)).annotate(regsmo=Count('reg_user'),acsmo=Sum('reg_user__regacres'),tonsmo=Sum('reg_user__fuelclass1'))
    user_list = preuser_list.exclude(regsmo='0').order_by('-regsmo')
    usercount = user_list.count()
    user2_list = preuser_list.exclude(regsmo='0').order_by('-acsmo')
    user3_list = preuser_list.exclude(regsmo='0').order_by('-tonsmo')
    ppldistrict_list = District.objects.filter(Q(reg_district__plan_sn__ignitiondate__year=iyear),Q(reg_district__plan_sn__ignitiondate__month=imo)).annotate(regsmo=Count('reg_district__plan_sn'),acsmo=Sum('reg_district__plan_sn__acrestoburn'),ptonsmo=Sum('reg_district__plan_sn__piletons'),ltonsmo=Sum('reg_district__plan_sn__landingtons'), tonsmo=Sum('reg_district__plan_sn__b_u_tonsperacre'))
    pdistrict_list = ppldistrict_list.exclude(regsmo='0').order_by('-regsmo')
    pdistcount = pdistrict_list.count()
    pdistrict2_list = ppldistrict_list.exclude(regsmo='0').order_by('-acsmo')
    pdistrict3_list = ppldistrict_list.exclude(regsmo='0').order_by('-tonsmo')
    rpreacs = dates_result_list.aggregate(Sum('acresburned'))
    racscount = sum(rpreacs.values())
    rpreptons = dates_result_list.aggregate(Sum('piletonned'))
    rptonscount = sum(rpreptons.values())
    rpreltons = dates_result_list.aggregate(Sum('landingtonned'))
    rltonscount = sum(rpreltons.values())
    rpretons = dates_result_list.aggregate(Sum('b_u_tonsperacred'))
    rtonscount = sum(rpretons.values())
    prsdistrict_list = District.objects.filter(Q(reg_district__plan_sn__result_snid__ignitiondated__year=iyear),Q(reg_district__plan_sn__result_snid__ignitiondated__month=imo)).annotate(regsmo=Count('reg_district__plan_sn__result_snid'),acsmo=Sum('reg_district__plan_sn__result_snid__acresburned'),ptonsmo=Sum('reg_district__plan_sn__result_snid__piletonned'),ltonsmo=Sum('reg_district__plan_sn__result_snid__landingtonned'), tonsmo=Sum('reg_district__plan_sn__result_snid__b_u_tonsperacred'))
    rdistrict_list = prsdistrict_list.exclude(regsmo='0').order_by('-regsmo')
    rdistcount = rdistrict_list.count()
    rdistrict2_list = rdistrict_list.exclude(regsmo='0').order_by('-acsmo')
    rdistrict3_list = rdistrict_list.exclude(regsmo='0').order_by('-tonsmo')
    ppluser_list = User.objects.filter(Q(reg_user__plan_sn__ignitiondate__year=iyear),Q(reg_user__plan_sn__ignitiondate__month=imo)).annotate(regsmo=Count('reg_user__plan_sn'),acsmo=Sum('reg_user__plan_sn__acrestoburn'),tonsmo=Sum('reg_user__plan_sn__b_u_tonsperacre'))
    puser_list = ppluser_list.exclude(regsmo='0').order_by('-regsmo')
    pusercount = puser_list.count()
    puser2_list = ppluser_list.exclude(regsmo='0').order_by('-acsmo')
    puser3_list = ppluser_list.exclude(regsmo='0').order_by('-tonsmo')
    dateyear = year
    datemo = mo
    return render(request,'fastrax/datesum.html', {'dateyear': dateyear, 'datemo': datemo, 'dates_reg_list': dates_reg_list, 'dates_plan_list': dates_plan_list, 'dates_result_list': dates_result_list, 'regcount': regcount, 'plancount': plancount, 'resultcount': resultcount, 'district_list': district_list, 'district2_list': district2_list, 'district3_list': district3_list, 'user_list': user_list, 'user2_list': user2_list, 'user3_list': user3_list, 'pdistrict_list': pdistrict_list, 'pdistrict2_list': pdistrict2_list, 'pdistrict3_list': pdistrict3_list, 'rdistrict_list': rdistrict_list, 'rdistrict2_list': rdistrict2_list, 'rdistrict3_list': rdistrict3_list, 'puser_list': puser_list, 'puser2_list': puser2_list, 'puser3_list': puser3_list, 'distcount': distcount, 'usercount': usercount, 'pdistcount': pdistcount, 'pusercount': pusercount, 'acscount': acscount, 'tonscount': tonscount, 'pacscount': pacscount, 'pptonscount': pptonscount, 'racscount': racscount, 'rptonscount': rptonscount, 'rltonscount': rltonscount, 'rtonscount': rtonscount })

def yearsum(request, year):
    iyear = int(year)
    dates_reg_list = SmokeRegister.objects.filter(
        Q(regdate__year=year)
        ).order_by('-regacres') # regs for year n
    dates_plan_list = SmokePlan.objects.filter(
        Q(ignitiondate__year=year)
        ).order_by('ignitiondate') # plans for year n
    dates_result_list = SmokeResult.objects.filter(
        Q(ignitiondated__year=year)
        ).order_by('ignitiondated') # results for year n
    dates_resulta_list = dates_result_list.exclude(
        Q(snid__sn__typeburn__in=['B', 'F', 'U', 'N']) # pile results for year n (type not BFUN)
        ).order_by('ignitiondated').annotate(ltons=Sum('landingtonned'), ptons=Sum('piletonned'))
    dates_resultb_list = dates_result_list.filter(
        Q(snid__sn__typeburn__in=['B', 'F', 'U', 'N']) # nonpile results for year n (type BFUN)
        ).order_by('ignitiondated').annotate(tons=Sum('b_u_tonsperacred')) # 
    regcount = dates_reg_list.count()
    plancount = dates_plan_list.count()
    resultcount = dates_result_list.count()
    resultacount = dates_resulta_list.count()
    resultbcount = dates_resultb_list.count()
    preacs = dates_reg_list.aggregate(Sum('regacres'))
    acscount = sum(preacs.values())
    preptons = dates_reg_list.aggregate(Sum('piletons'))
    ptonscount = sum(preptons.values())
    preltons = dates_reg_list.aggregate(Sum('landingtons'))
    ltonscount = sum(preltons.values())
    pretons = dates_reg_list.aggregate(Sum('fuelclass1'))
    tonscount = sum(pretons.values())
    ppreacs = dates_plan_list.aggregate(Sum('acrestoburn'))
    pacscount = sum(ppreacs.values())
    ppreptons = dates_plan_list.aggregate(Sum('piletons'))
    pptonscount = sum(ppreptons.values())
    ppreltons = dates_plan_list.aggregate(Sum('landingtons'))
    pltonscount = sum(ppreltons.values())
    ppretons = dates_plan_list.aggregate(Sum('b_u_tonsperacre'))
    ppretonscount = sum(ppretons.values())
    predistrict_list = District.objects.filter(Q(reg_district__regdate__year=iyear)).annotate(regsmo=Count('reg_district'),acsmo=Sum('reg_district__regacres'),ptonsmo=Sum('reg_district__piletons'),ltonsmo=Sum('reg_district__landingtons'), tonsmo=Sum('reg_district__fuelclass1'))
    district_list = predistrict_list.exclude(regsmo='0').order_by('-regsmo')
    distcount = district_list.count()
    district2_list = predistrict_list.exclude(regsmo='0').order_by('-acsmo')
    district3_list = predistrict_list.exclude(regsmo='0').order_by('-tonsmo')
    rpreacs = dates_result_list.aggregate(Sum('acresburned'))
    racscount = sum(rpreacs.values())
    rpreacsa = dates_resulta_list.aggregate(Sum('acresburned'))
    racscounta = sum(rpreacsa.values())
    rpreacsb = dates_resultb_list.aggregate(Sum('acresburned'))
    racscountb = sum(rpreacsb.values())
    rpreptons = dates_resulta_list.aggregate(Sum('piletonned'))
    rptonscount = sum(rpreptons.values())
    rpreltons = dates_resulta_list.aggregate(Sum('landingtonned'))
    rltonscount = sum(rpreltons.values())
    rpretons = dates_resultb_list.aggregate(Sum('b_u_tonsperacred'))
    rtonscount = sum(rpretons.values())
    prsdistrict_list = District.objects.filter(reg_district__plan_sn__result_snid__ignitiondated__year=iyear).annotate(regsmo=Count('reg_district__plan_sn__result_snid'), acsmo=Sum('reg_district__plan_sn__result_snid__acresburned'), ptonsmo=Sum('reg_district__plan_sn__result_snid__piletonned'), ltonsmo=Sum('reg_district__plan_sn__result_snid__landingtonned'))
    rdistrict_list = prsdistrict_list.exclude(regsmo='0').order_by('-regsmo')
    rdistcount = rdistrict_list.count()
    rdistrict2_list = rdistrict_list.exclude(regsmo='0').order_by('-acsmo')
    rdistrict3_list = rdistrict_list.exclude(regsmo='0').order_by('-tonsmo')
    preuser_list = User.objects.filter(Q(reg_user__regdate__year=iyear)).annotate(regsmo=Count('reg_user'),acsmo=Sum('reg_user__regacres'),tonsmo=Sum('reg_user__fuelclass1'))
    user_list = preuser_list.exclude(regsmo='0').order_by('-regsmo')
    usercount = user_list.count()
    user2_list = preuser_list.exclude(regsmo='0').order_by('-acsmo')
    user3_list = preuser_list.exclude(regsmo='0').order_by('-tonsmo')
    ppldistrict_list = District.objects.filter(Q(reg_district__plan_sn__ignitiondate__year=iyear)).annotate(regsmo=Count('reg_district__plan_sn'),acsmo=Sum('reg_district__plan_sn__acrestoburn'),ptonsmo=Sum('reg_district__plan_sn__piletons'),ltonsmo=Sum('reg_district__plan_sn__landingtons'), tonsmo=Sum('reg_district__plan_sn__b_u_tonsperacre'))
    pdistrict_list = ppldistrict_list.exclude(regsmo='0').order_by('-regsmo')
    pdistcount = pdistrict_list.count()
    pdistrict2_list = ppldistrict_list.exclude(regsmo='0').order_by('-acsmo')
    pdistrict3_list = ppldistrict_list.exclude(regsmo='0').order_by('-tonsmo')
    ppluser_list = User.objects.filter(Q(reg_user__plan_sn__ignitiondate__year=iyear)).annotate(regsmo=Count('reg_user__plan_sn'),acsmo=Sum('reg_user__plan_sn__acrestoburn'),tonsmo=Sum('reg_user__plan_sn__b_u_tonsperacre'))
    puser_list = ppluser_list.exclude(regsmo='0').order_by('-regsmo')
    pusercount = puser_list.count()
    puser2_list = ppluser_list.exclude(regsmo='0').order_by('-acsmo')
    puser3_list = ppluser_list.exclude(regsmo='0').order_by('-tonsmo')
    dateyear = year
    return render(request,'fastrax/datesum.html', {'dateyear': dateyear, 'dates_reg_list': dates_reg_list, 'dates_plan_list': dates_plan_list, 'dates_result_list': dates_result_list, 'regcount': regcount, 'plancount': plancount, 'resultcount': resultcount, 'resultacount': resultacount, 'resultbcount': resultbcount, 'district_list': district_list, 'district2_list': district2_list, 'district3_list': district3_list, 'user_list': user_list, 'user2_list': user2_list, 'user3_list': user3_list, 'pdistrict_list': pdistrict_list, 'pdistrict2_list': pdistrict2_list, 'pdistrict3_list': pdistrict3_list, 'rdistrict_list': rdistrict_list, 'rdistrict2_list': rdistrict2_list, 'rdistrict3_list': rdistrict3_list, 'puser_list': puser_list, 'puser2_list': puser2_list, 'puser3_list': puser3_list, 'distcount': distcount, 'usercount': usercount, 'pdistcount': pdistcount, 'pusercount': pusercount, 'acscount': acscount, 'tonscount': tonscount, 'pacscount': pacscount, 'pptonscount': pptonscount, 'racscount': racscount, 'racscounta': racscounta, 'racscountb': racscountb, 'rptonscount': rptonscount, 'rltonscount': rltonscount, 'rtonscount': rtonscount })

def monthaccomp(request, year, mo):
    iyear = int(year)
    imo = int(mo)
    dates_reg_list = SmokeRegister.objects.filter(
        Q(regdate__year=year),
        Q(regdate__month=mo)
        ).order_by('-regacres')
    dates_plan_list = SmokePlan.objects.filter(
        Q(ignitiondate__year=year),
        Q(ignitiondate__month=mo)
        ).order_by('ignitiondate')
    dates_result_list = SmokeResult.objects.filter(
        Q(ignitiondated__year=year),
        Q(ignitiondated__month=mo)
        ).order_by('snid__sn__district','snid__sn')
    regcount = dates_reg_list.count()
    plancount = dates_plan_list.count()
    resultcount = dates_result_list.count()
    preacs = dates_reg_list.aggregate(Sum('regacres'))
    acscount = sum(filter(None,(preacs.values())))
    preptons = dates_reg_list.aggregate(Sum('piletons'))
    ptonscount = sum(filter(None,(preptons.values())))
    preltons = dates_reg_list.aggregate(Sum('landingtons'))
    ltonscount = sum(filter(None,(preltons.values())))
    pretons = dates_reg_list.aggregate(Sum('fuelclass1'))
    tonscount = sum(filter(None,(pretons.values())))
    ppreacs = dates_plan_list.aggregate(Sum('acrestoburn'))
    pacscount = sum(filter(None,(ppreacs.values())))
    ppreptons = dates_plan_list.aggregate(Sum('piletons'))
    pptonscount = sum(filter(None,(ppreptons.values())))
    ppreltons = dates_plan_list.aggregate(Sum('landingtons'))
    pltonscount = sum(filter(None,(ppreltons.values())))
    ppretons = dates_plan_list.aggregate(Sum('b_u_tonsperacre'))
    ptonscount = sum(filter(None,(ppretons.values())))
    rpreacs = dates_result_list.aggregate(Sum('acresburned'))
    racscount = sum(filter(None,(rpreacs.values())))
    rpreptons = dates_result_list.aggregate(Sum('piletonned'))
    rptonscount = sum(filter(None,(rpreptons.values())))
    rpreltons = dates_result_list.aggregate(Sum('landingtonned'))
    rltonscount = sum(filter(None,(rpreltons.values())))
    rpretons = dates_result_list.aggregate(Sum('b_u_tonsperacred'))
    rtonscount = sum(filter(None,(rpretons.values())))
    predistrict_list = District.objects.filter(Q(reg_district__regdate__year=iyear),Q(reg_district__regdate__month=imo)).annotate(regsmo=Count('reg_district'),acsmo=Sum('reg_district__regacres'),ptonsmo=Sum('reg_district__piletons'),ltonsmo=Sum('reg_district__landingtons'), tonsmo=Sum('reg_district__fuelclass1'))
    district_list = predistrict_list.exclude(regsmo='0').order_by('-regsmo')
    distcount = district_list.count()
    district2_list = predistrict_list.exclude(regsmo='0').order_by('-acsmo')
    district3_list = predistrict_list.exclude(regsmo='0').order_by('-tonsmo')
    preuser_list = User.objects.filter(Q(reg_user__regdate__year=iyear),Q(reg_user__regdate__month=imo)).annotate(regsmo=Count('reg_user'),acsmo=Sum('reg_user__regacres'),tonsmo=Sum('reg_user__fuelclass1'))
    user_list = preuser_list.exclude(regsmo='0').order_by('-regsmo')
    usercount = user_list.count()
    user2_list = preuser_list.exclude(regsmo='0').order_by('-acsmo')
    user3_list = preuser_list.exclude(regsmo='0').order_by('-tonsmo')
    ppldistrict_list = District.objects.filter(Q(reg_district__plan_sn__ignitiondate__year=iyear),Q(reg_district__plan_sn__ignitiondate__month=imo)).annotate(regsmo=Count('reg_district__plan_sn'),acsmo=Sum('reg_district__plan_sn__acrestoburn'),ptonsmo=Sum('reg_district__plan_sn__piletons'),ltonsmo=Sum('reg_district__plan_sn__landingtons'), tonsmo=Sum('reg_district__plan_sn__b_u_tonsperacre'))
    pdistrict_list = ppldistrict_list.exclude(regsmo='0').order_by('-regsmo')
    pdistcount = pdistrict_list.count()
    pdistrict2_list = ppldistrict_list.exclude(regsmo='0').order_by('-acsmo')
    pdistrict3_list = ppldistrict_list.exclude(regsmo='0').order_by('-tonsmo')
    ppluser_list = User.objects.filter(Q(reg_user__plan_sn__ignitiondate__year=iyear),Q(reg_user__plan_sn__ignitiondate__month=imo)).annotate(regsmo=Count('reg_user__plan_sn'),acsmo=Sum('reg_user__plan_sn__acrestoburn'),tonsmo=Sum('reg_user__plan_sn__b_u_tonsperacre'))
    puser_list = ppluser_list.exclude(regsmo='0').order_by('-regsmo')
    pusercount = puser_list.count()
    puser2_list = ppluser_list.exclude(regsmo='0').order_by('-acsmo')
    puser3_list = ppluser_list.exclude(regsmo='0').order_by('-tonsmo')
    rrldistrict_list = District.objects.filter(Q(reg_district__plan_sn__result_snid__ignitiondated__year=iyear),Q(reg_district__plan_sn__result_snid__ignitiondated__month=imo)).annotate(regsmo=Count('reg_district__plan_sn__result_snid'),acsmo=Sum('reg_district__plan_sn__result_snid__acresburned'),ptonsmo=Sum('reg_district__plan_sn__result_snid__piletonned'),ltonsmo=Sum('reg_district__plan_sn__result_snid__landingtonned'), tonsmo=Sum('reg_district__plan_sn__result_snid__b_u_tonsperacred'))
    rdistrict_list = rrldistrict_list.exclude(regsmo='0').order_by('-regsmo')
    rdistcount = rdistrict_list.count()
    rdistrict2_list = rrldistrict_list.exclude(regsmo='0').order_by('-acsmo')
    rdistrict3_list = rrldistrict_list.exclude(regsmo='0').order_by('-tonsmo')
    pruser_list = User.objects.filter(Q(reg_user__plan_sn__result_snid__ignitiondated__year=iyear),Q(reg_user__plan_sn__result_snid__ignitiondated__month=imo)).annotate(regsmo=Count('reg_user__plan_sn__result_snid'),acsmo=Sum('reg_user__plan_sn__result_snid__acresburned'),tonsmo=Sum('reg_user__plan_sn__result_snid__b_u_tonsperacred'))
    ruser_list = pruser_list.exclude(regsmo='0').order_by('-regsmo')
    rusercount = ruser_list.count()
    ruser2_list = pruser_list.exclude(regsmo='0').order_by('-acsmo')
    ruser3_list = pruser_list.exclude(regsmo='0').order_by('-tonsmo')
    dateyear = year
    datemo = mo
    return render(request,'fastrax/dateaccomp.html', {'dateyear': dateyear, 'datemo': datemo, 'dates_reg_list': dates_reg_list, 'dates_plan_list': dates_plan_list, 'dates_result_list': dates_result_list, 'regcount': regcount, 'plancount': plancount, 'resultcount': resultcount, 'district_list': district_list, 'district2_list': district2_list, 'district3_list': district3_list, 'user_list': user_list, 'user2_list': user2_list, 'user3_list': user3_list, 'pdistrict_list': pdistrict_list, 'pdistrict2_list': pdistrict2_list, 'pdistrict3_list': pdistrict3_list, 'puser_list': puser_list, 'puser2_list': puser2_list, 'puser3_list': puser3_list, 'rdistrict_list': rdistrict_list, 'rdistrict2_list': rdistrict2_list, 'rdistrict3_list': rdistrict3_list, 'ruser_list': ruser_list, 'ruser2_list': ruser2_list, 'ruser3_list': ruser3_list, 'distcount': distcount, 'usercount': usercount, 'pdistcount': pdistcount, 'pusercount': pusercount, 'rdistcount': rdistcount, 'rusercount': rusercount, 'acscount': acscount, 'tonscount': tonscount, 'pacscount': pacscount, 'ptonscount': ptonscount, 'pptonscount': pptonscount, 'racscount': racscount, 'rtonscount': rtonscount, 'rptonscount': rptonscount })

def monthaccompt(request, year, mo):
    iyear = int(year)
    imo = int(mo)
    dates_reg_list = SmokeRegister.objects.filter(
        Q(regdate__year=year),
        Q(regdate__month=mo)
        ).order_by('-regacres')
    dates_plan_list = SmokePlan.objects.filter(
        Q(ignitiondate__year=year),
        Q(ignitiondate__month=mo)
        ).order_by('ignitiondate')
    dates_result_list = SmokeResult.objects.filter(
        Q(ignitiondated__year=year),
        Q(ignitiondated__month=mo)
        ).order_by('ignitiondated')
    regcount = dates_reg_list.count()
    plancount = dates_plan_list.count()
    resultcount = dates_result_list.count()
    preacs = dates_reg_list.aggregate(Sum('regacres'))
    acscount = sum(filter(None,(preacs.values())))
    preptons = dates_reg_list.aggregate(Sum('piletons'))
    ptonscount = sum(filter(None,(preptons.values())))
    preltons = dates_reg_list.aggregate(Sum('landingtons'))
    ltonscount = sum(filter(None,(preltons.values())))
    pretons = dates_reg_list.aggregate(Sum('fuelclass1'))
    tonscount = sum(filter(None,(pretons.values())))
    ppreacs = dates_plan_list.aggregate(Sum('acrestoburn'))
    pacscount = sum(filter(None,(ppreacs.values())))
    ppreptons = dates_plan_list.aggregate(Sum('piletons'))
    pptonscount = sum(filter(None,(ppreptons.values())))
    ppreltons = dates_plan_list.aggregate(Sum('landingtons'))
    pltonscount = sum(filter(None,(ppreltons.values())))
    ppretons = dates_plan_list.aggregate(Sum('b_u_tonsperacre'))
    ptonscount = sum(filter(None,(ppretons.values())))
    rpreacs = dates_result_list.aggregate(Sum('acresburned'))
    racscount = sum(filter(None,(rpreacs.values())))
    rpreptons = dates_result_list.aggregate(Sum('piletonned'))
    rptonscount = sum(filter(None,(rpreptons.values())))
    rpreltons = dates_result_list.aggregate(Sum('landingtonned'))
    rltonscount = sum(filter(None,(rpreltons.values())))
    rpretons = dates_result_list.aggregate(Sum('b_u_tonsperacred'))
    rtonscount = sum(filter(None,(rpretons.values())))
    predistrict_list = District.objects.filter(Q(reg_district__regdate__year=iyear),Q(reg_district__regdate__month=imo)).annotate(regsmo=Count('reg_district'),acsmo=Sum('reg_district__regacres'),ptonsmo=Sum('reg_district__piletons'),ltonsmo=Sum('reg_district__landingtons'), tonsmo=Sum('reg_district__fuelclass1'))
    district_list = predistrict_list.exclude(regsmo='0').order_by('-regsmo')
    distcount = district_list.count()
    district2_list = predistrict_list.exclude(regsmo='0').order_by('-acsmo')
    district3_list = predistrict_list.exclude(regsmo='0').order_by('-tonsmo')
    preuser_list = User.objects.filter(Q(reg_user__regdate__year=iyear),Q(reg_user__regdate__month=imo)).annotate(regsmo=Count('reg_user'),acsmo=Sum('reg_user__regacres'),tonsmo=Sum('reg_user__fuelclass1'))
    user_list = preuser_list.exclude(regsmo='0').order_by('-regsmo')
    usercount = user_list.count()
    user2_list = preuser_list.exclude(regsmo='0').order_by('-acsmo')
    user3_list = preuser_list.exclude(regsmo='0').order_by('-tonsmo')
    ppldistrict_list = District.objects.filter(Q(reg_district__plan_sn__ignitiondate__year=iyear),Q(reg_district__plan_sn__ignitiondate__month=imo)).annotate(regsmo=Count('reg_district__plan_sn'),acsmo=Sum('reg_district__plan_sn__acrestoburn'),ptonsmo=Sum('reg_district__plan_sn__piletons'),ltonsmo=Sum('reg_district__plan_sn__landingtons'), tonsmo=Sum('reg_district__plan_sn__b_u_tonsperacre'))
    pdistrict_list = ppldistrict_list.exclude(regsmo='0').order_by('-regsmo')
    pdistcount = pdistrict_list.count()
    pdistrict2_list = ppldistrict_list.exclude(regsmo='0').order_by('-acsmo')
    pdistrict3_list = ppldistrict_list.exclude(regsmo='0').order_by('-tonsmo')
    ppluser_list = User.objects.filter(Q(reg_user__plan_sn__ignitiondate__year=iyear),Q(reg_user__plan_sn__ignitiondate__month=imo)).annotate(regsmo=Count('reg_user__plan_sn'),acsmo=Sum('reg_user__plan_sn__acrestoburn'),tonsmo=Sum('reg_user__plan_sn__b_u_tonsperacre'))
    puser_list = ppluser_list.exclude(regsmo='0').order_by('-regsmo')
    pusercount = puser_list.count()
    puser2_list = ppluser_list.exclude(regsmo='0').order_by('-acsmo')
    puser3_list = ppluser_list.exclude(regsmo='0').order_by('-tonsmo')
    rrldistrict_list = District.objects.filter(Q(reg_district__plan_sn__result_snid__ignitiondated__year=iyear),Q(reg_district__plan_sn__result_snid__ignitiondated__month=imo)).annotate(regsmo=Count('reg_district__plan_sn__result_snid'),acsmo=Sum('reg_district__plan_sn__result_snid__acresburned'),ptonsmo=Sum('reg_district__plan_sn__result_snid__piletonned'),ltonsmo=Sum('reg_district__plan_sn__result_snid__landingtonned'), tonsmo=Sum('reg_district__plan_sn__result_snid__b_u_tonsperacred'))
    rdistrict_list = rrldistrict_list.exclude(regsmo='0').order_by('-regsmo')
    rdistcount = rdistrict_list.count()
    rdistrict2_list = rrldistrict_list.exclude(regsmo='0').order_by('-acsmo')
    rdistrict3_list = rrldistrict_list.exclude(regsmo='0').order_by('-tonsmo')
    pruser_list = User.objects.filter(Q(reg_user__plan_sn__result_snid__ignitiondated__year=iyear),Q(reg_user__plan_sn__result_snid__ignitiondated__month=imo)).annotate(regsmo=Count('reg_user__plan_sn__result_snid'),acsmo=Sum('reg_user__plan_sn__result_snid__acresburned'),tonsmo=Sum('reg_user__plan_sn__result_snid__b_u_tonsperacred'))
    ruser_list = pruser_list.exclude(regsmo='0').order_by('-regsmo')
    rusercount = ruser_list.count()
    ruser2_list = pruser_list.exclude(regsmo='0').order_by('-acsmo')
    ruser3_list = pruser_list.exclude(regsmo='0').order_by('-tonsmo')
    dateyear = year
    datemo = mo
    result = render(request,'fastrax/dateaccompt.csv', {'dateyear': dateyear, 'datemo': datemo, 'dates_reg_list': dates_reg_list, 'dates_plan_list': dates_plan_list, 'dates_result_list': dates_result_list, 'regcount': regcount, 'plancount': plancount, 'resultcount': resultcount, 'district_list': district_list, 'district2_list': district2_list, 'district3_list': district3_list, 'user_list': user_list, 'user2_list': user2_list, 'user3_list': user3_list, 'pdistrict_list': pdistrict_list, 'pdistrict2_list': pdistrict2_list, 'pdistrict3_list': pdistrict3_list, 'puser_list': puser_list, 'puser2_list': puser2_list, 'puser3_list': puser3_list, 'rdistrict_list': rdistrict_list, 'rdistrict2_list': rdistrict2_list, 'rdistrict3_list': rdistrict3_list, 'ruser_list': ruser_list, 'ruser2_list': ruser2_list, 'ruser3_list': ruser3_list, 'distcount': distcount, 'usercount': usercount, 'pdistcount': pdistcount, 'pusercount': pusercount, 'rdistcount': rdistcount, 'rusercount': rusercount, 'acscount': acscount, 'tonscount': tonscount, 'pacscount': pacscount, 'ptonscount': ptonscount, 'pptonscount': pptonscount, 'racscount': racscount, 'rtonscount': rtonscount, 'rptonscount': rptonscount })
    return HttpResponse(result, content_type='text/plain')

def fiscalaccomp(request, year):
    iyear = int(year)
    eyear = iyear-1
    adate = datetime.date(eyear, 10, 1)
    bdate = datetime.date(iyear, 9, 30)
    dates_reg_list = SmokeRegister.objects.filter(regdate__range=(adate, bdate)).order_by('-regacres')
    dates_plan_list = SmokePlan.objects.filter(ignitiondate__range=(adate, bdate)).order_by('ignitiondate')
    dates_result_list = SmokeResult.objects.filter(ignitiondated__range=(adate, bdate)).order_by('ignitiondated')
    dates_lit_list = SmokeRegister.objects.filter(plan_sn__result_snid__ignitiondated__range=(adate, bdate), plan_sn__result_snid__notaccomplished=False).annotate(lit=Min('plan_sn__result_snid__ignitiondated'),litacs=Sum('plan_sn__result_snid__acresburned')).filter(lit__range=(adate, bdate)).order_by('-lit')
    regcount = dates_reg_list.count()
    plancount = dates_plan_list.count()
    resultcount = dates_result_list.count()
    preacs = dates_reg_list.aggregate(Sum('regacres'))
    acscount = sum(filter(None,(preacs.values())))
    preptons = dates_reg_list.aggregate(Sum('piletons'))
    ptonscount = sum(filter(None,(preptons.values())))
    preltons = dates_reg_list.aggregate(Sum('landingtons'))
    ltonscount = sum(filter(None,(preltons.values())))
    pretons = dates_reg_list.aggregate(Sum('fuelclass1'))
    tonscount = sum(filter(None,(pretons.values())))
    ppreacs = dates_plan_list.aggregate(Sum('acrestoburn'))
    pacscount = sum(filter(None,(ppreacs.values())))
    ppreptons = dates_plan_list.aggregate(Sum('piletons'))
    pptonscount = sum(filter(None,(ppreptons.values())))
    ppreltons = dates_plan_list.aggregate(Sum('landingtons'))
    pltonscount = sum(filter(None,(ppreltons.values())))
    ppretons = dates_plan_list.aggregate(Sum('b_u_tonsperacre'))
    ptonscount = sum(filter(None,(ppretons.values())))
    rpreacs = dates_result_list.aggregate(Sum('acresburned'))
    racscount = sum(filter(None,(rpreacs.values())))
    rpreptons = dates_result_list.aggregate(Sum('piletonned'))
    rptonscount = sum(filter(None,(rpreptons.values())))
    rpreltons = dates_result_list.aggregate(Sum('landingtonned'))
    rltonscount = sum(filter(None,(rpreltons.values())))
    rpretons = dates_result_list.aggregate(Sum('b_u_tonsperacred'))
    rtonscount = sum(filter(None,(rpretons.values())))
    predistrict_list = District.objects.filter(reg_district__regdate__range=(adate, bdate)).annotate(regsmo=Count('reg_district'),acsmo=Sum('reg_district__regacres'),ptonsmo=Sum('reg_district__piletons'),ltonsmo=Sum('reg_district__landingtons'), tonsmo=Sum('reg_district__fuelclass1'))
    district_list = predistrict_list.exclude(regsmo='0').order_by('-regsmo')
    distcount = district_list.count()
    district2_list = predistrict_list.exclude(regsmo='0').order_by('-acsmo')
    district3_list = predistrict_list.exclude(regsmo='0').order_by('-tonsmo')
    preuser_list = User.objects.filter(reg_user__regdate__range=(adate, bdate)).annotate(regsmo=Count('reg_user'),acsmo=Sum('reg_user__regacres'),tonsmo=Sum('reg_user__fuelclass1'))
    user_list = preuser_list.exclude(regsmo='0').order_by('-regsmo')
    usercount = user_list.count()
    user2_list = preuser_list.exclude(regsmo='0').order_by('-acsmo')
    user3_list = preuser_list.exclude(regsmo='0').order_by('-tonsmo')
    ppldistrict_list = District.objects.filter(reg_district__plan_sn__ignitiondate__range=(adate, bdate)).annotate(regsmo=Count('reg_district__plan_sn'),acsmo=Sum('reg_district__plan_sn__acrestoburn'),ptonsmo=Sum('reg_district__plan_sn__piletons'),ltonsmo=Sum('reg_district__plan_sn__landingtons'), tonsmo=Sum('reg_district__plan_sn__b_u_tonsperacre'))
    pdistrict_list = ppldistrict_list.exclude(regsmo='0').order_by('-regsmo')
    pdistcount = pdistrict_list.count()
    pdistrict2_list = ppldistrict_list.exclude(regsmo='0').order_by('-acsmo')
    pdistrict3_list = ppldistrict_list.exclude(regsmo='0').order_by('-tonsmo')
    ppluser_list = User.objects.filter(reg_user__plan_sn__ignitiondate__range=(adate, bdate)).annotate(regsmo=Count('reg_user__plan_sn'),acsmo=Sum('reg_user__plan_sn__acrestoburn'),tonsmo=Sum('reg_user__plan_sn__b_u_tonsperacre'))
    puser_list = ppluser_list.exclude(regsmo='0').order_by('-regsmo')
    pusercount = puser_list.count()
    puser2_list = ppluser_list.exclude(regsmo='0').order_by('-acsmo')
    puser3_list = ppluser_list.exclude(regsmo='0').order_by('-tonsmo')
    rrldistrict_list = District.objects.filter(reg_district__plan_sn__result_snid__ignitiondated__range=(adate, bdate)).annotate(regsmo=Count('reg_district__plan_sn__result_snid'),acsmo=Sum('reg_district__plan_sn__result_snid__acresburned'),ptonsmo=Sum('reg_district__plan_sn__result_snid__piletonned'),ltonsmo=Sum('reg_district__plan_sn__result_snid__landingtonned'), tonsmo=Sum('reg_district__plan_sn__result_snid__b_u_tonsperacred'))
    rdistrict_list = rrldistrict_list.exclude(regsmo='0').order_by('-regsmo')
    rdistcount = rdistrict_list.count()
    rdistrict2_list = rrldistrict_list.exclude(regsmo='0').order_by('-acsmo')
    rdistrict3_list = rrldistrict_list.exclude(regsmo='0').order_by('-tonsmo')
    pruser_list = User.objects.filter(reg_user__plan_sn__result_snid__ignitiondated__range=(adate, bdate)).annotate(regsmo=Count('reg_user__plan_sn__result_snid'),acsmo=Sum('reg_user__plan_sn__result_snid__acresburned'),tonsmo=Sum('reg_user__plan_sn__result_snid__b_u_tonsperacred'))
    ruser_list = pruser_list.exclude(regsmo='0').order_by('-regsmo')
    rusercount = ruser_list.count()
    ruser2_list = pruser_list.exclude(regsmo='0').order_by('-acsmo')
    ruser3_list = pruser_list.exclude(regsmo='0').order_by('-tonsmo')
    dateyear = year
    return render(request,'fastrax/dateaccomp.html', {'dateyear': dateyear, 'dates_reg_list': dates_reg_list, 'dates_plan_list': dates_plan_list, 'dates_result_list': dates_result_list, 'dates_lit_list': dates_lit_list, 'regcount': regcount, 'plancount': plancount, 'resultcount': resultcount, 'district_list': district_list, 'district2_list': district2_list, 'district3_list': district3_list, 'user_list': user_list, 'user2_list': user2_list, 'user3_list': user3_list, 'pdistrict_list': pdistrict_list, 'pdistrict2_list': pdistrict2_list, 'pdistrict3_list': pdistrict3_list, 'puser_list': puser_list, 'puser2_list': puser2_list, 'puser3_list': puser3_list, 'rdistrict_list': rdistrict_list, 'rdistrict2_list': rdistrict2_list, 'rdistrict3_list': rdistrict3_list, 'ruser_list': ruser_list, 'ruser2_list': ruser2_list, 'ruser3_list': ruser3_list, 'distcount': distcount, 'usercount': usercount, 'pdistcount': pdistcount, 'pusercount': pusercount, 'rdistcount': rdistcount, 'rusercount': rusercount, 'acscount': acscount, 'tonscount': tonscount, 'pacscount': pacscount, 'ptonscount': ptonscount, 'pptonscount': pptonscount, 'racscount': racscount, 'rtonscount': rtonscount, 'rptonscount': rptonscount })

def fiscalaccompt(request, year):
    iyear = int(year)
    eyear = iyear-1
    adate = datetime.date(eyear, 10, 1)
    bdate = datetime.date(iyear, 9, 30)
    dates_reg_list = SmokeRegister.objects.filter(regdate__range=(adate, bdate)).order_by('-regacres')
    dates_plan_list = SmokePlan.objects.filter(ignitiondate__range=(adate, bdate)).order_by('ignitiondate')
    dates_result_list = SmokeResult.objects.filter(ignitiondated__range=(adate, bdate)).order_by('ignitiondated')
    dates_lit_list = SmokeRegister.objects.filter(plan_sn__result_snid__ignitiondated__range=(adate, bdate), plan_sn__result_snid__notaccomplished=False).annotate(lit=Min('plan_sn__result_snid__ignitiondated'),litacs=Sum('plan_sn__result_snid__acresburned')).filter(lit__range=(adate, bdate)).order_by('-lit')
    regcount = dates_reg_list.count()
    plancount = dates_plan_list.count()
    resultcount = dates_result_list.count()
    preacs = dates_reg_list.aggregate(Sum('regacres'))
    acscount = sum(filter(None,(preacs.values())))
    preptons = dates_reg_list.aggregate(Sum('piletons'))
    ptonscount = sum(filter(None,(preptons.values())))
    preltons = dates_reg_list.aggregate(Sum('landingtons'))
    ltonscount = sum(filter(None,(preltons.values())))
    pretons = dates_reg_list.aggregate(Sum('fuelclass1'))
    tonscount = sum(filter(None,(pretons.values())))
    ppreacs = dates_plan_list.aggregate(Sum('acrestoburn'))
    pacscount = sum(filter(None,(ppreacs.values())))
    ppreptons = dates_plan_list.aggregate(Sum('piletons'))
    pptonscount = sum(filter(None,(ppreptons.values())))
    ppreltons = dates_plan_list.aggregate(Sum('landingtons'))
    pltonscount = sum(filter(None,(ppreltons.values())))
    ppretons = dates_plan_list.aggregate(Sum('b_u_tonsperacre'))
    ptonscount = sum(filter(None,(ppretons.values())))
    rpreacs = dates_result_list.aggregate(Sum('acresburned'))
    racscount = sum(filter(None,(rpreacs.values())))
    rpreptons = dates_result_list.aggregate(Sum('piletonned'))
    rptonscount = sum(filter(None,(rpreptons.values())))
    rpreltons = dates_result_list.aggregate(Sum('landingtonned'))
    rltonscount = sum(filter(None,(rpreltons.values())))
    rpretons = dates_result_list.aggregate(Sum('b_u_tonsperacred'))
    rtonscount = sum(filter(None,(rpretons.values())))
    predistrict_list = District.objects.filter(reg_district__regdate__range=(adate, bdate)).annotate(regsmo=Count('reg_district'),acsmo=Sum('reg_district__regacres'),ptonsmo=Sum('reg_district__piletons'),ltonsmo=Sum('reg_district__landingtons'), tonsmo=Sum('reg_district__fuelclass1'))
    district_list = predistrict_list.exclude(regsmo='0').order_by('-regsmo')
    distcount = district_list.count()
    district2_list = predistrict_list.exclude(regsmo='0').order_by('-acsmo')
    district3_list = predistrict_list.exclude(regsmo='0').order_by('-tonsmo')
    preuser_list = User.objects.filter(reg_user__regdate__range=(adate, bdate)).annotate(regsmo=Count('reg_user'),acsmo=Sum('reg_user__regacres'),tonsmo=Sum('reg_user__fuelclass1'))
    user_list = preuser_list.exclude(regsmo='0').order_by('-regsmo')
    usercount = user_list.count()
    user2_list = preuser_list.exclude(regsmo='0').order_by('-acsmo')
    user3_list = preuser_list.exclude(regsmo='0').order_by('-tonsmo')
    ppldistrict_list = District.objects.filter(reg_district__plan_sn__ignitiondate__range=(adate, bdate)).annotate(regsmo=Count('reg_district__plan_sn'),acsmo=Sum('reg_district__plan_sn__acrestoburn'),ptonsmo=Sum('reg_district__plan_sn__piletons'),ltonsmo=Sum('reg_district__plan_sn__landingtons'), tonsmo=Sum('reg_district__plan_sn__b_u_tonsperacre'))
    pdistrict_list = ppldistrict_list.exclude(regsmo='0').order_by('-regsmo')
    pdistcount = pdistrict_list.count()
    pdistrict2_list = ppldistrict_list.exclude(regsmo='0').order_by('-acsmo')
    pdistrict3_list = ppldistrict_list.exclude(regsmo='0').order_by('-tonsmo')
    ppluser_list = User.objects.filter(reg_user__plan_sn__ignitiondate__range=(adate, bdate)).annotate(regsmo=Count('reg_user__plan_sn'),acsmo=Sum('reg_user__plan_sn__acrestoburn'),tonsmo=Sum('reg_user__plan_sn__b_u_tonsperacre'))
    puser_list = ppluser_list.exclude(regsmo='0').order_by('-regsmo')
    pusercount = puser_list.count()
    puser2_list = ppluser_list.exclude(regsmo='0').order_by('-acsmo')
    puser3_list = ppluser_list.exclude(regsmo='0').order_by('-tonsmo')
    rrldistrict_list = District.objects.filter(reg_district__plan_sn__result_snid__ignitiondated__range=(adate, bdate)).annotate(regsmo=Count('reg_district__plan_sn__result_snid'),acsmo=Sum('reg_district__plan_sn__result_snid__acresburned'),ptonsmo=Sum('reg_district__plan_sn__result_snid__piletonned'),ltonsmo=Sum('reg_district__plan_sn__result_snid__landingtonned'), tonsmo=Sum('reg_district__plan_sn__result_snid__b_u_tonsperacred'))
    rdistrict_list = rrldistrict_list.exclude(regsmo='0').order_by('-regsmo')
    rdistcount = rdistrict_list.count()
    rdistrict2_list = rrldistrict_list.exclude(regsmo='0').order_by('-acsmo')
    rdistrict3_list = rrldistrict_list.exclude(regsmo='0').order_by('-tonsmo')
    pruser_list = User.objects.filter(reg_user__plan_sn__result_snid__ignitiondated__range=(adate, bdate)).annotate(regsmo=Count('reg_user__plan_sn__result_snid'),acsmo=Sum('reg_user__plan_sn__result_snid__acresburned'),tonsmo=Sum('reg_user__plan_sn__result_snid__b_u_tonsperacred'))
    ruser_list = pruser_list.exclude(regsmo='0').order_by('-regsmo')
    rusercount = ruser_list.count()
    ruser2_list = pruser_list.exclude(regsmo='0').order_by('-acsmo')
    ruser3_list = pruser_list.exclude(regsmo='0').order_by('-tonsmo')
    dateyear = year
    result = render(request,'fastrax/dateaccompt.csv', {'dateyear': dateyear, 'dates_reg_list': dates_reg_list, 'dates_plan_list': dates_plan_list, 'dates_result_list': dates_result_list, 'dates_lit_list': dates_lit_list, 'regcount': regcount, 'plancount': plancount, 'resultcount': resultcount, 'district_list': district_list, 'district2_list': district2_list, 'district3_list': district3_list, 'user_list': user_list, 'user2_list': user2_list, 'user3_list': user3_list, 'pdistrict_list': pdistrict_list, 'pdistrict2_list': pdistrict2_list, 'pdistrict3_list': pdistrict3_list, 'puser_list': puser_list, 'puser2_list': puser2_list, 'puser3_list': puser3_list, 'rdistrict_list': rdistrict_list, 'rdistrict2_list': rdistrict2_list, 'rdistrict3_list': rdistrict3_list, 'ruser_list': ruser_list, 'ruser2_list': ruser2_list, 'ruser3_list': ruser3_list, 'distcount': distcount, 'usercount': usercount, 'pdistcount': pdistcount, 'pusercount': pusercount, 'rdistcount': rdistcount, 'rusercount': rusercount, 'acscount': acscount, 'tonscount': tonscount, 'pacscount': pacscount, 'ptonscount': ptonscount, 'pptonscount': pptonscount, 'racscount': racscount, 'rtonscount': rtonscount, 'rptonscount': rptonscount })
    return HttpResponse(result, content_type='text/plain')

def usersum(request, un):
    uuser = User.objects.filter(username__iexact=un)[:1]
    reg_list = SmokeRegister.objects.filter(author__username__exact=un).order_by('sn')
    plan_list = SmokePlan.objects.filter(author__username__exact=un).order_by('sn', 'suffix')
    result_list = SmokeResult.objects.filter(author__username__exact=un).order_by('snid__sn', 'snid__suffix')
    regcount = reg_list.count()
    plancount = plan_list.count()
    resultcount = result_list.count()
    preacs = reg_list.aggregate(Sum('regacres'))
    acscount = sum(preacs.values())
    preptons = reg_list.aggregate(Sum('piletons'))
    ptonscount = sum(preptons.values())
    preltons = reg_list.aggregate(Sum('landingtons'))
    ltonscount = sum(preltons.values())
    pretons = reg_list.aggregate(Sum('fuelclass1'))
    tonscount = sum(pretons.values())
    ppreacs = plan_list.aggregate(Sum('acrestoburn'))
    pacscount = sum(ppreacs.values())
    ppreptons = plan_list.aggregate(Sum('piletons'))
    pptonscount = sum(ppreptons.values())
    ppreltons = plan_list.aggregate(Sum('landingtons'))
    pltonscount = sum(ppreltons.values())
    ppretons = plan_list.aggregate(Sum('b_u_tonsperacre'))
    pptonscount = sum(ppretons.values())
    predistrict_list = District.objects.filter(Q(reg_district__author__username__exact=un)).annotate(regsmo=Count('reg_district'),acsmo=Sum('reg_district__regacres'),ptonsmo=Sum('reg_district__piletons'),ltonsmo=Sum('reg_district__landingtons'), tonsmo=Sum('reg_district__fuelclass1'))
    district_list = predistrict_list.exclude(regsmo='0').order_by('-regsmo')
    distcount = district_list.count()
    district2_list = predistrict_list.exclude(regsmo='0').order_by('-acsmo')
    district3_list = predistrict_list.exclude(regsmo='0').order_by('-tonsmo')
    preuser_list = User.objects.filter(Q(reg_user__author__username__exact=un)).annotate(regsmo=Count('reg_user'),acsmo=Sum('reg_user__regacres'),tonsmo=Sum('reg_user__fuelclass1'))
    user_list = preuser_list.exclude(regsmo='0').order_by('-regsmo')
    usercount = user_list.count()
    user2_list = preuser_list.exclude(regsmo='0').order_by('-acsmo')
    user3_list = preuser_list.exclude(regsmo='0').order_by('-tonsmo')
    ppldistrict_list = District.objects.filter(Q(reg_district__plan_sn__author__username__exact=un)).annotate(regsmo=Count('reg_district__plan_sn'),acsmo=Sum('reg_district__plan_sn__acrestoburn'),ptonsmo=Sum('reg_district__plan_sn__piletons'),ltonsmo=Sum('reg_district__plan_sn__landingtons'), tonsmo=Sum('reg_district__plan_sn__b_u_tonsperacre'))
    pdistrict_list = ppldistrict_list.exclude(regsmo='0').order_by('-regsmo')
    pdistcount = pdistrict_list.count()
    pdistrict2_list = ppldistrict_list.exclude(regsmo='0').order_by('-acsmo')
    pdistrict3_list = ppldistrict_list.exclude(regsmo='0').order_by('-tonsmo')
    ppluser_list = User.objects.filter(Q(reg_user__plan_sn__author__username__exact=un)).annotate(regsmo=Count('reg_user__plan_sn'),acsmo=Sum('reg_user__plan_sn__acrestoburn'),tonsmo=Sum('reg_user__plan_sn__b_u_tonsperacre'))
    puser_list = ppluser_list.exclude(regsmo='0').order_by('-regsmo')
    pusercount = puser_list.count()
    puser2_list = ppluser_list.exclude(regsmo='0').order_by('-acsmo')
    puser3_list = ppluser_list.exclude(regsmo='0').order_by('-tonsmo')
    return render(request,'fastrax/usersum.html', {'uuser': uuser, 'reg_list': reg_list, 'plan_list': plan_list, 'result_list': result_list, 'regcount': regcount, 'plancount': plancount, 'resultcount': resultcount, 'district_list': district_list, 'district2_list': district2_list, 'district3_list': district3_list, 'user_list': user_list, 'user2_list': user2_list, 'user3_list': user3_list, 'pdistrict_list': pdistrict_list, 'pdistrict2_list': pdistrict2_list, 'pdistrict3_list': pdistrict3_list, 'puser_list': puser_list, 'puser2_list': puser2_list, 'puser3_list': puser3_list, 'distcount': distcount, 'usercount': usercount, 'pdistcount': pdistcount, 'pusercount': pusercount, 'acscount': acscount, 'tonscount': tonscount, 'pacscount': pacscount, 'pptonscount': pptonscount })

def odfdistrict(request):
    district_list = ODFPD.objects.all().defer('geometry').exclude(nnn='000').order_by('nnn')
    return render(request,'fastrax/odfdistrict.html', {'district_list': district_list})

def users(request):
    reg_list = User.objects.filter(groups__name='fastrax-users').annotate(rx=Count('reg_user')).order_by('username')
    plan_list = User.objects.filter(groups__name='fastrax-users').annotate(px=Count('plan_user')).order_by('username')
    for user in reg_list:
        name = user.username
        user.px = plan_list.filter(username=name)[0].px
    user_list = reg_list
    col1 = round((reg_list.count())/4 + 2)
    col2 = round(col1 * 2 - 1)
    col3 = round(col1 * 3 - 2)
    col4 = round(col1 * 4 - 3)
    return render(request,'fastrax/users.html', {'user_list': user_list, 'col1': col1, 'col2': col2, 'col3': col3, 'col4': col4, })

def user(request, un):
    adate = datetime.datetime.now().year
    ayear = adate - 2
    iyear = datetime.date(ayear,1,1)
    uuser = User.objects.filter(username__iexact=un)[:1]
    reg_list = SmokeRegister.objects.filter(
        Q(regdate__gte=iyear),
        Q(author__username__exact=un)
        ).annotate(black=Sum('plan_sn__result_snid__acresburned')).filter(Q(black__lt=F('regacres')) | Q(black=None)).order_by('sn')
    for object in reg_list:
        if object.black == None:
            object.color = 'black'
        elif object.black < object.regacres:
            object.color = 'green'
        elif object.black >= object.regacres:
            object.color = 'red'
    plan_list = SmokePlan.objects.filter(
        Q(author__username__exact=un)
        ).exclude(result_snid__result_date__isnull=False).order_by('sn', 'suffix')
    return render(request,'fastrax/user.html', {'uuser': uuser, 'reg_list': reg_list, 'plan_list': plan_list })

def uclosed(request, un):
    adate = datetime.datetime.now().year
    ayear = adate - 2
    iyear = datetime.date(ayear,1,1)
    uuser = User.objects.filter(username__iexact=un)[:1]
    reg_list = SmokeRegister.objects.filter(author__username__exact=un).annotate(black=Sum('plan_sn__result_snid__acresburned')).filter(
        Q(regdate__lt=iyear) | Q(black__gte=F('regacres'))
        ).order_by('sn')
    for object in reg_list:
        if object.black == None:
            object.color = 'black'
        elif object.black < object.regacres:
            object.color = 'green'
        elif object.black >= object.regacres:
            object.color = 'red'
    plan_list = SmokePlan.objects.filter(
        Q(author__username__exact=un)
        ).exclude(result_snid__result_date__isnull=True).order_by('sn', 'suffix')
    result_list = SmokeResult.objects.filter(
        Q(author__username__exact=un)
        ).order_by('snid__sn', 'snid__suffix')
    return render(request,'fastrax/user.html', {'uuser': uuser, 'reg_list': reg_list, 'plan_list': plan_list, 'result_list': result_list, 'iyear': iyear })

def control(request):
    district_list = District.objects.all().order_by('tla','name')
    #iyear = datetime.date((datetime.datetime.now().year - 2),1,1)
    iyear = datetime.date(2007,1,1)
    for d in district_list:
        regr_list = SmokeRegister.objects.filter(
            #Q(regdate__gte=iyear),
            Q(district=d)
            ).order_by('regdate')
        black_list = SmokeRegister.objects.filter(
            #Q(regdate__gte=iyear),
            Q(district=d)
            ).annotate(black=Sum('plan_sn__result_snid__acresburned')).filter(Q(black__lt=F('regacres')) | Q(black=None)).order_by('regdate')
        for object in black_list:
            if object.black == None:
                object.color = 'black'
            elif object.black < object.regacres:
                object.color = 'green'
            elif object.black >= object.regacres:
                object.color = 'red'
        reg_list = black_list
        plan_list = SmokePlan.objects.filter(
            Q(sn__district__slug__iexact=d.slug)
            ).exclude(result_snid__result_date__isnull=False).order_by('sn', 'suffix')
        pland_list = SmokePlan.objects.filter(
            Q(sn__district__slug__iexact=d.slug)
            )
        result_list = SmokeResult.objects.filter(
            Q(snid__sn__district__slug__iexact=d.slug)
            )
        now = datetime.datetime.today()  
        first_month = datetime.datetime(now.year, now.month, 1)
        previous_months = (first_month - relativedelta(months = months) for months in range(0, 60, 1))
        themonths = previous_months
        e=[]
        cumu = regr_list.count()
        cump = pland_list.count()
        cumr = result_list.count()
        d.cumrt = result_list.count()
        maxcount = 0
        maxplan = 0
        maxresult = 0
        for month in themonths:
            iyear = month.year
            imonth = month.month
            entry_count = SmokeRegister.objects.filter(
                Q(regdate__year=iyear),
                Q(regdate__month=imonth),
                Q(district__slug__iexact=d.slug)
                ).annotate(black=Sum('plan_sn__result_snid__acresburned')).filter(Q(black__lt=F('regacres')) | Q(black=None)).count()
            if entry_count >= maxcount:
                d.maxcount = entry_count
            plan_count = SmokePlan.objects.filter(
                Q(plan_date__year=iyear),
                Q(plan_date__month=imonth),
                Q(sn__district__slug__iexact=d.slug)
                ).count()
            if plan_count >= maxplan:
                maxplan = plan_count
            result_count = SmokeResult.objects.filter(
                Q(result_date__year=iyear),
                Q(result_date__month=imonth),
                Q(snid__sn__district__slug__iexact=d.slug)
                ).count()
            if result_count >= maxresult:
                maxresult = result_count
            dict = {'month': month, 'count': entry_count, 'cumu': cumu, 'countp': plan_count, 'cump': cump, 'countr': result_count, 'cumr': cumr }
            e.append(dict)
            cumu = cumu - entry_count
            cump = cump - plan_count
            cumr = cumr - result_count
            d.maxplan = max(maxplan,maxresult)
        d.entry_dates = e

    return render(request,'fastrax/control.html', { 'district_list': district_list, 'iyear': iyear })

def districts(request):
    district_list = District.objects.exclude(state__iexact='WA').order_by('tla')
    col1 = round((district_list.count())/2)
    return render(request,'fastrax/districts.html', {'district_list': district_list, 'col1': col1, })

def tla(request, tn):
    adate = datetime.datetime.now().year
    ayear = adate - 2
    iyear = datetime.date(ayear,1,1)
    dtla = District.objects.filter(tla__iexact=tn)[:1]
    regr_list = SmokeRegister.objects.filter(
        Q(regdate__gte=iyear),
        Q(district__tla__iexact=tn)
        ).annotate(black=Sum('plan_sn__result_snid__acresburned')).order_by('sn')
    black_list = regr_list.filter(Q(black__lt=F('regacres')) | Q(black=None)).order_by('sn')
    for object in black_list:
        if object.black == None:
            object.color = 'black'
        elif object.black < object.regacres:
            object.color = 'green'
        elif object.black >= object.regacres:
            object.color = 'red'
    reg_list = black_list
    plan_list = SmokePlan.objects.filter(
        Q(sn__district__tla__iexact=tn)
        ).exclude(result_snid__result_date__isnull=False).order_by('sn', 'suffix')
    pland_list = SmokePlan.objects.filter(
        Q(sn__district__tla__iexact=tn)
        )
    result_list = SmokeResult.objects.filter(
        Q(snid__sn__district__tla__iexact=tn)
        )
    now = datetime.datetime.today()  
    first_month = datetime.datetime(now.year, now.month, 1)
    previous_months = (first_month - relativedelta(months = months) for months in range(0, 24, 1))
    themonths = previous_months
    e=[]
    cumu = regr_list.count()
    cump = pland_list.count()
    cumr = result_list.count()
    cumrt = result_list.count()
    maxcount = 0
    maxplan = 0
    maxresult = 0
    for month in themonths:
        iyear = month.year
        imonth = month.month
        entry_count = SmokeRegister.objects.filter(
            Q(regdate__year=iyear),
            Q(regdate__month=imonth),
            Q(district__tla__iexact=tn),
            ).annotate(black=Sum('plan_sn__result_snid__acresburned')).filter(Q(black__lt=F('regacres')) | Q(black=None)).count()
        if entry_count >= maxcount:
            maxcount = entry_count
        plan_count = SmokePlan.objects.filter(
            Q(plan_date__year=iyear),
            Q(plan_date__month=imonth),
            Q(sn__district__tla__iexact=tn),
            ).count()
        if plan_count >= maxplan:
            maxplan = plan_count
        result_count = SmokeResult.objects.filter(
            Q(result_date__year=iyear),
            Q(result_date__month=imonth),
            Q(snid__sn__district__tla__iexact=tn),
            ).count()
        if result_count >= maxresult:
            maxresult = result_count
        dict = {'month': month, 'count': entry_count, 'cumu': cumu, 'countp': plan_count, 'cump': cump, 'countr': result_count, 'cumr': cumr }
        e.append(dict)
        cumu = cumu - entry_count
        cump = cump - plan_count
        cumr = cumr - result_count
        maxplan = max(maxplan,maxresult)
    entry_dates = e
    return render(request,'fastrax/tla.html', { 'entry_dates': entry_dates, 'maxcount': maxcount, 'maxplan': maxplan, 'cumrt': cumrt, 'reg_list': reg_list, 'plan_list': plan_list, 'dtla': dtla}) #, 'result_list': result_list })

def tlamap(request, tn):
    adate = datetime.datetime.now().year
    ayear = adate - 2
    iyear = datetime.date(ayear,1,1)
    dtla = District.objects.filter(tla__iexact=tn)[:1]
    regr_list = SmokeRegister.objects.filter(
        Q(regdate__gte=iyear),
        Q(district__tla__iexact=tn)
        ).annotate(black=Sum('plan_sn__result_snid__acresburned')).order_by('sn')
    black_list = regr_list.filter(Q(black__lt=F('regacres')) | Q(black=None)).order_by('sn')
    for object in black_list:
        if object.black == None:
            object.color = 'black'
        elif object.black < object.regacres:
            object.color = 'green'
        elif object.black >= object.regacres:
            object.color = 'red'
    for object in black_list:
        try:
            object.plss = PLSS.objects.get(
                Q(township=object.township.upper()),
                Q(range=object.range.upper()),
                Q(section=object.section.zfill(2))
                )
        except:
            pass
    reg_list = black_list
    plan_list = SmokePlan.objects.filter(
        Q(sn__district__tla__iexact=tn)
        ).exclude(result_snid__result_date__isnull=False).order_by('sn', 'suffix')
    for object in plan_list:
        try:
            object.plss = PLSS.objects.get(
                Q(township=object.sn.township.upper()),
                Q(range=object.sn.range.upper()),
                Q(section=object.sn.section.zfill(2))
                )
        except:
            pass
    d={}
    [d.setdefault(str(a.get_county_display()),a) for a in reg_list]
    co_list = d
    #county_list = County.objects.filter(
    #    Q(name__in=co_list),
    #    Q(state__exact='Oregon')
    #    ).order_by('name')
    e={}
    [e.setdefault(str((a.township.upper() + a.range.upper() + u"%s" % (a.section.zfill(2)))),a) for a in reg_list]
    trs_list = e
    plss_list = PLSS.objects.filter(trs__in=trs_list).order_by('trs')
    e2={}
    [e2.setdefault(str((a.sn.township.upper() + a.sn.range.upper() + u"%s" % (a.sn.section.zfill(2)))),a) for a in plan_list]
    trs2_list = e2
    plss2_list = PLSS.objects.filter(trs__in=trs2_list).order_by('trs')
    return render(request,'fastrax/tlamap.html', { 'reg_list': reg_list, 'plan_list': plan_list, 'dtla': dtla, 'co_list': co_list, 'trs_list': trs_list, 'plss_list': plss_list, 'trs2_list': trs2_list, 'plss2_list': plss2_list,}) #, 'result_list': result_list })

def tclosed(request, tn):
    adate = datetime.datetime.now().year
    ayear = adate - 2
    iyear = datetime.date(ayear,1,1)
    dtla = District.objects.filter(tla__iexact=tn)[:1]
    black_list = SmokeRegister.objects.filter(district__tla__iexact=tn).annotate(black=Sum('plan_sn__result_snid__acresburned')).filter(
        Q(regdate__lt=iyear) | Q(black__gte=F('regacres'))
        ).order_by('sn')
    for object in black_list:
        if object.black == None:
            object.color = 'black'
        elif object.black < object.regacres:
            object.color = 'green'
        elif object.black >= object.regacres:
            object.color = 'red'
    reg_list = black_list
    plan_list = SmokePlan.objects.filter(
        Q(sn__district__tla__iexact=tn)
        ).exclude(result_snid__result_date__isnull=True).order_by('sn', 'suffix')
    now = datetime.datetime.today()  
    first_month = datetime.datetime(now.year, now.month, 1)
    previous_months = (first_month - relativedelta(months = months) for months in range(0, 24, 1))
    themonths = previous_months
    e=[]
    cumu = reg_list.count()
    for month in themonths:
        iyear = month.year
        imonth = month.month
        entry_count = SmokeRegister.objects.filter(
            Q(regdate__year=iyear),
            Q(regdate__month=imonth),
            Q(district__tla__iexact=tn),
            ).annotate(black=Sum('plan_sn__result_snid__acresburned')).filter(black__gte=F('regacres')).count()
        dict = {'month': month, 'count': entry_count, 'cumu': cumu }
        e.append(dict)
        cumu = cumu - entry_count
    entry_dates = e
    return render(request,'fastrax/tla.html', { 'entry_dates': entry_dates, 'reg_list': reg_list, 'plan_list': plan_list, 'dtla': dtla, 'iyear': iyear }) #, 'result_list': result_list })

def district(request, tn, dn):
    adate = datetime.datetime.now().year
    ayear = adate - 2
    iyear = datetime.date(ayear,1,1)
    dtla = District.objects.filter(tla=tn)[:1]
    ddistrict = District.objects.filter(slug=dn)[:1]
    regr_list = SmokeRegister.objects.filter(
        Q(regdate__gte=iyear),
        Q(district__slug__iexact=dn)
        ).order_by('sn')
    black_list = SmokeRegister.objects.filter(
        Q(regdate__gte=iyear),
        Q(district__slug__iexact=dn)
        ).annotate(black=Sum('plan_sn__result_snid__acresburned')).filter(Q(black__lt=F('regacres')) | Q(black=None)).order_by('sn')
    for object in black_list:
        if object.black == None:
            object.color = 'black'
        elif object.black < object.regacres:
            object.color = 'green'
        elif object.black >= object.regacres:
            object.color = 'red'
    reg_list = black_list
    plan_list = SmokePlan.objects.filter(
        Q(sn__district__slug__iexact=dn)
        ).exclude(result_snid__result_date__isnull=False).order_by('sn', 'suffix')
    pland_list = SmokePlan.objects.filter(
        Q(sn__district__slug__iexact=dn)
        )
    result_list = SmokeResult.objects.filter(
        Q(snid__sn__district__slug__iexact=dn)
        )
    now = datetime.datetime.today()  
    first_month = datetime.datetime(now.year, now.month, 1)
    previous_months = (first_month - relativedelta(months = months) for months in range(0, 24, 1))
    themonths = previous_months
    e=[]
    cumu = regr_list.count()
    cump = pland_list.count()
    cumr = result_list.count()
    cumrt = result_list.count()
    maxcount = 0
    maxplan = 0
    maxresult = 0
    for month in themonths:
        iyear = month.year
        imonth = month.month
        entry_count = SmokeRegister.objects.filter(
            Q(regdate__year=iyear),
            Q(regdate__month=imonth),
            Q(district__slug__iexact=dn)
            ).annotate(black=Sum('plan_sn__result_snid__acresburned')).filter(Q(black__lt=F('regacres')) | Q(black=None)).count()
        if entry_count >= maxcount:
            maxcount = entry_count
        plan_count = SmokePlan.objects.filter(
            Q(plan_date__year=iyear),
            Q(plan_date__month=imonth),
            Q(sn__district__slug__iexact=dn)
            ).count()
        if plan_count >= maxplan:
            maxplan = plan_count
        result_count = SmokeResult.objects.filter(
            Q(result_date__year=iyear),
            Q(result_date__month=imonth),
            Q(snid__sn__district__slug__iexact=dn)
            ).count()
        if result_count >= maxresult:
            maxresult = result_count
        dict = {'month': month, 'count': entry_count, 'cumu': cumu, 'countp': plan_count, 'cump': cump, 'countr': result_count, 'cumr': cumr }
        e.append(dict)
        cumu = cumu - entry_count
        cump = cump - plan_count
        cumr = cumr - result_count
        maxplan = max(maxplan,maxresult)
    entry_dates = e
    return render(request,'fastrax/district.html', { 'entry_dates': entry_dates, 'maxcount': maxcount, 'maxplan': maxplan, 'cumrt': cumrt, 'reg_list': reg_list, 'plan_list': plan_list, 'ddistrict': ddistrict, 'dtla': dtla},)

def dclosed(request, tn, dn):
    adate = datetime.datetime.now().year
    ayear = adate - 2
    iyear = datetime.date(ayear,1,1)
    dtla = District.objects.filter(tla=tn)[:1]
    ddistrict = District.objects.filter(slug=dn)[:1]
    #reg_list = SmokeRegister.objects.filter(
    #    Q(regdate__lt=iyear),
    #    Q(district__slug__iexact=dn)
    #    ).order_by('sn')
    black_list = SmokeRegister.objects.filter(district__slug__iexact=dn).annotate(black=Sum('plan_sn__result_snid__acresburned')).filter(
        Q(regdate__lt=iyear) | Q(black__gte=F('regacres'))
        ).order_by('sn')
    for object in black_list:
        if object.black == None:
            object.color = 'black'
        elif object.black < object.regacres:
            object.color = 'green'
        elif object.black >= object.regacres:
            object.color = 'red'
    reg_list = black_list
    plan_list = SmokePlan.objects.filter(
        Q(sn__district__slug__iexact=dn)
        ).exclude(result_snid__result_date__isnull=True).order_by('sn', 'suffix')
    now = datetime.datetime.today()  
    first_month = datetime.datetime(now.year, now.month, 1)
    previous_months = (first_month - relativedelta(months = months) for months in range(0, 24, 1))
    themonths = previous_months
    e=[]
    cumu = reg_list.count()
    for month in themonths:
        iyear = month.year
        imonth = month.month
        entry_count = SmokeRegister.objects.filter(
            Q(regdate__year=iyear),
            Q(regdate__month=imonth),
            Q(district__slug__iexact=dn),
            ).annotate(black=Sum('plan_sn__result_snid__acresburned')).filter(black__gte=F('regacres')).count()
        dict = {'month': month, 'count': entry_count, 'cumu': cumu }
        e.append(dict)
        cumu = cumu - entry_count
    entry_dates = e
    return render(request,'fastrax/district.html', { 'entry_dates': entry_dates, 'reg_list': reg_list, 'plan_list': plan_list, 'ddistrict': ddistrict, 'dtla': dtla, 'iyear': iyear }) #, 'result_list': result_list })

def distmap(request, tn, dn):
    adate = datetime.datetime.now().year
    ayear = adate - 2
    iyear = datetime.date(ayear,1,1)
    dtla = District.objects.filter(tla=tn)[:1]
    ddistrict = District.objects.filter(slug=dn)[:1]
    black_list = SmokeRegister.objects.filter(
        Q(regdate__gte=iyear),
        Q(district__slug__iexact=dn)
        ).annotate(black=Sum('plan_sn__result_snid__acresburned')).filter(Q(black__lt=F('regacres')) | Q(black=None)).order_by('sn')
    for object in black_list:
        if object.black == None:
            object.color = 'black'
        elif object.black < object.regacres:
            object.color = 'green'
        elif object.black >= object.regacres:
            object.color = 'red'
    for object in black_list:
        try:
            object.plss = PLSS.objects.get(
                Q(township=object.township.upper()),
                Q(range=object.range.upper()),
                Q(section=object.section.zfill(2))
                )
        except:
            pass
    reg_list = black_list
    #reg_list = black_list.filter(Q(black__lt=F('regacres')) | Q(black=None))
    #reg_listd = black_list.filter(black__gte=F('regacres'))
    plan_list = SmokePlan.objects.filter(
        Q(sn__district__slug__iexact=dn)
        ).exclude(result_snid__result_date__isnull=False).order_by('sn', 'suffix')
    for object in plan_list:
        try:
            object.plss = PLSS.objects.get(
                Q(township=object.sn.township.upper()),
                Q(range=object.sn.range.upper()),
                Q(section=object.sn.section.zfill(2))
                )
        except:
            pass
    d={}
    [d.setdefault(str(a.get_county_display()),a) for a in reg_list]
    co_list = d
    #county_list = County.objects.filter(
    #    Q(name__in=co_list),
    #    Q(state__exact='Oregon')
    #    ).order_by('name')
    e={}
    [e.setdefault(str((a.township.upper() + a.range.upper() + u"%s" % (a.section.zfill(2)))),a) for a in reg_list]
    trs_list = e
    plss_list = PLSS.objects.filter(trs__in=trs_list).order_by('trs')
    e2={}
    [e2.setdefault(str((a.sn.township.upper() + a.sn.range.upper() + u"%s" % (a.sn.section.zfill(2)))),a) for a in plan_list]
    trs2_list = e2
    plss2_list = PLSS.objects.filter(trs__in=trs2_list).order_by('trs')
    return render(request,'fastrax/distmap.html', {'dtla': dtla, 'ddistrict': ddistrict, 'reg_list': reg_list, 'plan_list': plan_list, 'co_list': co_list, 'trs_list': trs_list, 'plss_list': plss_list, 'trs2_list': trs2_list, 'plss2_list': plss2_list, })

def upcoming(request):
    adate = datetime.datetime.now()
    dates_result_list = SmokePlan.objects.filter(result_snid__ignitiondated__gte=adate).order_by('result_snid__notaccomplished','result_snid__ignitiondated','result_snid__ignitiontimed','sn', 'suffix')
    dates_plan_list = SmokePlan.objects.filter(ignitiondate__gte=adate).filter(result_snid__ignitiondated=None).order_by('ignitiondate','ignitiontime','sn', 'suffix')
    for planb in dates_result_list:
        try:
            planb.plss = PLSS.objects.get(
                Q(township=planb.sn.township.upper()),
                Q(range=planb.sn.range.upper()),
                Q(section=planb.sn.section.zfill(2))
                )
        except:
            pass
    for plan in dates_plan_list:
        try:
            plan.plss = PLSS.objects.get(
                Q(township=plan.sn.township.upper()),
                Q(range=plan.sn.range.upper()),
                Q(section=plan.sn.section.zfill(2))
                )
        except:
            pass
    e2={}
    [e2.setdefault(str((a.sn.township.upper() + a.sn.range.upper() + u"%s" % (a.sn.section.zfill(2)))),a) for a in dates_plan_list]
    trs2_list = e2
    plss2_list = PLSS.objects.filter(trs__in=trs2_list).order_by('trs')
    e3={}
    [e3.setdefault(str((a.sn.township.upper() + a.sn.range.upper() + u"%s" % (a.sn.section.zfill(2)))),a) for a in dates_result_list]
    trs3_list = e3
    plss3_list = PLSS.objects.filter(trs__in=trs3_list).order_by('trs')
    return render(request,'fastrax/dateignition.html', {'dates_plan_list': dates_plan_list, 'dates_result_list': dates_result_list, 'adate': adate, 'trs2_list': trs2_list, 'plss2_list': plss2_list, 'plss3_list': plss3_list, })

def date_ignition(request, year, mo, da):
    dates_result_list = SmokePlan.objects.filter(
        Q(result_snid__ignitiondated__year=year),
        Q(result_snid__ignitiondated__month=mo),
        Q(result_snid__ignitiondated__day=da) # burned today
        ).order_by('result_snid__notaccomplished','result_snid__ignitiondated','result_snid__ignitiontimed','sn', 'suffix')
    dates_plan_list = SmokePlan.objects.filter(
        Q(ignitiondate__year=year),
        Q(ignitiondate__month=mo),
        Q(ignitiondate__day=da) # planned for today...
        #).exclude( # exlude any resuted plans
        #Q(result_snid__ignitiondated__year=year),
        #Q(result_snid__ignitiondated__month=mo),
        #Q(result_snid__ignitiondated__day=da) # ...but not burned today -- this is broke for 9 28 2013
        ).filter(result_snid__ignitiondated=None).order_by('ignitiondate','ignitiontime','sn', 'suffix') 
    dateyear = year
    datemo = mo
    dateda = da
    for planb in dates_result_list:
        try:
            planb.plss = PLSS.objects.get(
                Q(township=planb.sn.township.upper()),
                Q(range=planb.sn.range.upper()),
                Q(section=planb.sn.section.zfill(2))
                )
        except:
            pass
    for plan in dates_plan_list:
        try:
            plan.plss = PLSS.objects.get(
                Q(township=plan.sn.township.upper()),
                Q(range=plan.sn.range.upper()),
                Q(section=plan.sn.section.zfill(2))
                )
        except:
            pass
    e2={}
    [e2.setdefault(str((a.sn.township.upper() + a.sn.range.upper() + u"%s" % (a.sn.section.zfill(2)))),a) for a in dates_plan_list]
    trs2_list = e2
    plss2_list = PLSS.objects.filter(trs__in=trs2_list).order_by('trs')
    e3={}
    [e3.setdefault(str((a.sn.township.upper() + a.sn.range.upper() + u"%s" % (a.sn.section.zfill(2)))),a) for a in dates_result_list]
    trs3_list = e3
    plss3_list = PLSS.objects.filter(trs__in=trs3_list).order_by('trs')
    return render(request,'fastrax/dateignition.html', {'dates_plan_list': dates_plan_list, 'dates_result_list': dates_result_list, 'dateyear': dateyear, 'datemo': datemo, 'dateda': dateda, 'trs2_list': trs2_list, 'plss2_list': plss2_list, 'plss3_list': plss3_list, })

def datemap(request, year, mo, da):
    black_list = SmokeRegister.objects.filter(
        Q(regdate__year=year),
        Q(regdate__month=mo),
        Q(regdate__day=da)
        ).annotate(black=Sum('plan_sn__result_snid__acresburned')).order_by('sn')
    for object in black_list:
        if object.black == None:
            object.color = 'black'
        elif object.black < object.regacres:
            object.color = 'green'
        elif object.black >= object.regacres:
            object.color = 'red'
    for object in black_list:
        try:
            object.plss = PLSS.objects.get(
                Q(township=object.township.upper()),
                Q(range=object.range.upper()),
                Q(section=object.section.zfill(2))
                )
        except:
            pass
    dates_reg_list = black_list
    dates_plan_list = SmokePlan.objects.filter(
        Q(plan_date__year=year),
        Q(plan_date__month=mo),
        Q(plan_date__day=da)
        ).order_by('sn', 'suffix')
    for object in dates_plan_list:
        try:
            object.plss = PLSS.objects.get(
                Q(township=object.sn.township.upper()),
                Q(range=object.sn.range.upper()),
                Q(section=object.sn.section.zfill(2))
                )
        except:
            pass
    dates_result_list = SmokeResult.objects.filter(
        Q(result_date__year=year),
        Q(result_date__month=mo),
        Q(result_date__day=da)
        ).order_by('snid__sn', 'snid__suffix')
    for object in dates_result_list:
        try:
            object.plss = PLSS.objects.get(
                Q(township=object.snid.sn.township.upper()),
                Q(range=object.snid.sn.range.upper()),
                Q(section=object.snid.sn.section.zfill(2))
                )
        except:
            pass
    dateyear = year
    datemo = mo
    dateda = da
    d={}
    [d.setdefault(str(a.get_county_display()),a) for a in dates_reg_list]
    co_list = d
    #county_list = County.objects.filter(
    #    Q(name__in=co_list),
    #    Q(state__exact='Oregon')
    #    ).order_by('name')
    e={}
    [e.setdefault(str((a.township.upper() + a.range.upper() + u"%s" % (a.section.zfill(2)))),a) for a in dates_reg_list]
    trs_list = e
    plss_list = PLSS.objects.filter(trs__in=trs_list).order_by('trs')
    e2={}
    [e2.setdefault(str((a.sn.township.upper() + a.sn.range.upper() + u"%s" % (a.sn.section.zfill(2)))),a) for a in dates_plan_list]
    trs2_list = e2
    plss2_list = PLSS.objects.filter(trs__in=trs2_list).order_by('trs')
    e3={}
    [e3.setdefault(str((a.snid.sn.township.upper() + a.snid.sn.range.upper() + u"%s" % (a.snid.sn.section.zfill(2)))),a) for a in dates_result_list]
    trs3_list = e3
    plss3_list = PLSS.objects.filter(trs__in=trs3_list).order_by('trs')
    return render(request,'fastrax/datemap.html', {'dates_reg_list': dates_reg_list, 'dates_plan_list': dates_plan_list, 'dates_result_list': dates_result_list, 'dateyear': dateyear, 'datemo': datemo, 'dateda': dateda, 'co_list': co_list, 'trs_list': trs_list, 'plss_list': plss_list, 'trs2_list': trs2_list, 'plss2_list': plss2_list, 'plss3_list': plss3_list, })

def monthmap(request, year, mo):
    black_list = SmokeRegister.objects.filter(
        Q(regdate__year=year),
        Q(regdate__month=mo)
        ).annotate(black=Sum('plan_sn__result_snid__acresburned')).order_by('sn')
    for object in black_list:
        if object.black == None:
            object.color = 'black'
        elif object.black < object.regacres:
            object.color = 'green'
        elif object.black >= object.regacres:
            object.color = 'red'
    for object in black_list:
        try:
            object.plss = PLSS.objects.get(
                Q(township=object.township.upper()),
                Q(range=object.range.upper()),
                Q(section=object.section.zfill(2))
                )
        except:
            pass
    dates_reg_list = black_list
    dates_plan_list = SmokePlan.objects.filter(
        Q(plan_date__year=year),
        Q(plan_date__month=mo)
        ).order_by('sn', 'suffix')
    for object in dates_plan_list:
        try:
            object.plss = PLSS.objects.get(
                Q(township=object.sn.township.upper()),
                Q(range=object.sn.range.upper()),
                Q(section=object.sn.section.zfill(2))
                )
        except:
            pass
    dates_result_list = SmokeResult.objects.filter(
        Q(result_date__year=year),
        Q(result_date__month=mo)
        ).order_by('snid__sn', 'snid__suffix')
    for object in dates_result_list:
        try:
            object.plss = PLSS.objects.get(
                Q(township=object.snid.sn.township.upper()),
                Q(range=object.snid.sn.range.upper()),
                Q(section=object.snid.sn.section.zfill(2))
                )
        except:
            pass

    dateyear = year
    datemo = mo
    #dateda = da
    d={}
    [d.setdefault(str(a.get_county_display()),a) for a in dates_reg_list]
    co_list = d
    #county_list = County.objects.filter(
    #    Q(name__in=co_list),
    #    Q(state__exact='Oregon')
    #    ).order_by('name')
    e={}
    [e.setdefault(str((a.township.upper() + a.range.upper() + u"%s" % (a.section.zfill(2)))),a) for a in dates_reg_list]
    trs_list = e
    plss_list = PLSS.objects.filter(trs__in=trs_list).order_by('trs')
    e2={}
    [e2.setdefault(str((a.sn.township.upper() + a.sn.range.upper() + u"%s" % (a.sn.section.zfill(2)))),a) for a in dates_plan_list]
    trs2_list = e2
    plss2_list = PLSS.objects.filter(trs__in=trs2_list).order_by('trs')
    e3={}
    [e3.setdefault(str((a.snid.sn.township.upper() + a.snid.sn.range.upper() + u"%s" % (a.snid.sn.section.zfill(2)))),a) for a in dates_result_list]
    trs3_list = e3
    plss3_list = PLSS.objects.filter(trs__in=trs3_list).order_by('trs')
    return render(request,'fastrax/datemap.html', {'dates_reg_list': dates_reg_list, 'dates_plan_list': dates_plan_list, 'dates_result_list': dates_result_list, 'dateyear': dateyear, 'datemo': datemo, 'co_list': co_list, 'trs_list': trs_list, 'plss_list': plss_list, 'trs2_list': trs2_list, 'plss2_list': plss2_list, 'plss3_list': plss3_list, })

def yearmap(request, year):
    black_list = SmokeRegister.objects.filter(regdate__year=year).annotate(black=Sum('plan_sn__result_snid__acresburned')).order_by('sn')
    for object in black_list:
        if object.black == None:
            object.color = 'black'
        elif object.black < object.regacres:
            object.color = 'green'
        elif object.black >= object.regacres:
            object.color = 'red'
    for object in black_list:
        try:
            object.plss = PLSS.objects.get(
                Q(township=object.township.upper()),
                Q(range=object.range.upper()),
                Q(section=object.section.zfill(2))
                )
        except:
            pass
    dates_reg_list = black_list
    dates_plan_list = SmokePlan.objects.filter(plan_date__year=year).order_by('sn', 'suffix')
    for object in dates_plan_list:
        try:
            object.plss = PLSS.objects.get(
                Q(township=object.sn.township.upper()),
                Q(range=object.sn.range.upper()),
                Q(section=object.sn.section.zfill(2))
                )
        except:
            pass
    dates_result_list = SmokeResult.objects.filter(result_date__year=year).order_by('snid__sn', 'snid__suffix')
    for object in dates_result_list:
        try:
            object.plss = PLSS.objects.get(
                Q(township=object.snid.sn.township.upper()),
                Q(range=object.snid.sn.range.upper()),
                Q(section=object.snid.sn.section.zfill(2))
                )
        except:
            pass

    dateyear = year
    d={}
    [d.setdefault(str(a.get_county_display()),a) for a in dates_reg_list]
    co_list = d
    #county_list = County.objects.filter(
    #    Q(name__in=co_list),
    #    Q(state__exact='Oregon')
    #    ).order_by('name')
    e={}
    [e.setdefault(str((a.township.upper() + a.range.upper() + u"%s" % (a.section.zfill(2)))),a) for a in dates_reg_list]
    trs_list = e
    plss_list = PLSS.objects.filter(trs__in=trs_list).order_by('trs')
    e2={}
    [e2.setdefault(str((a.sn.township.upper() + a.sn.range.upper() + u"%s" % (a.sn.section.zfill(2)))),a) for a in dates_plan_list]
    trs2_list = e2
    plss2_list = PLSS.objects.filter(trs__in=trs2_list).order_by('trs')
    e3={}
    [e3.setdefault(str((a.snid.sn.township.upper() + a.snid.sn.range.upper() + u"%s" % (a.snid.sn.section.zfill(2)))),a) for a in dates_result_list]
    trs3_list = e3
    plss3_list = PLSS.objects.filter(trs__in=trs3_list).order_by('trs')
    return render(request,'fastrax/datemap.html', {'dates_reg_list': dates_reg_list, 'dates_plan_list': dates_plan_list, 'dates_result_list': dates_result_list, 'dateyear': dateyear, 'co_list': co_list, 'trs_list': trs_list, 'plss_list': plss_list, 'trs2_list': trs2_list, 'plss2_list': plss2_list, 'plss3_list': plss3_list, })

def dateam(request, year, mo, da, hr, mi):
    dateyear = year
    intyear = int(year)
    datemo = mo
    intmo = int(mo)
    dateda = da
    intda = int(da)
    datehr = hr
    inthr = int(hr)
    datemi = mi
    intmi = int(mi)
    sun = datetime.datetime(intyear, intmo, intda)
    starp = sun
    storp = starp
    if hr == '04':
        starp = sun - datetime.timedelta(hours=13, minutes=14, seconds=0)
        storp = starp + datetime.timedelta(hours=17, minutes=59, seconds=59)
        last = 20
    if hr == '10':
        starp = sun + datetime.timedelta(hours=4, minutes=46, seconds=0)
        storp = starp + datetime.timedelta(hours=5, minutes=59, seconds=59)
        last = 7
    dates_reg_list = SmokeRegister.objects.filter(entered__range=(starp, storp)).annotate(black=Sum('plan_sn__result_snid__acresburned')).order_by('entered')
    for object in dates_reg_list:
        if object.black == None:
            object.color = 'black'
        elif object.black < object.regacres:
            object.color = 'green'
        elif object.black >= object.regacres:
            object.color = 'red'
    dates_regu_list = SmokeRegister.objects.filter(modified__range=(starp, storp)).exclude(entered__range=(starp, storp)).annotate(black=Sum('plan_sn__result_snid__acresburned')).order_by('modified')
    for object in dates_regu_list:
        if object.black == None:
            object.color = 'black'
        elif object.black < object.regacres:
            object.color = 'green'
        elif object.black >= object.regacres:
            object.color = 'red'
    dates_plan_list = SmokePlan.objects.filter(entered__range=(starp, storp)).order_by('entered')
    dates_result_list = SmokeResult.objects.filter(entered__range=(starp, storp)).order_by('entered')
    dates_resultu_list = SmokeResult.objects.filter(modified__range=(starp, storp)).exclude(entered__range=(starp, storp)).order_by('modified')
    #last = 23
    #first_month = datetime.datetime(intyear, intmo, intda, last)
    first_month = storp
    previous_months = (first_month - relativedelta(hours = hours) for hours in range(0, last, 1))
    #previous_months = (first_month - starp)
    themonths = previous_months
    e=[]
    cumu = dates_reg_list.count()
    cump = dates_plan_list.count()
    cumr = dates_result_list.count()
    maxcount = 0
    maxplan = 0
    maxresult = 0
    for month in themonths:
        iyear = month.year
        imonth = month.month
        idate = month.day
        ihour = month.hour
        entry_count = SmokeRegister.objects.filter(
            Q(modified__range=(starp, storp)),
            Q(modified__gte=datetime.datetime(iyear,imonth,idate,ihour,0)) & Q(modified__lte=datetime.datetime(iyear,imonth,idate,ihour,59))
            ).count()
        if entry_count >= maxcount:
            maxcount = entry_count
        plan_count = SmokePlan.objects.filter(
            Q(entered__range=(starp, storp)),
            Q(entered__gte=datetime.datetime(iyear,imonth,idate,ihour,0)) & Q(entered__lte=datetime.datetime(iyear,imonth,idate,ihour,59))
            ).count()
        if plan_count >= maxplan:
            maxplan = plan_count
        result_count = SmokeResult.objects.filter(
            Q(modified__range=(starp, storp)),
            Q(modified__gte=datetime.datetime(iyear,imonth,idate,ihour,0)) & Q(modified__lte=datetime.datetime(iyear,imonth,idate,ihour,59))
            ).count()
        if result_count >= maxresult:
            maxresult = result_count
        dict = {'month': ihour, 'count': entry_count, 'cumu': cumu, 'countp': plan_count, 'cump': cump, 'countr': result_count, 'cumr': cumr }
        e.append(dict)
        cumu = cumu - entry_count
        cump = cump - plan_count
        cumr = cumr - result_count
        maxplan = max(maxplan,maxresult)
    entry_dates = e

    d={}
    [d.setdefault(str(a.get_county_display()),a) for a in dates_reg_list]
    co_list = d
    #county_list = County.objects.filter(
    #    Q(name__in=co_list),
    #    Q(state__exact='Oregon')
    #    ).order_by('name')
    e={}
    [e.setdefault(str((a.township.upper() + a.range.upper() + u"%s" % (a.section.zfill(2)))),a) for a in dates_reg_list]
    trs_list = e
    plss_list = PLSS.objects.filter(trs__in=trs_list).order_by('trs')
    e2={}
    [e2.setdefault(str((a.sn.township.upper() + a.sn.range.upper() + u"%s" % (a.sn.section.zfill(2)))),a) for a in dates_plan_list]
    trs2_list = e2
    plss2_list = PLSS.objects.filter(trs__in=trs2_list).order_by('trs')

    return render(request,'fastrax/dateam.html', {'entry_dates': entry_dates, 'maxcount': maxcount, 'maxplan': maxplan, 'dates_reg_list': dates_reg_list, 'dates_regu_list': dates_regu_list, 'dates_plan_list': dates_plan_list, 'dates_result_list': dates_result_list, 'dates_resultu_list': dates_resultu_list, 'starp': starp, 'storp': storp, 'dateyear': dateyear, 'datemo': datemo, 'dateda': dateda, 'datehr': datehr, 'datemi': datemi, 'co_list': co_list, 'trs_list': trs_list, 'plss_list': plss_list, 'trs2_list': trs2_list, 'plss2_list': plss2_list,})

def odfamtxt(request, year, mo, da, hr, mi):
    dateyear = year
    datemo = mo
    dateda = da
    datehr = hr
    datemi = mi
    iyear = int(dateyear)
    imo = int(datemo)
    ida = int(dateda)
    ihr = int(datehr)
    imi = int(datemi)
    sun = datetime.datetime(iyear, imo, ida)
    starp = sun
    storp = starp
    if hr == '04':
        starp = sun - datetime.timedelta(hours=13, minutes=14, seconds=0)
        storp = starp + datetime.timedelta(hours=17, minutes=59, seconds=59)
    if hr == '10':
        starp = sun + datetime.timedelta(hours=4, minutes=46, seconds=0)
        storp = starp + datetime.timedelta(hours=5, minutes=59, seconds=59)
    dates_reg_list = SmokeRegister.objects.filter(entered__range=(starp, storp)).order_by('entered')
    dates_regu_list = SmokeRegister.objects.filter(modified__range=(starp, storp)).exclude(entered__range=(starp, storp)).order_by('modified')
    dates_plan_list = SmokePlan.objects.filter(entered__range=(starp, storp)).order_by('entered')
    dates_result_list = SmokeResult.objects.filter(entered__range=(starp, storp)).order_by('entered')
    dates_resultu_list = SmokeResult.objects.filter(modified__range=(starp, storp)).exclude(entered__range=(starp, storp)).order_by('modified')
    odfyear = year
    odfmo = mo
    odfda = da
    result = render(request,'fastrax/odfdate.txt', {'dates_reg_list': dates_reg_list, 'dates_regu_list': dates_regu_list, 'dates_plan_list': dates_plan_list, 'dates_result_list': dates_result_list, 'dates_resultu_list': dates_resultu_list, 'starp': starp, 'storp': storp, 'dateyear': dateyear, 'datemo': datemo, 'dateda': dateda, 'datehr': datehr, 'datemi': datemi, 'odfyear': odfyear, 'odfmo': odfmo, 'odfda': odfda,})
    return HttpResponse(result, content_type='text/plain') 

def dateammap(request, year, mo, da, hr, mi):
    dateyear = year
    datemo = mo
    dateda = da
    datehr = hr
    datemi = mi
    iyear = int(dateyear)
    imo = int(datemo)
    ida = int(dateda)
    ihr = int(datehr)
    imi = int(datemi)
    sun = datetime.datetime(iyear, imo, ida)
    starp = sun
    storp = starp
    if hr == '04':
        starp = sun - datetime.timedelta(hours=13, minutes=14, seconds=0)
        storp = starp + datetime.timedelta(hours=17, minutes=59, seconds=59)
    if hr == '10':
        starp = sun + datetime.timedelta(hours=4, minutes=46, seconds=0)
        storp = starp + datetime.timedelta(hours=5, minutes=59, seconds=59)
    dates_regu_list = SmokeRegister.objects.filter(modified__range=(starp, storp)).exclude(entered__range=(starp, storp)).annotate(black=Sum('plan_sn__result_snid__acresburned')).order_by('modified')
    for object in dates_regu_list:
        if object.black < object.regacres:
            object.color = 'green'
        elif object.black == None:
            object.color = 'black'
        elif object.black >= object.regacres:
            object.color = 'red'
    dates_resultu_list = SmokeResult.objects.filter(modified__range=(starp, storp)).exclude(entered__range=(starp, storp)).order_by('modified')
    black_list = SmokeRegister.objects.filter(entered__range=(starp, storp)).annotate(black=Sum('plan_sn__result_snid__acresburned')).order_by('entered')
    for object in black_list:
        if object.black == None:
            object.color = 'black'
        elif object.black < object.regacres:
            object.color = 'green'
        elif object.black >= object.regacres:
            object.color = 'red'
    for object in black_list:
        try:
            object.plss = PLSS.objects.get(
                Q(township=object.township.upper()),
                Q(range=object.range.upper()),
                Q(section=object.section.zfill(2))
                )
        except:
            pass
    dates_reg_list = black_list
    dates_plan_list = SmokePlan.objects.filter(entered__range=(starp, storp)).order_by('entered')
    for object in dates_plan_list:
        try:
            object.plss = PLSS.objects.get(
                Q(township=object.sn.township.upper()),
                Q(range=object.sn.range.upper()),
                Q(section=object.sn.section.zfill(2))
                )
        except:
            pass
    dates_result_list = SmokeResult.objects.filter(entered__range=(starp, storp)).order_by('entered')
    for object in dates_result_list:
        try:
            object.plss = PLSS.objects.get(
                Q(township=object.snid.sn.township.upper()),
                Q(range=object.snid.sn.range.upper()),
                Q(section=object.snid.sn.section.zfill(2))
                )
        except:
            pass
    dateyear = year
    datemo = mo
    dateda = da
    d={}
    [d.setdefault(str(a.get_county_display()),a) for a in dates_reg_list]
    co_list = d
    #county_list = County.objects.filter(
    #    Q(name__in=co_list),
    #    Q(state__exact='Oregon')
    #    ).order_by('name')
    e={}
    [e.setdefault(str((a.township.upper() + a.range.upper() + u"%s" % (a.section.zfill(2)))),a) for a in dates_reg_list]
    trs_list = e
    plss_list = PLSS.objects.filter(trs__in=trs_list).order_by('trs')
    e2={}
    [e2.setdefault(str((a.sn.township.upper() + a.sn.range.upper() + u"%s" % (a.sn.section.zfill(2)))),a) for a in dates_plan_list]
    trs2_list = e2
    plss2_list = PLSS.objects.filter(trs__in=trs2_list).order_by('trs')
    e3={}
    [e3.setdefault(str((a.snid.sn.township.upper() + a.snid.sn.range.upper() + u"%s" % (a.snid.sn.section.zfill(2)))),a) for a in dates_result_list]
    trs3_list = e3
    plss3_list = PLSS.objects.filter(trs__in=trs3_list).order_by('trs')
    return render(request,'fastrax/dateammap.html', {'dates_reg_list': dates_reg_list, 'dates_regu_list': dates_regu_list, 'dates_plan_list': dates_plan_list, 'dates_result_list': dates_result_list, 'dates_resultu_list': dates_resultu_list, 'starp': starp, 'storp': storp, 'dateyear': dateyear, 'datemo': datemo, 'dateda': dateda, 'datehr': datehr, 'datemi': datemi, 'co_list': co_list, 'trs_list': trs_list, 'plss_list': plss_list, 'trs2_list': trs2_list, 'plss2_list': plss2_list, 'plss3_list': plss3_list,})

@login_required
@permission_required('fastrax.add_smokeregister')
def transfer(request):
    adate = datetime.datetime.now()
    #adate = datetime.datetime(2010, 04, 18, 04, 43) #test date
    #adate = datetime.datetime(2010, 04, 18, 04, 45) #test date
    #adate = datetime.datetime(2010, 04, 18, 04, 47) #test date
    #adate = datetime.datetime(2010, 04, 18, 10, 43) #test date
    #adate = datetime.datetime(2010, 04, 18, 10, 45) #test date
    #adate = datetime.datetime(2010, 04, 18, 10, 47) #test date
    idate = int(adate.strftime("%Y%m%d"))
    iyear = int(adate.strftime("%Y"))
    imo = int(adate.strftime("%m"))
    ida = int(adate.strftime("%d"))
    itime = int(adate.strftime("%H%M"))
    #itime = int('0443') # test time
    d0445 = datetime.datetime(iyear, imo, ida, 4, 45)
    d1045 = datetime.datetime(iyear, imo, ida, 10, 45)
    ndate = adate + datetime.timedelta(hours=24)
    nyear = int(ndate.strftime("%Y"))
    nmo = int(ndate.strftime("%m"))
    nda = int(ndate.strftime("%d"))
    n0445 = datetime.datetime(nyear, nmo, nda, 4, 45)
    duntil = n0445 - adate
    duntil = duntil.seconds
    ftime = '0000'
    if itime < int('1059'):
        duntil = n0445 - adate
        duntil = duntil.seconds
        ftime = '1045'
    if itime < int('1046'):
        duntil = int('60')
        ftime = '0000'
    if itime < int('1045'):
        duntil = d1045 - adate
        duntil = duntil.seconds
        ftime = '0000'
    if itime < int('0459'):
        duntil = d1045 - adate
        duntil = duntil.seconds
        ftime = '0445'
    if itime < int('0446'):
        duntil = int('60')
        ftime = '0000'
    if itime < int('0445'):
        duntil = d0445 - adate
        duntil = duntil.seconds
        ftime = '0000'
    test1 = duntil
    test2 = duntil
    test3 = duntil
    #duntil = min(test1, test2, test3)
    muntil = duntil
    fdate = str(idate)
    #ftime = str(itime)
    fname = str("REGISTERDATETIME" + fdate + ftime + ".txt")
    url = str("http:{{ request.site.domain }}odf/" + fname)
    sock = urllib.urlopen(url)
    htmlSource = sock.read()
    sock.close()
    logcmd = str(settings.STATIC_ROOT + '/odfout/' + fname)
    logfile = open(logcmd, 'w')
    logfile.write(htmlSource)
    logfile.close()
    storcmd = ''
    #ftp = FTP('ftp2.fs.fed.us')
    #ftp.login('anonymous','anonymous')
    #ftp.cwd('incoming/r6/fire/fastracs')
    if ftime == '0445':
        #ftp = FTP('REDACTED')
        ftp = FTP('REDACTED')
        #ftp.login('REDACTED','REDACTED')
        ftp.login('REDACTED','REDACTED')
        ftp.put_Ssl(True)
        #ftp.cwd('usfs')
        storcmd = str("STOR " + fname)
        ftp.storlines(storcmd, open(logcmd, 'ra'))
        ftp.close()
    elif ftime == '1045':
        #ftp = FTP('REDACTED')
        ftp = FTP('REDACTED')
        #ftp.login('REDACTED','REDACTED')
        ftp.login('REDACTED','REDACTED')
        ftp.put_Ssl(True)
        #ftp.cwd('usfs')
        storcmd = str("STOR " + fname)
        ftp.storlines(storcmd, open(logcmd, 'ra'))
        ftp.close()
    return render(request,'fastrax/transfer.html', {'adate': adate, 'muntil': muntil, 'fdate': fdate, 'ftime': ftime, 'fname': fname, 'url': url, 'logcmd': logcmd, 'storcmd': storcmd, 'd0445': d0445, 'd1045': d1045, 'n0445': n0445, 'test1': test1, 'test2': test2, 'test3': test3, },)

@login_required
@permission_required('fastrax.add_smokeregister')
def tndnregister2(request, tn, dn):
    adate = datetime.datetime.now().year
    yy = datetime.datetime.now().strftime("%y")
    ayear = adate - 1
    iyear = datetime.date(ayear,1,1)
    dreg_list = SmokeRegister.objects.filter(
        Q(regdate__gte=iyear),
        Q(district__slug__iexact=dn)
        ).order_by('sn')
    if request.method == 'POST':
        dtla = District.objects.filter(tla=tn)[:1]
        ddistrict = District.objects.filter(slug=dn)[:1]
        reg_list = SmokeRegister.objects.filter(
            Q(regdate__gte=iyear),
            Q(district__slug__iexact=dn)
            ).order_by('sn')
        did = u"%s" % (ddistrict[0].pk)
        form = SmokeRegisterFormSN2(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.author = request.user
            obj.district = ddistrict[0]
            polys = ODFSSRA.objects.all()
            poly1 = polys[0].geometry
            poly1.transform(2991)
            regt = u"%s" % (obj.township.upper())
            regt = u"%s" % (obj.township.upper())
            regr = u"%s" % (obj.range.upper())
            regs = u"%s" % (obj.section.zfill(2))
            trsr = PLSS.objects.filter(
                Q(township__exact=regt),
                Q(range__exact=regr),
                Q(section__iexact=regs)
                ).order_by('township')[:1]
            if trsr:
                mix = u"%s" % (trsr[0].mix)
                miy = u"%s" % (trsr[0].miy)
                max = u"%s" % (trsr[0].max)
                may = u"%s" % (trsr[0].may)
                minx = float(mix)
                miny = float(miy)
                maxx = float(max)
                maxy = float(may)
                nw = geos.Point(minx, maxy, srid=4326)
                ne = geos.Point(maxx, maxy, srid=4326)
                se = geos.Point(maxx, miny, srid=4326)
                sw = geos.Point(minx, miny, srid=4326)
                nw.transform(2991) 
                ne.transform(2991) 
                se.transform(2991) 
                sw.transform(2991) 
                obj.mix = minx
                obj.miy = miny
                obj.max = maxx
                obj.may = maxy
                bp = geos.Polygon( ((minx, maxy), (maxx, maxy), (maxx, miny), (minx, miny), (minx, maxy)), srid=4326)
                #pnt1 = geos.Point(-122.65, 45.60, srid=4326)
                pnt1 = bp
                pnt1.transform(2991) 
                #dp1nw = D(m=nw.distance(pnt1)).mi
                #dp1ne = D(m=ne.distance(pnt1)).mi
                #dp1se = D(m=se.distance(pnt1)).mi
                #dp1sw = D(m=sw.distance(pnt1)).mi
                #dp1p2 = min(dp1nw,dp1ne,dp1se,dp1sw)
                dssra = 90
                obj.ssra = 'None'
                for poly in polys:
                    poly1 = poly.geometry
                    poly1.transform(2991) 
                    d2 = D(m=poly1.distance(pnt1)).mi
                    obj.dssra = dssra
                    if d2 <= dssra:
                        dssra = d2
                        obj.ssra = poly.name
                        obj.dssra = dssra
                        poly1.transform(4326) 
                        obj.poly = poly1
                        obj.gpoly = GPolygon(obj.poly).points
                        obj.gpoly = GPolygon(obj.poly).points
                obj.ssradistance = 60
                if obj.dssra <= 60:
                    obj.ssradistance = str(int(obj.dssra))
                #dp1p2 = D(m=ODFSSRA.objects.distance(poly1)).mi
                #obj.dp1p2 = dp1p2
                pnt1.transform(4326) 
                obj.pnt1 = pnt1
                mx = str((minx + maxx)/2)
                my = str((miny + maxy)/2)
                url = "http://imsdemo.cr.usgs.gov/xmlwebservices2/elevation_service.asmx/getElevation?X_Value=" + mix +"&Y_Value=" + miy + "&Elevation_Units=FEET&Source_Layer=-1&Elevation_Only=true"
                url = "http://ned.usgs.gov/epqs/pqs.php?x=" + mix +"&y=" + miy + "&units=Feet&10&y=10&units=Feet&output=xml"
                #response = minidom.parse(urllib.request.urlopen(url))
                #nlist = response.childNodes
                #double = nlist[0].firstChild.data
                #uelev = response.getElementsByTagName("double")
                #obj.elevation = int(Decimal(double))
            if obj.revenue:
                #sn = 10 + 999 + revenue + 01
                odf = ddistrict[0].nnn
                if odf.endswith('XX'):
                    odf = obj.fpf
                revenue = obj.revenue
                base = u"%s%3s%05s" % (yy, odf, revenue)
                base_list = SmokeRegister.objects.filter(sn__startswith=base).order_by('sn')
                seq = 1
                if base_list:
                    seq = base_list.count()
                    #seq = base_list[0].sn[10:12]
                    seq = int(seq)+1
                    seq = int(str(seq)[-2:])
                obj.sn = u"%s%3s%05s%02d" % (yy, odf, revenue, seq)
                sn_list = SmokeRegister.objects.filter(sn__iexact=obj.sn).order_by('sn')
                if sn_list:
                    base_list = SmokeRegister.objects.filter(sn__startswith=base).order_by('-sn')[:1]
                    seq = 1
                    if base_list:
                        seq = base_list.count()
                        #seq = base_list[0].sn[10:12]
                        seq = int(seq)+1
                        seq = int(str(seq)[-2:])
                    obj.sn = u"%s%3s%05s%02d" % (yy, odf, revenue, seq)
                
            else:
                #sn = 10 + 406 + 99900 + 01
                odf = 406
                odfid = ddistrict[0].odfid
                odfid = int(odfid)
                base = u"%s%3s%05d" % (yy, odf, odfid)
                base_list = SmokeRegister.objects.filter(sn__startswith=base).order_by('sn')
                seq = 1
                if base_list:
                    #seq = base_list[0].sn[10:12]
                    seq = base_list.count()
                    if seq != 99:
                        seq = int(seq)+1
                    seq = int(str(seq)[-2:])
                obj.sn = u"%s%3s%05d%02d" % (yy, odf, odfid, seq)
                hold1 = obj.sn
                #obj.regname = u"%s%3s%05d%02d" % (yy, odf, odfid, seq)
                #obj.sn = 'TESTTEST0000' #104060110099
                sn_list = SmokeRegister.objects.filter(sn__iexact=obj.sn).order_by('sn')
                if sn_list: # 0001-0000 skipped numbers
                    base_list = SmokeRegister.objects.filter(sn__startswith=base).order_by('-sn')[:1]
                    seq = 1
                    if base_list:
                        seq = base_list[0].sn[10:12]
                        if seq != 99:
                            seq = int(seq)+1
                        seq = int(str(seq)[-2:])
                    obj.sn = u"%s%3s%05d%02d" % (yy, odf, odfid, seq)
                    #obj.regname = u"%s%3s%05d%02d" % (yy, odf, odfid, seq)
                    #obj.regname = hold1
                    #obj.sn = 'TESTTEST0001' #1040601100100 - seq of 100 to long, slice it
                    sn_list = SmokeRegister.objects.filter(sn__iexact=obj.sn).order_by('sn')
                    if sn_list: # 0101-0100 second hundred
                        odfid = ddistrict[0].odfid
                        odfid = int(odfid)+1
                        base = u"%s%3s%05d" % (yy, odf, odfid)
                        base_list = SmokeRegister.objects.filter(sn__startswith=base).order_by('-sn')
                        seq = 1
                        if base_list:
                            seq = base_list.count()
                            #seq = base_list[0].sn[10:12]
                            if seq != 99:
                                seq = int(seq)+1
                            seq = int(str(seq)[-2:])
                        obj.sn = u"%s%3s%05d%02d" % (yy, odf, odfid, seq)
                        #obj.regname = u"%s%3s%05d%02d" % (yy, odf, odfid, seq)
                        #obj.regname = hold1
                        #obj.sn = 'TESTTEST0002' #10406 110101 - missing leading zero in odfid, pad it
                        sn_list = SmokeRegister.objects.filter(sn__iexact=obj.sn).order_by('sn')
                        if sn_list: # 0201-0200 third hundred
                            odfid = ddistrict[0].odfid
                            odfid = int(odfid)+1
                            base = u"%s%3s%05d" % (yy, odf, odfid)
                            base_list = SmokeRegister.objects.filter(sn__startswith=base).order_by('-sn')
                            seq = 1
                            if base_list:
                                seq = base_list.count()
                                #seq = base_list[0].sn[10:12]
                                if seq != 99:
                                    seq = int(seq)+1
                                seq = int(str(seq)[-2:])
                            obj.sn = u"%s%3s%05d%02d" % (yy, odf, odfid, seq)
                            sn_list = SmokeRegister.objects.filter(sn__iexact=obj.sn).order_by('sn')
                            if sn_list: #0301-0300 fourth hundred
                                odfid = ddistrict[0].odfid
                                odfid = int(odfid)+1
                                base = u"%s%3s%05d" % (yy, odf, odfid)
                                base_list = SmokeRegister.objects.filter(sn__startswith=base).order_by('-sn')
                                seq = 1
                                if base_list:
                                    seq = base_list.count()
                                    #seq = base_list[0].sn[10:12]
                                    if seq != 99:
                                        seq = int(seq)+1
                                    seq = int(str(seq)[-2:])
                                obj.sn = u"%s%3s%05s%02d" % (yy, odf, odfid, seq)
            obj.sequence = 66
            obj.save()
            return HttpResponseRedirect('/%s/' % (obj.sn))
    else:
        dtla = District.objects.filter(tla=tn)[:1]
        ddistrict = District.objects.filter(slug=dn)[:1]
        reg_list = SmokeRegister.objects.filter(
            Q(regdate__gte=iyear),
            Q(district__slug__iexact=dn)
            ).order_by('sn')
        did = u"%s" % (ddistrict[0].pk)
        dfpf = u"%s" % (ddistrict[0].nnn)
        data_dict = {'district': did, 'fpf': dfpf}
        form = SmokeRegisterFormSN2(initial=data_dict)

    return render(request,'fastrax/tndnregister2.html', {
        'form': form, 'reg_list': reg_list, 'dreg_list': dreg_list, 'ddistrict': ddistrict, 'dtla': dtla
    },)


def test(request, tn, dn):
    adate = datetime.datetime.now().year
    ayear = adate - 2
    iyear = datetime.date(ayear,1,1)
    dtla = District.objects.filter(tla=tn)[:1]
    ddistrict = District.objects.filter(slug=dn)[:1]
    reg_list = SmokeRegister.objects.filter(
        Q(regdate__gte=iyear),
        Q(district__slug__iexact=dn)
        ).order_by('sn')
    #polys = ODFSSRA.objects.filter(name__iexact='Bear Creek Rogue River Valley')[:1]
    polys = ODFSSRA.objects.all()
    poly1 = polys[0].geometry
    poly1.transform(2991) 
    for obj in reg_list:
        regt = u"%s" % (obj.township.upper())
        regt = u"%s" % (obj.township.upper())
        regr = u"%s" % (obj.range.upper())
        regs = u"%s" % (obj.section.zfill(2))
        trsr = PLSS.objects.filter(
            Q(township__exact=regt),
            Q(range__exact=regr),
            Q(section__iexact=regs)
            ).order_by('township')[:1]
        if trsr:
            mix = u"%s" % (trsr[0].mix)
            miy = u"%s" % (trsr[0].miy)
            max = u"%s" % (trsr[0].max)
            may = u"%s" % (trsr[0].may)
            minx = float(mix)
            miny = float(miy)
            maxx = float(max)
            maxy = float(may)
            nw = geos.Point(minx, maxy, srid=4326)
            ne = geos.Point(maxx, maxy, srid=4326)
            se = geos.Point(maxx, miny, srid=4326)
            sw = geos.Point(minx, miny, srid=4326)
            nw.transform(2991) 
            ne.transform(2991) 
            se.transform(2991) 
            sw.transform(2991) 
            obj.mix = minx
            obj.miy = miny
            obj.max = maxx
            obj.may = maxy
            bp = geos.Polygon( ((minx, maxy), (maxx, maxy), (maxx, miny), (minx, miny), (minx, maxy)), srid=4326)
            #pnt1 = geos.Point(-122.65, 45.60, srid=4326)
            pnt1 = bp
            pnt1.transform(2991) 
            #dp1nw = D(m=nw.distance(pnt1)).mi
            #dp1ne = D(m=ne.distance(pnt1)).mi
            #dp1se = D(m=se.distance(pnt1)).mi
            #dp1sw = D(m=sw.distance(pnt1)).mi
            #dp1p2 = min(dp1nw,dp1ne,dp1se,dp1sw)
            dssra = 9000
            obj.ssra = 'None'
            for poly in polys:
                poly1 = poly.geometry
                poly1.transform(2991) 
                d2 = D(m=poly1.distance(pnt1)).mi
                obj.dssra = dssra
                if d2 <= dssra:
                    dssra = d2
                    obj.ssra = poly.name
                    obj.dssra = dssra
                    poly1.transform(4326) 
                    obj.poly = poly1
                    obj.gpoly = GPolygon(obj.poly).points
            #dp1p2 = D(m=ODFSSRA.objects.distance(poly1)).mi
            #obj.dp1p2 = dp1p2
            pnt1.transform(4326) 
            obj.pnt1 = pnt1
            mx = str((minx + maxx)/2)
            my = str((miny + maxy)/2)
            url = "http://gisdata.usgs.gov/xmlwebservices2/elevation_service.asmx/getElevation?X_Value=" + mix +"&Y_Value=" + miy + "&Elevation_Units=FEET&Source_Layer=-1&Elevation_Only=true"
            response = minidom.parse(urllib.request.urlopen(url))
            nlist = response.childNodes
            double = nlist[0].firstChild.data
            #uelev = response.getElementsByTagName("double")
            obj.uelev = double
            #url2 = "http://maps.googleapis.com/maps/api/elevation/xml?locations=" + miy + "," + mix + "&sensor=false"
            #response2 = minidom.parse(urllib.urlopen(url2))
            #nlist = response2.childNodes
            #n2list = nlist[0].childNodes
            #n3list = n2list[3].childNodes
            #n4list = n3list[3].firstChild.data
            #obj.gelev = Decimal(n4list) * Decimal('3.2808399')
            obj.gelev = obj.uelev
    return render(request,'fastrax/test.html', {
                'tn': tn, 'dn': dn, 'reg_list': reg_list,
            })

