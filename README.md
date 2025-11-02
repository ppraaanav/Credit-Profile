Credit Profile for E-Commerce Customers (Django + DRF)

A minimal Django REST API to build and analyze credit profiles for e-commerce customers. It ingests orders and payments, computes features, and generates a rule-based credit score and risk band.

Quickstart

1) Create and activate virtualenv
```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
```

2) Install dependencies
```powershell
pip install -r requirements.txt
```

3) Create database and superuser
```powershell
python manage.py migrate
python manage.py createsuperuser
```

4) Run server
```powershell
python manage.py runserver
```

Open `http://127.0.0.1:8000/admin/` for the admin and `http://127.0.0.1:8000/api/` for the API.

API

- POST /api/customers/ create a customer
- GET /api/customers/ list customers
- POST /api/customers/{id}/recompute-score/ recompute credit score
- GET /api/customers/{id}/credit-profile/ get credit profile
- POST /api/orders/ create an order
- POST /api/payments/ create a payment
- GET /api/credit-profiles/ list profiles

Example payloads:
```json
POST /api/customers/
{
  "full_name": "Jane Doe",
  "email": "jane@example.com",
  "phone": "+123456789"
}
```
```json
POST /api/orders/
{
  "customer": "<customer_uuid>",
  "amount": "249.99",
  "status": "delivered"
}
```
```json
POST /api/payments/
{
  "customer": "<customer_uuid>",
  "order": 1,
  "method": "card",
  "success": true,
  "amount": "249.99"
}
```

Scoring

A simple rule-based score (300-1000): rewards total spend, delivered orders, and AOV; penalizes return rate, failed payment rate, and COD usage. Bands: A (>=800), B (>=700), C (>=600), D (>=500), E (<500).

Recompute all scores
```powershell
python manage.py recompute_scores
```

Seed sample data (10–15 customers with orders and payments)
```powershell
python manage.py seed_sample_data --count 12
```
Run it after migrate to quickly populate the dashboards and customer pages. You can adjust the count (10–50 allowed).

Tech

- Django 5.x, Django REST Framework
- SQLite by default

Authentication & Permissions

- Web login: `http://127.0.0.1:8000/accounts/login/` (use your Django superuser or staff user)
- API Token: obtain via `POST /api/token/` with JSON body `{ "username": "...", "password": "..." }` → returns `{ "token": "..." }`
- Use the token with header: `Authorization: Token <token>`
- Permissions:
  - Authenticated users: can view data (read-only)
  - Staff users: can create/update orders/payments/customers and recompute scores

Frontend pages

- `/` Customers list (login required)
- `/customers/<uuid>/` Customer detail + Recompute (staff only for recompute)
- `/dashboard/` Manager dashboard with metrics and chart
- `/customers/<uuid>/credit-report.pdf` Download PDF credit report


