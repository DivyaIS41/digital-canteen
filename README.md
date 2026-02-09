🍽️ Digital Canteen Automation System

A dual-interface web application designed to modernize food ordering in educational institutions by eliminating long queues and enabling real-time order management.

👨‍💻 Developed By

Divya K (4SF23IS041)

Chetan S Baliga (4SF23IS033)

Department of Information Science
Sahyadri College of Engineering & Management

📋 Project Overview

The Digital Canteen Automation System streamlines the canteen ordering process through two dedicated web applications built using Flask and connected via a shared MySQL database.

System Architecture

Student Application (Port 5000)
Browse menu, manage cart, and make secure wallet payments.

Admin Application (Port 5001)
Manage menu items, control inventory, and process orders in real time.

This architecture ensures smooth ordering for students and efficient kitchen management.

🚀 Features
🎓 Student Portal

📖 Digital Menu – Categorized menu with real-time Sold Out status

🛒 Cart System – Add/remove items with live total calculation

🔐 Secure Wallet – Cashless payments protected by a 4-digit PIN (Default: 1234)

📦 Order History – Track order status (Pending / Completed)

👨‍🍳 Admin Dashboard

🧾 Menu Management – Add, update, or delete food items

📊 Inventory Control – Toggle availability for out-of-stock items

⏱️ Order Management – View live orders and mark them as completed

🛠️ Technology Stack
Layer	Technologies Used
Backend	Python (Flask)
Database	MySQL
Frontend	HTML5, CSS3, Bootstrap 5
Templating	Jinja2
Config Management	python-dotenv
⚙️ Installation & Setup
✅ Prerequisites

Ensure the following are installed:

Python 3.x

MySQL Server

📥 Clone Repository & Install Dependencies
git clone https://github.com/your-username/digital-canteen.git
cd digital-canteen
python -m pip install -r requirements.txt

🔐 Environment Configuration

Create a .env file in the root directory:

copy .env.example .env


Update .env with your credentials:

FLASK_APP=student_app.py
FLASK_ENV=development
SECRET_KEY=your_secret_key_here

DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=canteen_db

🗄️ Database Initialization
Option A: Command Line
mysql -u root -p < schema.sql
mysql -u root -p < seed.sql   # Optional sample data

Option B: MySQL Workbench

Open MySQL Workbench

Connect to your local server

Open schema.sql

Select all → Click ⚡ Execute

(Optional) Repeat for seed.sql

▶️ Running the Application

⚠️ Two terminals are required since this is a dual-server system.

Terminal 1 – Student Application
python student_app.py


📍 Runs at: http://127.0.0.1:5000

Terminal 2 – Admin Application
python admin_app.py


📍 Runs at: http://127.0.0.1:5001

📂 Project Structure
digital-canteen/
│
├── static/                 # CSS, Images, JavaScript
├── templates/              # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── cart.html
│   └── admin/
│
├── student_app.py           # Student portal logic
├── admin_app.py             # Admin dashboard logic
├── db_connect.py            # Database connection helper
├── schema.sql               # Database schema
├── seed.sql                 # Sample data
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (ignored)
└── README.md

⚠️ Troubleshooting
Issue	Solution
MySQL Access Denied	Verify DB_PASSWORD in .env
Table doesn't exist	Ensure schema.sql was executed
Port already in use	Change port in app.run()
📜 License

This project is developed strictly for academic submission at
Sahyadri College of Engineering & Management.