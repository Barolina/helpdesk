# -*- coding:utf-8 -*-
from models import CompanyPC, Company, CompanyAdmins, PcOptionListHistory, PcOptionsList, PcOptions
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView, FormView, CreateView
from django.views.generic.base import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.models import Group, User
from proj import settings
from Forms import ChangePcOptionForm, AddPcOptionForPCForm, AddCompanyPcForm, AddPcOptionsForm
from django.http import Http404


class GetPcFrom(ListView):
    """
    Предсталвение которое доет список селектов для аякса, обязательно должна пресудствовать группа company
    если пользователь в ней то приедосталяется список ПК в этой компании, если пользователь не компания,
    то список пуст
    """
    model = CompanyPC
    context_object_name = u'pc'
    template_name = u'ajax_pc_from.html'

    def get_queryset(self):
        try:
            self.user.groups.all().get(name = settings.COMPANY_GROUP_NAME)
            com      = Company.objects.get(com_user=self.user)
            queryset = CompanyPC.objects.filter(company=com)
        except Group.DoesNotExist, Company.DoesNotExist:
            queryset = Company.objects.none()
        return queryset

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.user = request.user
        return super(GetPcFrom, self).dispatch(request, *args, **kwargs)



class GetUserTo(ListView):
    """
    Представление возвращает список кому отправлять вопрос для аякса
    если это пользователь который состоит в группе company то возвращает
    админов данной компании, если это админ то показывает всех админов
    """
    model = User
    context_object_name = u'users'
    template_name = None
    template_for_company = u'ajax_users_to_for_company.html'
    template_for_admins = u'ajax_users_to_for_admins.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.user = request.user
        return super(GetUserTo, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        try:
            self.user.groups.all().get(name = settings.COMPANY_GROUP_NAME)
            self.user_group = settings.COMPANY_GROUP_NAME
            com = Company.objects.get(com_user=self.user)
            queryset = CompanyAdmins.objects.filter(company = com).order_by('username.id').distinct('username')
        except Group.DoesNotExist:
            queryset = User.objects.exclude(groups__name = settings.COMPANY_GROUP_NAME).exclude(username = settings.USER_MESS_FOR_ALL_COMPANY).exclude(username=self.user.username)
            self.user_group = None
        return queryset

    def get_template_names(self):
        if self.user_group:
            template = self.template_for_company
        else:
            template = self.template_for_admins
        return template


class GetCompanyTo(ListView):
    """
    представление которое возвращает список компаний которых данный админ курирует аякс
    """
    model = User
    context_object_name = u'companys'
    template_name = u'ajax_get_company_for_admin.html'
    user_for_all_company_choese = settings.USER_MESS_FOR_ALL_COMPANY
    block_for_all = False

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.user = request.user
        return super(GetCompanyTo, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        try:
            self.user.groups.all().get(name = settings.COMPANY_GROUP_NAME)
            queryset = CompanyAdmins.objects.none()
        except Group.DoesNotExist:
            queryset = CompanyAdmins.objects.filter(username=self.user).order_by('company.id').distinct('company')
            if not queryset:
                self.block_for_all = True
        return queryset

    def get_context_data(self, **kwargs):
        all_company = self.get_choese_for_all_company()
        context = super(GetCompanyTo, self).get_context_data(**kwargs)
        context['all'] = all_company
        context['block_for_all'] = self.block_for_all
        return context


    def get_choese_for_all_company(self):
        choese_all_user, created = User.objects.get_or_create(username=self.user_for_all_company_choese)
        return choese_all_user


class ChangePcOption(UpdateView):
    """
    Предсталение для формы изменения характеритики ПК
    """
    form_class = ChangePcOptionForm
    success_url = None
    template_name = 'change_pc_option.html'
    company_group = settings.COMPANY_GROUP_NAME
    model = PcOptionsList

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.user = request.user
        try:
            self.user.groups.all().get(name = self.company_group)
            raise Http404
        except Group.DoesNotExist:
            return super(ChangePcOption, self).dispatch(request, *args, **kwargs)


    def get_object(self, queryset=None):
        obj = super(ChangePcOption, self).get_object(queryset=None)
        self.pc = obj.pc.id
        return obj

    def get_success_url(self):
        url = u'/pc_detail/%s/' % (self.pc,)
        return url


    def get_context_data(self, **kwargs):
        context = super(ChangePcOption, self).get_context_data(**kwargs)
        context['user_is_company'] = False
        return context

    def form_valid(self, form):
        self.object.user = self.user
        pc      = self.object.pc
        option  = self.object.option
        body    = self.object.body
        user    = self.user
        new_row = PcOptionListHistory(pc = pc, option=option, body=body, user=user)
        new_row.save()
        return super(ChangePcOption, self).form_valid(form)



class PcList(TemplateView):
    """
    представление с выбором компании на нем и подгрузкой с другого
    представления аяксом список ПК для изменения
    """
    template_name = 'pc_list.html'
    company_group = settings.COMPANY_GROUP_NAME

    def is_user_group_company(self):
        try:
            self.user.groups.all().get(name=self.company_group)
            return True
        except Group.DoesNotExist:
            return False

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.user = request.user
        try:
            self.user.groups.all().get(name = self.company_group)
            raise Http404
        except Group.DoesNotExist:
            return super(PcList, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        user_is_company = self.is_user_group_company()
        context = super(PcList, self).get_context_data(**kwargs)
        context['user_is_company'] = user_is_company
        return context



class GetCompanyForPcList(GetCompanyTo):
    """
    Аякс предсталвение для отображения доступных компаний насдуется от списка из создания вопроса
    """

    def get_context_data(self, **kwargs):
        context = super(GetCompanyForPcList, self).get_context_data(**kwargs)
        context['block_for_all'] = True
        return context


class GetPcForPcList(ListView):
    """
    аякс представление для получения списка пк по выбранной фирме
    """
    template_name = 'ajax_get_pc_for_list.html'
    model = CompanyPC
    context_object_name = 'pc_list'
    pk_url_kwarg  = 'pk'
    company_group = settings.COMPANY_GROUP_NAME
    paginate_by = 40

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.user = request.user
        try:
            self.user.groups.all().get(name = self.company_group)
            raise Http404
        except Group.DoesNotExist:
            return super(GetPcForPcList, self).dispatch(request, *args, **kwargs)


    def get_queryset(self):
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        if pk is not None:
            try:
                company = Company.objects.get(com_user=pk)
            except Company.DoesNotExist:
                raise Http404
            queryset = CompanyPC.objects.filter(company=company)
            return queryset
        else:
            raise Http404


class PcDetail(ListView):
    """
    Представление для детализации информации о ПК
    """
    template_name = 'pc_detail.html'
    model = PcOptionsList
    context_object_name = 'options'
    company_group = settings.COMPANY_GROUP_NAME
    pk_url_kwarg  = 'pk'
    paginate_by = 40


    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.user = request.user
        try:
            self.user.groups.all().get(name = self.company_group)
            raise Http404
        except Group.DoesNotExist:
            return super(PcDetail, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        pk = self.get_pk()
        try:
            self.pc = CompanyPC.objects.get(pk = pk)
        except CompanyPC.DoesNotExist:
            raise Http404
        queryset = PcOptionsList.objects.filter(pc = self.pc)
        return queryset

    def get_pk(self):
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        if pk is not None:
            return pk
        else:
            raise Http404

    def get_context_data(self, **kwargs):
        context = super(PcDetail, self).get_context_data(**kwargs)
        context['pc'] = self.pc
        return context


class AddPcOption(FormView):
    """
    Представление для добавления характеристики к ПК
    """
    form_class = AddPcOptionForPCForm
    template_name = 'add_pc_option.html'
    success_url = None
    pk_url_kwarg  = 'pk'
    company_group = settings.COMPANY_GROUP_NAME


    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.user = request.user
        try:
            self.user.groups.all().get(name = self.company_group)
            raise Http404
        except Group.DoesNotExist:
            return super(AddPcOption, self).dispatch(request, *args, **kwargs)

    def get_pk(self):
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        if pk is not None:
            return pk
        else:
            raise Http404

    def get_parent_obj(self):
        pk = self.get_pk()
        try:
            obj = CompanyPC.objects.get(pk=pk)
        except CompanyPC.DoesNotExist:
            raise Http404
        return obj

    def form_valid(self, form):
        option  = form.cleaned_data['option']
        body    = form.cleaned_data['body']
        self.pc = self.get_parent_obj()
        user    = self.user
        new_option = PcOptionsList(
            pc = self.pc,
            option = option,
            body = body,
            user = user,
        )
        new_option.save()
        new_history_opt = PcOptionListHistory(
            pc = self.pc,
            option = option,
            body = body,
            user = user,
        )
        new_history_opt.save()
        return super(AddPcOption, self).form_valid(form)


    def get_success_url(self):
        url = u'/pc_detail/%s/' % (self.pc.id,)
        return url

    def get_context_data(self, **kwargs):
        context = super(AddPcOption, self).get_context_data(**kwargs)
        context['pc_pk'] = self.get_pk()
        return context



class GetOptionsForAdd(ListView):
    """
    Ajax представление для отображения списка доступных для создания характеристик ПК
    """
    template_name = 'ajax_get_options_for_add.html'
    pk_url_kwarg  = 'pk'
    company_group = settings.COMPANY_GROUP_NAME
    model = PcOptions
    context_object_name = 'options'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.user = request.user
        try:
            self.user.groups.all().get(name = self.company_group)
            raise Http404
        except Group.DoesNotExist:
            return super(GetOptionsForAdd, self).dispatch(request, *args, **kwargs)

    def get_pk(self):
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        if pk is not None:
            return pk
        else:
            raise Http404

    def get_queryset(self):
        pk          = self.get_pk()
        pc_options  = PcOptionsList.objects.filter(pc__id = pk).values_list('option')
        new_options = PcOptions.objects.exclude(id__in = pc_options)
        return new_options


class PcOptionHistoryView(ListView):
    """
    Предсталение для вывода истории по ПК
    """
    template_name = 'get_history_to_pc_options.html'
    pk_url_kwarg  = 'pk'
    company_group = settings.COMPANY_GROUP_NAME
    model = PcOptionListHistory
    context_object_name = 'options'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.user = request.user
        try:
            self.user.groups.all().get(name = self.company_group)
            raise Http404
        except Group.DoesNotExist:
            return super(PcOptionHistoryView, self).dispatch(request, *args, **kwargs)

    def get_pk(self):
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        if pk is not None:
            return pk
        else:
            raise Http404

    def get_queryset(self):
        pk = self.get_pk()
        try:
            self.pc = CompanyPC.objects.get(id = pk)
        except CompanyPC.DoesNotExist:
            raise Http404
        queryset = PcOptionListHistory.objects.filter(pc = self.pc)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(PcOptionHistoryView, self).get_context_data(**kwargs)
        context['pc'] = self.pc
        return context



class AddCompanyPcView(CreateView):
    """
    представление для добавления ПК
    """
    form_class = AddCompanyPcForm
    template_name = 'add_pc_to_company.html'
    success_url = None

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.user = request.user
        try:
            self.user.groups.all().get(name = settings.COMPANY_GROUP_NAME)
            raise Http404
        except Group.DoesNotExist:
            return super(AddCompanyPcView, self).dispatch(request, *args, **kwargs)


    def get_success_url(self):
        url = u'/pc_detail/%s/' % (self.object.id,)
        return url




class GetCompanyForPcAddView(ListView):
    """
    Ajax представление для получения списка компаний в представление по добавлению ПК
    """
    model = CompanyAdmins
    context_object_name = u'company_admins_list'
    template_name = 'ajax_get_company_for_pc_add.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.user = request.user
        try:
            self.user.groups.all().get(name = settings.COMPANY_GROUP_NAME)
            raise Http404
        except Group.DoesNotExist:
            return super(GetCompanyForPcAddView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = CompanyAdmins.objects.filter(username = self.user).order_by('company.id').distinct('company')
        return queryset


class AddPcOptionForAllView(CreateView):
    """
    Представление для добавления характеристики ПК
    """
    form_class = AddPcOptionsForm
    template_name = 'add_option_pc_for_all_pc.html'
    success_url = None
    pk_url_kwarg  = 'pk'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.user = request.user
        try:
            self.user.groups.all().get(name = settings.COMPANY_GROUP_NAME)
            raise Http404
        except Group.DoesNotExist:
            return super(AddPcOptionForAllView, self).dispatch(request, *args, **kwargs)

    def get_pk(self):
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        if pk is not None:
            return pk
        else:
            raise Http404

    def get_success_url(self):
        self.pk = self.get_pk()
        url = u'/add_opt/%s/' % (self.pk, )
        return url

    def get_context_data(self, **kwargs):
        self.pk = self.get_pk()
        context = super(AddPcOptionForAllView, self).get_context_data(**kwargs)
        context['pc_pk'] = self.pk
        return context




