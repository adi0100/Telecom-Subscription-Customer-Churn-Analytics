from django.db import models


class SystemUsers(models.Model):
    user_id = models.AutoField(primary_key=True)
    user_name = models.CharField(max_length=100)
    email = models.CharField(unique=True, max_length=150)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'system_users'

    def __str__(self):
        return self.user_name


class Customers(models.Model):
    customer_id = models.CharField(primary_key=True, max_length=50)
    gender = models.CharField(max_length=10, blank=True, null=True)
    senior_citizen = models.SmallIntegerField(blank=True, null=True)
    partner = models.CharField(max_length=3, blank=True, null=True)
    dependents = models.CharField(max_length=3, blank=True, null=True)
    created_by_user = models.ForeignKey(SystemUsers, models.SET_NULL, db_column='created_by_user_id', blank=True, null=True)

    class Meta:
        managed = False
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
        managed = False
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
        managed = False
        db_table = 'billing_accounts'


class ChurnRecords(models.Model):
    churn_id = models.AutoField(primary_key=True)
    customer = models.OneToOneField(Customers, models.CASCADE, db_column='customer_id')
    churn_status = models.CharField(max_length=3)

    class Meta:
        managed = False
        db_table = 'churn_records'


class ChurnPrediction(models.Model):
    prediction_id = models.AutoField(primary_key=True)
    customer = models.OneToOneField(
        Customers,
        on_delete=models.CASCADE,
        db_column='customer_id',
        related_name='prediction'
    )
    churn_probability = models.FloatField()  # e.g., 0.782
    risk_level = models.CharField(max_length=10)  # 'Low', 'Medium', 'High'
    top_factors = models.JSONField(null=True, blank=True)  # List of primary risk drivers
    predicted_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True  # Managed by Django migrations
        db_table = 'churn_predictions'

    def __str__(self):
        return f"{self.customer_id} - {self.risk_level} ({self.churn_probability:.2%})"