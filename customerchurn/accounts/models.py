from django.db import models
from django.conf import settings
from uuid import uuid4


def generate_customer_id():
    return f'CUST-{uuid4().hex.upper()}'


class SystemUsers(models.Model):
    user_id = models.AutoField(primary_key=True)
    user_name = models.CharField(max_length=100)
    email = models.CharField(unique=True, max_length=150)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=20)

    class Meta:
        managed = True
        db_table = 'system_users'

    def __str__(self):
        return self.user_name


class Customers(models.Model):
    customer_id = models.CharField(
        primary_key=True,
        max_length=50,
        default=generate_customer_id,
    )
    name = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(max_length=254, blank=True, null=True)
    is_archived = models.BooleanField(default=False, db_default=False)
    gender = models.CharField(max_length=10, blank=True, null=True)
    senior_citizen = models.SmallIntegerField(blank=True, null=True)
    partner = models.CharField(max_length=3, blank=True, null=True)
    dependents = models.CharField(max_length=3, blank=True, null=True)
    created_by_user = models.ForeignKey(SystemUsers, models.SET_NULL, db_column='created_by_user_id', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'customers'

    def __str__(self):
        return self.customer_id


class Services(models.Model):
    service_id = models.AutoField(primary_key=True)
    customer = models.OneToOneField(Customers, models.CASCADE, db_column='customer_id')
    phone_service = models.CharField(max_length=10, blank=True, null=True)
    multiple_lines = models.CharField(max_length=25, blank=True, null=True)
    internet_service = models.CharField(max_length=20, blank=True, null=True)
    online_security = models.CharField(max_length=25, blank=True, null=True)
    online_backup = models.CharField(max_length=25, blank=True, null=True)
    device_protection = models.CharField(max_length=25, blank=True, null=True)
    tech_support = models.CharField(max_length=25, blank=True, null=True)
    streaming_tv = models.CharField(max_length=25, blank=True, null=True)
    streaming_movies = models.CharField(max_length=25, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'services'


class BillingAccounts(models.Model):
    account_id = models.AutoField(primary_key=True)
    customer = models.OneToOneField(Customers, models.CASCADE, db_column='customer_id')
    tenure = models.IntegerField(blank=True, null=True)
    contract = models.CharField(max_length=25, blank=True, null=True)
    paperless_billing = models.CharField(max_length=3, blank=True, null=True)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    monthly_charges = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    total_charges = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'billing_accounts'


class ChurnRecords(models.Model):
    churn_id = models.AutoField(primary_key=True)
    customer = models.OneToOneField(Customers, models.CASCADE, db_column='customer_id')
    churn_status = models.CharField(max_length=3)

    class Meta:
        managed = True
        db_table = 'churn_records'


class ChurnPrediction(models.Model):
    prediction_id = models.AutoField(primary_key=True)
    customer = models.OneToOneField(
        Customers,
        on_delete=models.CASCADE,
        db_column='customer_id',
        related_name='prediction'
    )
    churn_probability = models.FloatField()
    risk_level = models.CharField(max_length=10)
    top_factors = models.JSONField(null=True, blank=True)
    predicted_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'churn_predictions'

    def __str__(self):
        return f"{self.customer_id} - {self.risk_level} ({self.churn_probability:.2%})"


class AgentActivity(models.Model):
    ACTION_CHOICES = [
        ('email_updated', 'Customer email updated'),
        ('predictions_run', 'Churn predictions run'),
        ('customer_created', 'Customer record created'),
        ('customer_updated', 'Customer record updated'),
        ('customer_archived', 'Churned customer archived'),
        ('customer_restored', 'Customer restored'),
        ('agent_added', 'Agent added'),
        ('agent_removed', 'Agent removed'),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agent_activities',
    )
    actor_username = models.CharField(max_length=150)
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    customer_id = models.CharField(max_length=50, blank=True)
    details = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'agent_activities'
        ordering = ('-created_at', '-pk')

    def __str__(self):
        return f"{self.actor_username}: {self.get_action_display()}"