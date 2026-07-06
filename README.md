# Digital Canteen Automation System

Digital Canteen is a Flask prototype with two web apps backed by SQLite:

- `student_app.py` for students to browse the menu, manage a cart, and place orders
- `admin_app.py` for canteen staff to manage items, specials, pricing, and orders

## Architecture

- Backend: Flask
- Database: SQLite
- Templates: Jinja2
- Production server: Gunicorn
- Deployment shape: two app processes on the same host sharing one SQLite database file

## Local Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and fill in real values:

```bash
copy .env.example .env
```

Required values:

- `FLASK_SECRET_KEY`
- `SQLITE_DB_PATH`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `WALLET_PIN`

### 3. Initialize the SQLite database

```bash
python init_sqlite_db.py
```

This creates the database file, applies `schema.sql`, and loads sample data from `seed.sql`.

### 4. Run both apps

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
- Admin app: `http://127.0.0.1:5001`

## Deployment

This prototype is deployment-worthy for a simple single-host setup.
Use one machine or one VPS with a persistent writable filesystem so both apps point to the same SQLite file.

### Included deployment files

- `wsgi_student.py` exposes the student app for Gunicorn
- `wsgi_admin.py` exposes the admin app for Gunicorn

### Prototype deployment steps

1. Push this repository to GitHub.
2. Choose a host that supports a persistent SQLite file.
3. Run both apps on that same host.
4. Set these environment variables:

- `FLASK_ENV=production`
- `FLASK_DEBUG=false`
- `SESSION_COOKIE_SECURE=true`
- `FLASK_SECRET_KEY=<strong-random-secret>`
- `ADMIN_USERNAME=<your-admin-user>`
- `ADMIN_PASSWORD=<your-admin-password>`
- `WALLET_PIN=<private-wallet-pin>`
- `SQLITE_DB_PATH=<path-to-persistent-canteen.db>`

5. Run:

```bash
python init_sqlite_db.py
```

6. Start both apps with Gunicorn or Python on that same host.
7. Check both health endpoints:

- Student: `/health`
- Admin: `/health`

### Start commands

Student service:

```bash
gunicorn --bind 0.0.0.0:$PORT wsgi_student:app
```

Admin service:

```bash
gunicorn --bind 0.0.0.0:$PORT wsgi_admin:app
```

## Notes

- The app now uses SQLite instead of MySQL.
- SQLite is fine for a personal prototype, demo, or portfolio project.
- SQLite is not ideal for heavy concurrent multi-user production traffic.
- SQLite is also not a great fit for split multi-service cloud deployments where each service has separate filesystem storage.
- The admin app still uses `.env` credentials for admin login.
- The student app requires `WALLET_PIN` in production.

## Important Security Reminder

Do not commit your real `.env` file. If your old MySQL credentials were ever published, rotate them.
