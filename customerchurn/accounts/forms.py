from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import BillingAccounts, ChurnRecords, Customers, Services


User = get_user_model()


class AgentCreationForm(UserCreationForm):
    full_name = forms.CharField(max_length=150)
    email = forms.EmailField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'full_name', 'email')

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        name_parts = self.cleaned_data['full_name'].split(maxsplit=1)
        user.first_name = name_parts[0]
        user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        if commit:
            user.save()
        return user


class CustomerEmailForm(forms.Form):
    email = forms.EmailField(max_length=254, required=False)


class CustomerRecordForm(forms.Form):
    CONTRACT_CHOICES = [
        ('Month-to-month', 'Month-to-month'),
        ('One year', 'One year'),
        ('Two year', 'Two year'),
    ]
    YES_NO_CHOICES = [
        ('', '---------'),
        ('Yes', 'Yes'),
        ('No', 'No'),
    ]
    PHONE_CHOICES = [
        ('', '---------'),
        ('Yes', 'Yes'),
        ('No', 'No'),
    ]
    MULTIPLE_LINES_CHOICES = [
        ('', '---------'),
        ('No phone service', 'No phone service'),
        ('No', 'No'),
        ('Yes', 'Yes'),
    ]
    INTERNET_CHOICES = [
        ('', '---------'),
        ('DSL', 'DSL'),
        ('Fiber optic', 'Fiber optic'),
        ('No', 'No internet service'),
    ]
    INTERNET_SERVICE_CHOICES = [
        ('', '---------'),
        ('No internet service', 'No internet service'),
        ('No', 'No'),
        ('Yes', 'Yes'),
    ]
    PAYMENT_CHOICES = [
        ('', '---------'),
        ('Electronic check', 'Electronic check'),
        ('Mailed check', 'Mailed check'),
        ('Bank transfer (automatic)', 'Bank transfer (automatic)'),
        ('Credit card (automatic)', 'Credit card (automatic)'),
    ]
    CHURN_CHOICES = [
        ('No', 'Retained'),
        ('Yes', 'Churned'),
    ]

    name = forms.CharField(max_length=150, label='Customer name')
    email = forms.EmailField(max_length=254, required=False)
    gender = forms.ChoiceField(
        choices=[('', '---------'), ('Female', 'Female'), ('Male', 'Male')],
        required=False,
    )
    senior_citizen = forms.ChoiceField(
        choices=[('', '---------'), ('0', 'No'), ('1', 'Yes')],
        required=False,
        label='Senior citizen',
    )
    partner = forms.ChoiceField(choices=YES_NO_CHOICES, required=False)
    dependents = forms.ChoiceField(choices=YES_NO_CHOICES, required=False)
    contract = forms.ChoiceField(choices=[('', '---------'), *CONTRACT_CHOICES])
    tenure = forms.IntegerField(min_value=0, required=False, initial=0)
    monthly_charges = forms.DecimalField(max_digits=8, decimal_places=2, min_value=0)
    total_charges = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        required=False,
    )
    paperless_billing = forms.ChoiceField(choices=YES_NO_CHOICES, required=False)
    payment_method = forms.ChoiceField(choices=PAYMENT_CHOICES, required=False)
    phone_service = forms.ChoiceField(choices=PHONE_CHOICES, required=False)
    multiple_lines = forms.ChoiceField(choices=MULTIPLE_LINES_CHOICES, required=False)
    internet_service = forms.ChoiceField(choices=INTERNET_CHOICES, required=False)
    online_security = forms.ChoiceField(choices=INTERNET_SERVICE_CHOICES, required=False)
    online_backup = forms.ChoiceField(choices=INTERNET_SERVICE_CHOICES, required=False)
    device_protection = forms.ChoiceField(choices=INTERNET_SERVICE_CHOICES, required=False)
    tech_support = forms.ChoiceField(choices=INTERNET_SERVICE_CHOICES, required=False)
    streaming_tv = forms.ChoiceField(choices=INTERNET_SERVICE_CHOICES, required=False)
    streaming_movies = forms.ChoiceField(choices=INTERNET_SERVICE_CHOICES, required=False)
    churn_status = forms.ChoiceField(choices=CHURN_CHOICES, initial='No')

    def __init__(self, *args, instance=None, require_name=True, **kwargs):
        self.instance = instance
        self.require_name = require_name
        if instance is not None and 'initial' not in kwargs:
            initial = {
                field: getattr(instance, field, None)
                for field in (
                    'name',
                    'email',
                    'gender',
                    'senior_citizen',
                    'partner',
                    'dependents',
                )
            }
            billing = getattr(instance, 'billingaccounts', None)
            services = getattr(instance, 'services', None)
            churn = getattr(instance, 'churnrecords', None)
            if billing:
                initial.update({
                    field: getattr(billing, field)
                    for field in (
                        'contract',
                        'tenure',
                        'monthly_charges',
                        'total_charges',
                        'paperless_billing',
                        'payment_method',
                    )
                })
            if services:
                initial.update({
                    field: getattr(services, field)
                    for field in (
                        'phone_service',
                        'multiple_lines',
                        'internet_service',
                        'online_security',
                        'online_backup',
                        'device_protection',
                        'tech_support',
                        'streaming_tv',
                        'streaming_movies',
                    )
                })
            if churn:
                initial['churn_status'] = churn.churn_status
            kwargs['initial'] = initial
        super().__init__(*args, **kwargs)
        self.fields['name'].required = require_name
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def save(self, *, instance=None):
        data = self.cleaned_data
        instance = instance or self.instance
        if instance is None:
            instance = Customers()

        instance.name = data.get('name') or None
        instance.email = data.get('email') or None
        instance.gender = data.get('gender') or None
        instance.senior_citizen = data.get('senior_citizen') or None
        instance.partner = data.get('partner') or None
        instance.dependents = data.get('dependents') or None
        instance.save()

        BillingAccounts.objects.update_or_create(
            customer=instance,
            defaults={
                'contract': data['contract'],
                'tenure': data.get('tenure'),
                'monthly_charges': data['monthly_charges'],
                'total_charges': data.get('total_charges'),
                'paperless_billing': data.get('paperless_billing') or None,
                'payment_method': data.get('payment_method') or None,
            },
        )
        Services.objects.update_or_create(
            customer=instance,
            defaults={
                field: data.get(field) or None
                for field in (
                    'phone_service',
                    'multiple_lines',
                    'internet_service',
                    'online_security',
                    'online_backup',
                    'device_protection',
                    'tech_support',
                    'streaming_tv',
                    'streaming_movies',
                )
            },
        )
        ChurnRecords.objects.update_or_create(
            customer=instance,
            defaults={'churn_status': data['churn_status']},
        )
        return instance
