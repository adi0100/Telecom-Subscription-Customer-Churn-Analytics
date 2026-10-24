import random
from accounts.models import Customers, Services, BillingAccounts, ChurnRecords, ChurnPrediction

def run():
    genders = ['Male', 'Female']
    yes_no = ['Yes', 'No']
    contracts = ['Month-to-month', 'One year', 'Two year']
    internet_types = ['DSL', 'Fiber optic', 'No']
    payment_methods = ['Electronic check', 'Mailed check', 'Bank transfer', 'Credit card']

    print("Generating 100 sample records...")

    for i in range(1, 101):
        c_id = f"CUST-SIM-{i:03d}"
        
        # 1. Customer Profile
        customer, _ = Customers.objects.get_or_create(
            customer_id=c_id,
            defaults={
                'name': f"Customer {i}",
                'email': f"customer{i}@example.com",
                'gender': random.choice(genders),
                'senior_citizen': random.choice([0, 1]),
                'partner': random.choice(yes_no),
                'dependents': random.choice(yes_no),
            }
        )

        # 2. Services
        Services.objects.get_or_create(
            customer=customer,
            defaults={
                'phone_service': random.choice(yes_no),
                'multiple_lines': random.choice(yes_no),
                'internet_service': random.choice(internet_types),
                'online_security': random.choice(yes_no),
                'online_backup': random.choice(yes_no),
                'device_protection': random.choice(yes_no),
                'tech_support': random.choice(yes_no),
                'streaming_tv': random.choice(yes_no),
                'streaming_movies': random.choice(yes_no),
            }
        )

        # 3. Billing
        tenure_months = random.randint(1, 72)
        m_charges = round(random.uniform(20.0, 115.0), 2)
        BillingAccounts.objects.get_or_create(
            customer=customer,
            defaults={
                'tenure': tenure_months,
                'contract': random.choice(contracts),
                'paperless_billing': random.choice(yes_no),
                'payment_method': random.choice(payment_methods),
                'monthly_charges': m_charges,
                'total_charges': round(m_charges * tenure_months, 2),
            }
        )

        # 4. Churn & Risk Analytics
        churn_flag = random.choice(['Yes', 'No', 'No', 'No'])
        ChurnRecords.objects.get_or_create(
            customer=customer,
            defaults={'churn_status': churn_flag}
        )

        prob = round(random.uniform(0.6, 0.95), 2) if churn_flag == 'Yes' else round(random.uniform(0.05, 0.55), 2)
        risk = 'High' if prob > 0.7 else ('Medium' if prob > 0.3 else 'Low')
        
        ChurnPrediction.objects.get_or_create(
            customer=customer,
            defaults={
                'churn_probability': prob,
                'risk_level': risk,
                'top_factors': ['High Monthly Charges', 'Short Tenure'] if risk == 'High' else ['Long Contract']
            }
        )

    print("100 sample customers generated successfully!")

if __name__ == "__main__":
    run()