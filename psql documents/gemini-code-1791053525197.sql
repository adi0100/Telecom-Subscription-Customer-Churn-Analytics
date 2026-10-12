-- 1. Create SYSTEM_USERS
CREATE TABLE system_users (
    user_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('DBA', 'Agent'))
);

-- 2. Create CUSTOMERS
CREATE TABLE customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(150),
    email VARCHAR(254),
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    gender VARCHAR(10),
    senior_citizen SMALLINT CHECK (senior_citizen IN (0, 1)),
    partner VARCHAR(3) CHECK (partner IN ('Yes', 'No')),
    dependents VARCHAR(3) CHECK (dependents IN ('Yes', 'No')),
    created_by_user_id INT,
    CONSTRAINT fk_cust_user FOREIGN KEY (created_by_user_id) 
        REFERENCES system_users(user_id) ON DELETE SET NULL
);

-- 3. Create SERVICES (1:1 with customers)
CREATE TABLE services (
    service_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL UNIQUE,
    phone_service VARCHAR(10),
    multiple_lines VARCHAR(25),
    internet_service VARCHAR(20),
    online_security VARCHAR(25),
    online_backup VARCHAR(25),
    device_protection VARCHAR(25),
    tech_support VARCHAR(25),
    streaming_tv VARCHAR(25),
    streaming_movies VARCHAR(25),
    CONSTRAINT fk_serv_cust FOREIGN KEY (customer_id) 
        REFERENCES customers(customer_id) ON DELETE CASCADE
);

-- 4. Create BILLING_ACCOUNTS (1:1 with customers)
CREATE TABLE billing_accounts (
    account_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL UNIQUE,
    tenure INT CHECK (tenure >= 0),
    contract VARCHAR(25),
    paperless_billing VARCHAR(3) CHECK (paperless_billing IN ('Yes', 'No')),
    payment_method VARCHAR(50),
    monthly_charges NUMERIC(8, 2),
    total_charges NUMERIC(10, 2),
    CONSTRAINT fk_bill_cust FOREIGN KEY (customer_id) 
        REFERENCES customers(customer_id) ON DELETE CASCADE
);

-- 5. Create CHURN_RECORDS (1:1 with customers)
CREATE TABLE churn_records (
    churn_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL UNIQUE,
    churn_status VARCHAR(3) NOT NULL CHECK (churn_status IN ('Yes', 'No')),
    CONSTRAINT fk_churn_cust FOREIGN KEY (customer_id) 
        REFERENCES customers(customer_id) ON DELETE CASCADE
);