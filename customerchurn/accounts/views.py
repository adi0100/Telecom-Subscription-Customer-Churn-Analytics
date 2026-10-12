from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Q
from django.http import QueryDict
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.core.paginator import Paginator
from .models import AgentActivity, BillingAccounts, ChurnPrediction, ChurnRecords, Customers
from .forms import AgentCreationForm, CustomerEmailForm, CustomerRecordForm


AGENT_GROUP_NAME = 'Agents'
User = get_user_model()

# Create your views here.

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method=='POST':
        form=AuthenticationForm(request,data=request.POST)
        if form.is_valid():
            user=form.get_user()
            login(request,user)
            return redirect('dashboard')
    else:
        form=AuthenticationForm()
    return render(request,'accounts/login.html',{'form':form})


def _record_agent_activity(user, action, details, customer_id=''):
    AgentActivity.objects.create(
        actor=user,
        actor_username=user.get_username(),
        action=action,
        details=details,
        customer_id=customer_id,
    )


def _customer_list_redirect(request):
    query = QueryDict(mutable=True)
    for parameter in ('customer_id', 'risk_level', 'customer_state', 'page'):
        value = request.POST.get(parameter, '').strip()
        if value:
            query[parameter] = value
    url = reverse('customer_list')
    if query:
        url = f'{url}?{query.urlencode()}'
    return redirect(url)


@login_required(login_url='login')
def dashboard_view(request):
    active_customers = Customers.objects.filter(is_archived=False)
    customer_count = active_customers.count()
    churned_count = ChurnRecords.objects.filter(
        churn_status='Yes',
        customer__is_archived=False,
    ).count()
    retained_count = ChurnRecords.objects.filter(
        churn_status='No',
        customer__is_archived=False,
    ).count()
    labelled_count = churned_count + retained_count

    contract_stats = BillingAccounts.objects.filter(
        customer__churnrecords__isnull=False,
        customer__is_archived=False,
    ).values('contract').annotate(
        total=Count('account_id'),
        churned=Count('account_id', filter=Q(customer__churnrecords__churn_status='Yes')),
    ).order_by('contract')
    contract_chart_data = []
    for contract in contract_stats:
        contract_total = contract['total']
        contract_chart_data.append({
            'label': contract['contract'] or 'Unknown',
            'churn_rate': round(contract['churned'] / contract_total * 100, 1),
        })
    high_risk_contract = max(
        contract_chart_data,
        key=lambda contract: contract['churn_rate'],
        default=None,
    )

    risk_customers = ChurnPrediction.objects.filter(
        risk_level__in=('High', 'Medium'),
        customer__is_archived=False,
    ).select_related(
        'customer__billingaccounts',
        'customer__services',
    ).order_by('-churn_probability')[:4]

    return render(request, 'accounts/dashboard.html', {
        'customer_count': customer_count,
        'customer_count_display': f'{customer_count:,}',
        'churned_count': churned_count,
        'churned_count_display': f'{churned_count:,}',
        'retained_count': retained_count,
        'retained_count_display': f'{retained_count:,}',
        'churn_rate': round(churned_count / labelled_count * 100, 1) if labelled_count else None,
        'high_risk_contract': high_risk_contract,
        'contract_chart_data': contract_chart_data,
        'status_chart_data': [retained_count, churned_count],
        'risk_customers': risk_customers,
    })


@login_required(login_url='login')
def agent_list_view(request):
    if not request.user.is_superuser:
        raise PermissionDenied

    agent_group = Group.objects.filter(name=AGENT_GROUP_NAME).first()
    agents = User.objects.none()
    if agent_group:
        agents = agent_group.user_set.order_by('username')

    form = AgentCreationForm()
    if request.method == 'POST':
        form = AgentCreationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                agent = form.save()
                agent_group, _ = Group.objects.get_or_create(name=AGENT_GROUP_NAME)
                agent.groups.add(agent_group)
                _record_agent_activity(
                    request.user,
                    'agent_added',
                    f'Added agent account "{agent.username}".',
                )
            messages.success(request, f'Agent "{agent.username}" was added.')
            return redirect('agent_list')

    return render(request, 'accounts/agent_list.html', {
        'agents': agents,
        'form': form,
        'recent_activities': AgentActivity.objects.select_related('actor')[:25],
    })


@login_required(login_url='login')
@require_POST
def agent_remove_view(request, user_id):
    if not request.user.is_superuser:
        raise PermissionDenied

    agent_group = Group.objects.filter(name=AGENT_GROUP_NAME).first()
    if not agent_group:
        return redirect('agent_list')

    agent = get_object_or_404(
        agent_group.user_set,
        pk=user_id,
        is_superuser=False,
    )
    username = agent.username
    with transaction.atomic():
        _record_agent_activity(
            request.user,
            'agent_removed',
            f'Removed agent account "{username}".',
        )
        agent.delete()
    messages.success(request, f'Agent "{username}" was removed.')
    return redirect('agent_list')


@login_required(login_url='login')
def customer_list_view(request):
    search_query=request.GET.get('customer_id','').strip()
    risk_level=request.GET.get('risk_level','').strip()
    customer_state=request.GET.get('customer_state','active').strip()
    if customer_state not in ('active', 'archived'):
        customer_state = 'active'
    customers = Customers.objects.select_related(
        'billingaccounts',
        'churnrecords',
        'prediction',
    ).order_by('customer_id')
    customers = customers.filter(is_archived=(customer_state == 'archived'))
    if search_query:
        customers=customers.filter(customer_id__iexact=search_query)
    if risk_level in ('High', 'Medium', 'Low'):
        customers=customers.filter(prediction__risk_level=risk_level)
    elif risk_level == 'unpredicted':
        customers=customers.filter(prediction__isnull=True)
    else:
        risk_level = ''
    paginator = Paginator(customers, 50)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'accounts/customer_list.html', {
        'page_obj': page_obj,
        'search_query':search_query,
        'risk_level':risk_level,
        'customer_state':customer_state,
        'risk_levels': [
            ('', 'All risk levels'),
            ('High', 'High'),
            ('Medium', 'Medium'),
            ('Low', 'Low'),
            ('unpredicted', 'Not predicted'),
        ],
        })


@login_required(login_url='login')
def customer_create_view(request):
    if request.method == 'POST':
        form = CustomerRecordForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                customer = form.save()
                _record_agent_activity(
                    request.user,
                    'customer_created',
                    f'Created customer record for {customer.name} ({customer.customer_id}).',
                    customer.customer_id,
                )
            messages.success(request, f'Customer {customer.customer_id} was added.')
            return redirect('customer_list')
    else:
        form = CustomerRecordForm()

    return render(request, 'accounts/customer_form.html', {
        'form': form,
        'page_title': 'Add customer',
        'submit_label': 'Add customer',
        'cancel_url': reverse('customer_list'),
    })


@login_required(login_url='login')
def customer_edit_view(request, customer_id):
    customer = get_object_or_404(Customers, pk=customer_id)
    if request.method == 'POST':
        form = CustomerRecordForm(
            request.POST,
            instance=customer,
            require_name=False,
        )
        if form.is_valid():
            with transaction.atomic():
                customer = form.save()
                _record_agent_activity(
                    request.user,
                    'customer_updated',
                    f'Updated customer record for {customer.name or customer.customer_id}.',
                    customer.customer_id,
                )
            messages.success(request, f'Customer {customer.customer_id} was updated.')
            return redirect('customer_list')
    else:
        form = CustomerRecordForm(instance=customer, require_name=False)

    return render(request, 'accounts/customer_form.html', {
        'form': form,
        'page_title': f'Edit customer {customer.customer_id}',
        'submit_label': 'Save changes',
        'cancel_url': reverse('customer_list'),
    })


@login_required(login_url='login')
@require_POST
def customer_email_update_view(request, customer_id):
    customer = get_object_or_404(Customers, pk=customer_id)
    form = CustomerEmailForm(request.POST)
    if form.is_valid():
        with transaction.atomic():
            customer.email = form.cleaned_data['email'] or None
            customer.save(update_fields=['email'])
            _record_agent_activity(
                request.user,
                'email_updated',
                f'Updated the contact email for customer {customer.customer_id}.',
                customer.customer_id,
            )
        messages.success(request, f'Email updated for customer {customer.customer_id}.')
    else:
        messages.error(request, form.errors['email'][0])

    return _customer_list_redirect(request)


@login_required(login_url='login')
@require_POST
def customer_archive_view(request, customer_id):
    customer = get_object_or_404(
        Customers.objects.select_related('churnrecords'),
        pk=customer_id,
        is_archived=False,
    )
    if not hasattr(customer, 'churnrecords') or customer.churnrecords.churn_status != 'Yes':
        messages.error(request, 'Only churned customers can be archived.')
        return _customer_list_redirect(request)

    with transaction.atomic():
        customer.is_archived = True
        customer.save(update_fields=['is_archived'])
        _record_agent_activity(
            request.user,
            'customer_archived',
            f'Archived churned customer {customer.customer_id}.',
            customer.customer_id,
        )
    messages.success(
        request,
        f'Customer {customer.customer_id} was archived. Their records remain available.',
    )
    return _customer_list_redirect(request)


@login_required(login_url='login')
@require_POST
def customer_restore_view(request, customer_id):
    customer = get_object_or_404(Customers, pk=customer_id, is_archived=True)
    with transaction.atomic():
        customer.is_archived = False
        customer.save(update_fields=['is_archived'])
        _record_agent_activity(
            request.user,
            'customer_restored',
            f'Restored customer {customer.customer_id} from the archive.',
            customer.customer_id,
        )
    messages.success(request, f'Customer {customer.customer_id} was restored.')
    return _customer_list_redirect(request)


@login_required(login_url='login')
def agent_activity_view(request):
    activities = AgentActivity.objects.select_related('actor')
    agent_filter = ''
    agents = User.objects.none()
    if request.user.is_superuser:
        agent_group = Group.objects.filter(name=AGENT_GROUP_NAME).first()
        if agent_group:
            agents = agent_group.user_set.order_by('username')
        agent_filter = request.GET.get('agent_id', '').strip()
        if agent_filter.isdigit():
            activities = activities.filter(actor_id=int(agent_filter))
        else:
            agent_filter = ''
    else:
        activities = activities.filter(actor=request.user)

    paginator = Paginator(activities, 50)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'accounts/agent_activity.html', {
        'page_obj': page_obj,
        'agents': agents,
        'agent_filter': agent_filter,
        'is_admin': request.user.is_superuser,
    })


def logout_view(request):
    logout(request)
    return redirect('login')
