from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .models import Customers
from .forms import AgentCreationForm


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

@login_required(login_url='login')
def dashboard_view(request):
    return render(request, 'accounts/dashboard.html')


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
            messages.success(request, f'Agent "{agent.username}" was added.')
            return redirect('agent_list')

    return render(request, 'accounts/agent_list.html', {
        'agents': agents,
        'form': form,
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
    agent.delete()
    messages.success(request, f'Agent "{username}" was removed.')
    return redirect('agent_list')


@login_required(login_url='login')
def customer_list_view(request):
    search_query=request.GET.get('customer_id','').strip()
    churn_status=request.GET.get('churn_status','').strip()
    customers = Customers.objects.select_related(
        'billingaccounts',
        'churnrecords',
    ).order_by('customer_id')
    if search_query:
        customers=customers.filter(customer_id__iexact=search_query)
    if churn_status:
        customers=customers.filter(churnrecords__churn_status=churn_status)
    paginator = Paginator(customers, 50)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'accounts/customer_list.html', {
        'page_obj': page_obj,
        'search_query':search_query,
        'churn_status':churn_status,
        })


def logout_view(request):
    logout(request)
    return redirect('login')
