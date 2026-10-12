from django.urls import path
from . import views

urlpatterns = [
    path('',views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('agents/', views.agent_list_view, name='agent_list'),
    path('agents/<int:user_id>/remove/', views.agent_remove_view, name='agent_remove'),
    path('agent-activity/', views.agent_activity_view, name='agent_activity'),
    path('customers/', views.customer_list_view, name='customer_list'),
    path('customers/add/', views.customer_create_view, name='customer_create'),
    path('customers/<str:customer_id>/edit/', views.customer_edit_view, name='customer_edit'),
    path('customers/<str:customer_id>/email/', views.customer_email_update_view, name='customer_email_update'),
    path('customers/<str:customer_id>/archive/', views.customer_archive_view, name='customer_archive'),
    path('customers/<str:customer_id>/restore/', views.customer_restore_view, name='customer_restore'),
    path('logout/',views.logout_view, name='logout'),
]