Digital Canteen Automation System

Developed by:

Divya K (4SF23IS041)

Chetan S Baliga (4SF23IS033)

Dept. of Information Science, Sahyadri College of Engineering & Management

📋 Project Overview

The Digital Canteen is a dual-interface web application designed to streamline food ordering in educational institutions. It eliminates long queues by allowing students to order from their devices while providing kitchen staff with a real-time dashboard to manage orders.

The system is architected as two separate Flask applications sharing a common MySQL database:

Student App (Port 5000): For browsing menus, cart management, and secure wallet payments.

Admin App (Port 5001): For menu updates, stock management, and order fulfillment.

🚀 Features

🎓 Student Portal

Digital Menu: View a categorized list of available items with real-time "Sold Out" status.

Cart System: Add items, adjust quantities, and view a live total.

Secure Wallet: Integrated cashless payment system protected by a 4-digit PIN (Default: 1234).

Order History: Track the status of active orders (Pending vs. Completed).

👨‍🍳 Admin Dashboard

Menu Management: Add new dishes, update prices, and delete items.

Inventory Control: Instantly toggle item availability to prevent ordering of out-of-stock items.

Order Management: Real-time view of incoming orders with the ability to mark them as "Completed".

🛠️ Tech Stack

Backend: Python (Flask)

Database: MySQL (Relational Data Management)

Frontend: HTML5, CSS3, Bootstrap 5 (Responsive UI)

Templating: Jinja2

Configuration: python-dotenv

⚙️ Installation & Setup

Follow these steps to set up the project locally.

1. Prerequisites

Ensure you have the following installed on your system:

Python 3.x

[suspicious link removed]

2. Clone & Install Dependencies

# Clone the repository
git clone [https://github.com/your-username/digital-canteen.git](https://github.com/your-username/digital-canteen.git)
cd digital-canteen

# Install Python dependencies
python -m pip install -r requirements.txt


3. Environment Configuration

Create a .env file in the root directory to store sensitive credentials.

# Copy the example file
copy .env.example .env


Edit .env with your actual MySQL credentials:

FLASK_APP=student_app.py
FLASK_ENV=development
SECRET_KEY=your_secret_key_here
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=canteen_db


4. Database Initialization

You must create the database schema before running the app.

Option A: Via Command Line

# Login to MySQL and run schema.sql
mysql -u root -p < schema.sql

# (Optional) Load sample menu items
mysql -u root -p < seed.sql


Option B: Via MySQL Workbench

Open MySQL Workbench and connect to your local server.

Open schema.sql, select all text, and click the Lightning Bolt icon to execute.

(Optional) Repeat for seed.sql.

▶️ Running the Application

Since the system uses a dual-server architecture, you must run the Student App and Admin App in separate terminal windows.

Terminal 1: Start Student App

python student_app.py
# Server will start at [http://127.0.0.1:5000](http://127.0.0.1:5000)


Terminal 2: Start Admin App

python admin_app.py
# Server will start at [http://127.0.0.1:5001](http://127.0.0.1:5001)


📂 Project Structure

digital-canteen/
├── static/              # CSS, Images, JavaScript files
├── templates/           # Jinja2 HTML Templates
│   ├── base.html        # Base layout (Navbar, Footer)
│   ├── index.html       # Menu Page
│   ├── login.html       # Student Login
│   ├── cart.html        # Cart & Checkout
│   └── admin/           # Admin-specific templates
├── student_app.py       # Main logic for Student Portal
├── admin_app.py         # Main logic for Admin Dashboard
├── db_connect.py        # Database connection helper module
├── schema.sql           # Database creation script
├── seed.sql             # Sample data for testing
├── requirements.txt     # List of Python libraries
├── .env                 # Environment variables (Excluded from Git)
└── README.md            # Project documentation


⚠️ Troubleshooting

"Access Denied" for MySQL: Check your DB_PASSWORD in the .env file.

"Table doesn't exist": Ensure you ran schema.sql to create the tables.

Port already in use: If port 5000 is taken, you can change the port in the app.run() line inside student_app.py.

📜 License

This project is created for academic submission at Sahyadri College of Engineering & Management.