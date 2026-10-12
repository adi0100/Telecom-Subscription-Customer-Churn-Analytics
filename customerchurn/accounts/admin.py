from django.contrib import admin
from .models import Customers, Services, BillingAccounts, ChurnRecords, SystemUsers


class ServicesInline(admin.StackedInline):
    model = Services
    can_delete = False


class BillingAccountsInline(admin.StackedInline):
    model = BillingAccounts
    can_delete = False


class ChurnRecordsInline(admin.StackedInline):
    model = ChurnRecords
    can_delete = False


@admin.register(Customers)
class CustomersAdmin(admin.ModelAdmin):
    list_display = ('customer_id', 'gender', 'senior_citizen', 'partner', 'dependents')
    search_fields = ('customer_id',)
    list_filter = ('gender', 'partner', 'dependents')
    inlines = [ServicesInline, BillingAccountsInline, ChurnRecordsInline]


@admin.register(BillingAccounts)
class BillingAccountsAdmin(admin.ModelAdmin):
    list_display = ('customer', 'contract', 'monthly_charges', 'total_charges', 'payment_method')
    list_filter = ('contract', 'payment_method')
    search_fields = ('customer__customer_id',)


@admin.register(ChurnRecords)
class ChurnRecordsAdmin(admin.ModelAdmin):
    list_display = ('customer', 'churn_status')
    list_filter = ('churn_status',)
    search_fields = ('customer__customer_id',)


admin.site.register(Services)
admin.site.register(SystemUsers)