# HoldOn — Telecom Subscription Customer Churn Analytics

**HoldOn** is an end-to-end customer retention intelligence platform designed for telecom providers. It predicts customer churn risks using machine learning, classifies risk segments (High, Medium, Low), and provides actionable customer retention analytics through an interactive dashboard.

---

## 🌟 Key Features

* **Churn Risk Analytics:** Tracks total customers, active churn rates, and high-risk segments in real-time.
* **Predictive Insights:** Calculates individual churn probability and highlights key risk drivers (e.g., short tenure, high monthly charges).
* **Customer Management:** Full management of customer profiles, billing accounts, and service subscriptions.
* **Agent Activity Logging:** Audit trails tracking operational actions taken by agents.
* **Dockerized Infrastructure:** Containerized with Gunicorn for consistent local development and cloud production deployment.
* **Cloud Database Support:** Integrated with **Neon PostgreSQL** managed cloud database via `DATABASE_URL`.

---

## 🛠️ Tech Stack

* **Backend:** Python 3.10+, Django 5.x
* **Database:** PostgreSQL (Neon Cloud DB) / SQLite (Local fallback)
* **Frontend:** HTML5, CSS3, JavaScript, Bootstrap
* **Containerization:** Docker & Gunicorn
* **Deployment Platform:** Render

---

## 📁 Database Schema Highlights

* **`SystemUsers`**: Application role & access management.
* **`Customers`**: Core demographic and customer record profiles.
* **`Services`**: Phone, internet, streaming, and technical support service plans.
* **`BillingAccounts`**: Contract types, payment methods, monthly charges, and tenure tracking.
* **`ChurnRecords` & `ChurnPrediction`**: Churn flags, probability scoring, and risk driver breakdowns.
* **`AgentActivity`**: Operational activity logging for retention agents.

## RENDER URL :  https://telecom-churn-analytics.onrender.com
