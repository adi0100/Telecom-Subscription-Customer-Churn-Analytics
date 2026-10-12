import os
import sys
import django
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
import joblib
from sklearn.metrics import classification_report, roc_auc_score

BASE_DIR=os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # 1. Locate the project root directory
sys.path.append(BASE_DIR) # 2.Add the root directory to python's module search path
os.environ.setdefault('DJANGO_SETTINGS_MODULE','customerchurn.settings') #3. Point to project's settings file

django.setup()

from accounts.models import Customers, BillingAccounts, Services, ChurnRecords

def load_data():
    print("Fetching records from PostgreSQL using SQL JOINs...")
    queryset = Customers.objects.select_related(
        'services', 
        'billingaccounts', 
        'churnrecords'
    ).all()
    
    records=[]
    for c in queryset:
        srv=getattr(c, 'services',None)
        bill=getattr(c, 'billingaccounts', None)
        churn=getattr(c, 'churnrecords', None)

        if not (srv and bill and churn):
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
            'churn_status': 1 if churn.churn_status.strip().lower() == 'yes' else 0
        })

    # Convert the list of merged dictionaries into a Pandas DataFrame
    df=pd.DataFrame(records)
    return df

def build_pipeline():
    # Define numerical vs categorical feature names
    numerical_cols = ['tenure', 'monthly_charges', 'total_charges', 'senior_citizen']
    
    # Categorical columns are all non-numeric columns except customer_id and churn_status
    categorical_cols = [
        'gender', 'partner', 'dependents', 'phone_service', 'multiple_lines',
        'internet_service', 'online_security', 'online_backup', 'device_protection',
        'tech_support', 'streaming_tv', 'streaming_movies', 'contract',
        'paperless_billing', 'payment_method'
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            ('num',StandardScaler(),numerical_cols),
            ('cat',OneHotEncoder(handle_unknown='ignore',drop='first'), categorical_cols)
        ]
    )

    pipeline = Pipeline(steps=[
        ('preprocessor',preprocessor),
        ('classifier',RandomForestClassifier(
            n_estimators=150,
            max_depth=10,
            min_samples_split=5,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        ))
    ])

    return pipeline

if __name__ == '__main__':
    # 1. Load merged dataset
    df = load_data()
    
    # 2. Separate Features (X) and Target (y)
    X = df.drop(columns=['customer_id', 'churn_status'])
    y = df['churn_status']

    # 3. Split: 90% Training, 10% Testing
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.10, random_state=42, stratify=y
    )

    print(f"Data split successfully! Training on {len(X_train)} rows, testing on {len(X_test)} rows.")

    # 4. Build and Train the Pipeline
    print("Training Random Forest model...")
    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    # 5. Evaluate on 10% Test Data
    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    print("\n--- Model Performance on 10% Test Data ---")
    print(classification_report(y_test, y_pred, target_names=['Retained (0)', 'Churned (1)']))
    print(f"ROC-AUC Score: {roc_auc_score(y_test, y_proba):.4f}")

    # 6. Save the Trained Model Pipeline
    model_path = os.path.join(os.path.dirname(__file__), 'churn_rf_pipeline.joblib')
    joblib.dump(pipeline, model_path)
    print(f"\nTrained model successfully saved to: {model_path}")