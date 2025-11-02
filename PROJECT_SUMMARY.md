Project Summary: Credit Profile for E-Commerce Customers (Django + DRF)

What was built

- A Django + Django REST Framework backend to create and analyze credit profiles for e-commerce customers.
- Models for `Customer`, `Order`, `Payment`, and `CreditProfile` with admin integration.
- A rule-based credit scoring engine that extracts behavioral features (spend, returns, payment failures, COD usage) and assigns a score (300–1000) and a risk band (A–E).
- REST API endpoints to manage customers, orders, payments, and to view/recompute credit profiles.
- A management command to recompute all customer scores in bulk.

Tech stack

- Python, Django 5.x, Django REST Framework 3.16.x
- SQLite (default), easily switchable via Django settings

Key files and modules

- manage.py — Django entrypoint
- config/settings.py — Project settings (apps, DB, DRF, static)
- config/urls.py — Root URLs (`/admin/`, `/api/`)
- profiles/models.py — `Customer`, `Order`, `Payment`, `CreditProfile`
- profiles/admin.py — Admin registrations and lists
- profiles/serializers.py — DRF serializers for all models
- profiles/views.py — DRF viewsets + custom actions
- profiles/urls.py — DRF router for API endpoints
- profiles/services/credit_scoring.py — Feature extraction + scorecard logic
- profiles/management/commands/recompute_scores.py — Bulk recompute scores

Data model

- Customer: UUID id, name, email, phone
- Order: customer, amount, status (placed/shipped/delivered/cancelled/returned)
- Payment: customer, optional order, method (card/cod/wallet/bank), success, amount
- CreditProfile: one-to-one with customer, score, risk band, extracted features (JSON)

Scoring logic (rule-based)

- Starts from 600 baseline; rewards total spend, delivered orders, and average order value.
- Penalizes return rate, failed payment rate, and frequent COD usage.
- Clamps final score to 300–1000 and maps to bands: A (≥800), B (≥700), C (≥600), D (≥500), E (<500).

API endpoints (JSON)

- POST /api/customers/ — Create customer
- GET /api/customers/ — List customers
- GET /api/customers/{id}/ — Retrieve customer
- POST /api/customers/{id}/recompute-score/ — Recompute this customer’s credit score
- GET /api/customers/{id}/credit-profile/ — Get this customer’s credit profile
- POST /api/orders/ — Create order
- POST /api/payments/ — Create payment
- GET /api/credit-profiles/ — List credit profiles

How to run locally (Windows PowerShell)

1) Create and activate virtual env
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Install dependencies
```powershell
pip install -r requirements.txt
```

3) Migrate database and create admin
```powershell
python manage.py migrate
python manage.py createsuperuser
```

4) Start server
```powershell
python manage.py runserver
```

Open: http://127.0.0.1:8000/admin/ (admin) and http://127.0.0.1:8000/api/ (API)

Recompute all scores

```powershell
python manage.py recompute_scores
```

Next steps (optional)

- Replace rule-based scoring with an ML model (train on historical outcomes).
- Add authentication/permissions to protect endpoints.
- Add rate limiting and audit logging for score recomputations.
- Integrate external bureaus or risk signals if available.


