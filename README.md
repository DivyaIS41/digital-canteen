# Digital Canteen Automation System

Digital Canteen is a Flask prototype with two web experiences:

- `student_app.py` for students to browse the menu, manage a cart, and place orders
- `admin_app.py` for staff to manage menu items, pricing, daily specials, discounts, and order status

For a free demo deployment, this repo is now set up for:

- `Render` free web service for hosting
- `Aiven` free MySQL for persistent database storage

## Architecture

- Backend: Flask
- Database: MySQL
- Templates: Jinja2
- Production server: Gunicorn
- Deployment shape: one Render web service serving both apps through `combined_wsgi.py`

## Local Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and fill in your values:

```bash
copy .env.example .env
```

Required values:

- `FLASK_SECRET_KEY`
- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `WALLET_PIN`

Optional database TLS values:

- `DB_SSL_MODE`
- `DB_SSL_CA`

### 3. Create the MySQL schema and seed data

Once your MySQL database exists and your `.env` points to it:

```bash
python init_mysql_db.py
```

This applies `schema.sql` and loads sample demo data from `seed.sql`.

### 4. Run both apps locally

Student app:

```bash
python student_app.py
```

Admin app:

```bash
python admin_app.py
```

Default local URLs:

- Student app: `http://127.0.0.1:5000`
- Admin app: `http://127.0.0.1:5001/admin/login`

## Free Demo Deployment

This repo is now structured for a free demo using one Render web service and one free Aiven MySQL database.

### Demo URLs after deploy

- Student app: `https://your-service.onrender.com/`
- Admin app: `https://your-service.onrender.com/staff/admin/login`
- Student health: `https://your-service.onrender.com/health`
- Admin health: `https://your-service.onrender.com/staff/health`

### Render setup

1. Push this repository to GitHub.
2. Create a free MySQL service in Aiven.
3. Copy the Aiven connection values into Render environment variables.
4. Create a new Render web service from this repo.
5. Choose the `Free` instance type.
6. Set the start command to:

```bash
gunicorn --bind 0.0.0.0:$PORT combined_wsgi:app
```

### Render environment variables

Set these in Render:

- `FLASK_ENV=production`
- `FLASK_DEBUG=false`
- `SESSION_COOKIE_SECURE=true`
- `SESSION_LIFETIME_SECONDS=7200`
- `DB_PORT=3306`
- `DB_SSL_MODE=REQUIRED`
- `FLASK_SECRET_KEY=<long random secret>`
- `DB_HOST=<aiven host>`
- `DB_USER=<aiven user>`
- `DB_PASSWORD=<aiven password>`
- `DB_NAME=<aiven database name>`
- `ADMIN_USERNAME=<your admin username>`
- `ADMIN_PASSWORD=<your admin password>`
- `WALLET_PIN=<your wallet pin>`

If you want certificate verification instead of basic TLS, also set:

- `DB_SSL_MODE=VERIFY_IDENTITY`
- `DB_SSL_CA=<path to CA file on the host>`

### Aiven setup

1. Create a free MySQL service.
2. Copy the host, port, username, password, and database name.
3. Use those same values in your local `.env`.
4. Run `python init_mysql_db.py` once from your machine to create the schema and sample data.
5. Deploy the Render web service.

## Included deployment files

- `combined_wsgi.py` serves student routes at `/` and admin routes at `/staff`
- `wsgi_student.py` exposes the student app separately
- `wsgi_admin.py` exposes the admin app separately
- `render.yaml` contains a compatible Render service definition

## Notes

- This is suitable for a personal prototype and portfolio demo.
- Render free web services sleep after idle time, so the first request can be slow.
- The app now avoids SQLite, which makes it much better suited for free cloud hosting.
- Do not commit your real `.env` file or any real database credentials.
