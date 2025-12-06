# Digital Canteen

This repository contains a simple Flask-based digital canteen application (student and admin apps), along with database schema and sample data.

## Quickstart

1. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

2. Copy the example env and edit values

```powershell
copy .env.example .env
# then open .env in an editor and fill real values
```

3. Create the database and tables

```powershell
# Login to MySQL and run schema.sql
mysql -u <db_user> -p < schema.sql
# or from command-line
mysql -u %DB_USER% -p%DB_PASSWORD% < schema.sql
```

4. (Optional) Load seed data

```powershell
mysql -u <db_user> -p < seed.sql
```

5. Run the apps

```powershell
# Admin app (port 5001)
python admin_app.py

# Student app (port 5000)
python student_app.py
```

## Notes
- Do not commit your `.env` file — it is excluded by `.gitignore`.
- The apps will fail at startup with a clear error if required environment variables are missing.

## Files added
- `schema.sql` — CREATE TABLE statements
- `seed.sql` — sample data (optional)
- `README.md` — this file

If you want, I can also add a small GitHub Actions workflow to run linting/tests on pushes.
