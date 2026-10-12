import os
import sys
import django
import joblib
import pandas as pd



# 1. Bootstrap Django environment
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'customerchurn.settings')
django.setup()

from accounts.models import Customers, ChurnPrediction



def fetch_active_customers():
    """Fetch active customers from PostgreSQL for inference."""
    print("Fetching customer data for inference...")
    
    # Query all customers and their related service/billing data
    queryset = Customers.objects.select_related(
        'services', 
        'billingaccounts', 
        'churnrecords'
    ).filter(is_archived=False)

    records = []
    for c in queryset:
        srv = getattr(c, 'services', None)
        bill = getattr(c, 'billingaccounts', None)
        
        # Skip records missing services or billing info
        if not (srv and bill):
            continue

        records.append({
            'customer_id': c.customer_id,
            'gender': c.gender,
            'senior_citizen': c.senior_citizen,
            'partner': c.partner,
            'dependents': c.dependents,
            'phone_service': srv.phone_service,
            'multiple_lines': srv.multiple_lines,
            'internet_service': srv.internet_service,
            'online_security': srv.online_security,
            'online_backup': srv.online_backup,
            'device_protection': srv.device_protection,
            'tech_support': srv.tech_support,
            'streaming_tv': srv.streaming_tv,
            'streaming_movies': srv.streaming_movies,
            'tenure': bill.tenure,
            'contract': bill.contract,
            'paperless_billing': bill.paperless_billing,
            'payment_method': bill.payment_method,
            'monthly_charges': float(bill.monthly_charges or 0.0),
            'total_charges': float(bill.total_charges or 0.0),
        })

    return pd.DataFrame(records)

def run_predictions():
    # 1. Load trained model pipeline
    model_path = os.path.join(os.path.dirname(__file__), 'churn_rf_pipeline.joblib')
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}. Run train.py first!")

    print("Loading saved Random Forest pipeline...")
    pipeline = joblib.load(model_path)

    # 2. Fetch customer data
    df = fetch_active_customers()
    if df.empty:
        print("No active customer records found.")
        return 0

    # 3. Extract features (drop ID column)
    X = df.drop(columns=['customer_id'])

    # 4. Predict probabilities (index 1 is the probability of Churn)
    print("Generating churn risk predictions...")
    churn_probabilities = pipeline.predict_proba(X)[:, 1]

    # 5. Bulk insert/update into PostgreSQL
    print("Saving predictions to PostgreSQL...")
    updated_count = 0

    for idx, row in df.iterrows():
        prob = float(churn_probabilities[idx])
        
        # Categorize risk levels
        if prob >= 0.70:
            risk_level = 'High'
        elif prob >= 0.35:
            risk_level = 'Medium'
        else:
            risk_level = 'Low'

        # Get customer instance
        customer_inst = Customers.objects.get(customer_id=row['customer_id'])

        # Update existing prediction or create a new row
        ChurnPrediction.objects.update_or_create(
            customer=customer_inst,
            defaults={
                'churn_probability': round(prob, 4),
                'risk_level': risk_level
            }
        )
        updated_count += 1

    print(f"Successfully processed and updated predictions for {updated_count} customers!")
    return updated_count


if __name__ == '__main__':
    run_predictions()