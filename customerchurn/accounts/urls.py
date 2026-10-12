from django.urls import path
from . import views

urlpatterns = [
    path('',views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('agents/', views.agent_list_view, name='agent_list'),
    path('agents/<int:user_id>/remove/', views.agent_remove_view, name='agent_remove'),
    path('customers/', views.customer_list_view, name='customer_list'),
    path('logout/',views.logout_view, name='logout'),
]