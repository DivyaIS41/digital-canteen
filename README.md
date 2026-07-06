# Digital Canteen Automation System

Digital Canteen is a Flask prototype with two web apps backed by SQLite:

- `student_app.py` for students to browse the menu, manage a cart, and place orders
- `admin_app.py` for canteen staff to manage items, specials, pricing, and orders

## Architecture

- Backend: Flask
- Database: SQLite
- Templates: Jinja2
- Production server: Gunicorn
- Deployment shape: one Render web service serving both apps and one SQLite database file on a persistent disk

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
- Admin app: `http://127.0.0.1:5001`

## Deployment

This prototype is deployment-worthy on Render as a single web service with a persistent disk for SQLite.
That avoids the "two services cannot share one disk" limitation.

### Included deployment files

- `wsgi_student.py` exposes the student app for Gunicorn
- `wsgi_admin.py` exposes the admin app for Gunicorn
- `combined_wsgi.py` exposes both apps together for Render
- `render.yaml` defines the Render web service and disk

### Render demo deployment

1. Push this repository to GitHub.
2. Create a new Blueprint service in Render from this repo.
3. Set these environment variables:

- `FLASK_ENV=production`
- `FLASK_DEBUG=false`
- `SESSION_COOKIE_SECURE=true`
- `FLASK_SECRET_KEY=<strong-random-secret>`
- `ADMIN_USERNAME=<your-admin-user>`
- `ADMIN_PASSWORD=<your-admin-password>`
- `WALLET_PIN=<private-wallet-pin>`
- `SQLITE_DB_PATH=/opt/render/project/src/data/canteen.db`

4. Render will mount a persistent disk at `/opt/render/project/src/data`.
5. On first deploy, the app initializes the SQLite database automatically if the DB file does not exist.
6. Your demo URLs will be:

- Student app: `https://your-service.onrender.com/`
- Admin app: `https://your-service.onrender.com/staff/admin/login`
- Student health: `https://your-service.onrender.com/health`
- Admin health: `https://your-service.onrender.com/staff/health`

### Local or VPS alternative

You can still run the student and admin apps separately locally with `student_app.py` and `admin_app.py`.

## Notes

- The app now uses SQLite instead of MySQL.
- SQLite is fine for a personal prototype, demo, or portfolio project.
- SQLite is not ideal for heavy concurrent multi-user production traffic.
- Render persistent disks are attached to one service only, so the demo deployment uses one combined service.
- The admin app still uses `.env` credentials for admin login.
- The student app requires `WALLET_PIN` in production.

## Important Security Reminder

Do not commit your real `.env` file. If your old MySQL credentials were ever published, rotate them.
