# QueueLess – Virtual Queue Management System

A dynamic, web-based virtual queuing application designed for colleges, service counters, and administrative offices. Built using **Python (Flask)**, **SQLite**, **HTML5**, **CSS3**, and **JavaScript**, adhering strictly to the **Model-View-Controller (MVC)** architectural pattern and standard **Software Development Life Cycle (SDLC)** phases.

---

## 🎯 Project Overview & Objective

Long physical queues at college administrative desks (admissions, fee payment, document verification, library, exam cell) lead to overcrowding, lost time, and frustration. **QueueLess** replaces physical standing lines with a digital queuing experience:

- **Students/Users** can register, log in, select a service, take a digital token, track their real-time queue position and estimated wait time from their phone or laptop, and cancel their token if needed.
- **Counter Staff / Administrators** can manage service counters, call the next token in line, mark tokens as completed, or cancel absent tokens.
- **Dynamic Updates**: Queue positions, waiting times, and token statuses update dynamically from the SQLite database via client-side polling without requiring full page reloads.

---

## 🏗️ Software Development Life Cycle (SDLC) Phases

This project follows standard academic SDLC methodology:

### Phase 1: Requirements Analysis
- **User / Student Functional Requirements:**
  - Secure registration and login with encrypted password storage.
  - View available service counters with real-time waiting counts and average turnaround times.
  - Generate a sequential digital token (e.g., `ADM-101`) for an active service.
  - Monitor live queue status: Position in line (`#1`, `#2`), people ahead, estimated wait time in minutes, and currently serving token.
  - Ability to cancel an active token before being called.
  - Ability to view and print digital token slip.
- **Administrator Functional Requirements:**
  - Administrative authentication and role-based access control.
  - Centralized dashboard displaying live metrics (Total Waiting, Serving, Completed, Cancelled).
  - One-click "Call Next Token" per service desk.
  - Manual queue overrides: Mark as Completed, Cancel, or Serve.
  - Manage services: Add new counters, update turnaround speed (min/person), and toggle counters active/inactive.
  - Audit trail & token history with filtering options.

### Phase 2: System Design & MVC Architecture
```
                         +------------------------+
                         |      Browser (View)    |
                         | HTML / CSS / JS (Live) |
                         +-----------+------------+
                                     |
               HTTP Requests / Forms | JSON API Polling
                                     v
                       +-----------------------------+
                       |    Controllers (Routes)     |
                       | - auth_controller.py        |
                       | - user_controller.py        |
                       | - admin_controller.py       |
                       | - api_controller.py         |
                       +--------------+--------------+
                                      |
                      Queries / Logic | Updates
                                      v
                       +-----------------------------+
                       |     Models (Data Layer)     |
                       | - user_model.py             |
                       | - service_model.py          |
                       | - token_model.py            |
                       | - db.py                     |
                       +--------------+--------------+
                                      |
                                  SQL | Transactions
                                      v
                       +-----------------------------+
                       |     SQLite Database File    |
                       |        (queueless.db)       |
                       +-----------------------------+
```

### Phase 3: Implementation
- **Backend:** Python 3 with Flask framework and Werkzeug security.
- **Database:** SQLite3 with relational foreign keys and transaction integrity.
- **Frontend Views:** Jinja2 templates styled with custom CSS designed for clarity, high contrast, and academic presentation.
- **Client Scripting:** Pure JavaScript (ES6) for DOM updates, countdown timer, Web Audio API chime notifications, and live status synchronization.

### Phase 4: Testing & Verification
- Unit and integration tests in `tests/test_queueless.py` verifying user registration, duplicate prevention, password hashing, sequential token generation, position calculation algorithms, admin call-next logic, and API endpoints.

### Phase 5: Deployment & Maintenance
- Standalone execution with isolated virtual environment (`venv`) and automatic SQLite database seeding on initial boot.

---

## 📂 Project Structure

```
queueless/
│
├── app.py                     # Flask application factory, error handlers & context
├── config.py                  # App configuration (Secret key, Database URI)
├── init_db.py                 # Standalone script to initialize and seed database
├── requirements.txt           # Python package dependencies
├── .gitignore                 # Excludes venv, pycache, and database files
├── README.md                  # Complete documentation and setup manual
│
├── models/                    # [M] MODEL LAYER: Database queries & business logic
│   ├── __init__.py
│   ├── db.py                  # SQLite connection management & table DDL
│   ├── user_model.py          # User authentication, hashing & profile retrieval
│   ├── service_model.py       # Service counter configuration & live statistics
│   └── token_model.py         # Token numbering, queue position & wait estimation
│
├── controllers/               # [C] CONTROLLER LAYER: Flask route handlers
│   ├── __init__.py            # Auth decorators (@login_required, @admin_required)
│   ├── auth_controller.py     # Login, registration, and session logout
│   ├── user_controller.py     # Student dashboard, token generation & cancellation
│   ├── admin_controller.py    # Admin console, call-next logic & counter config
│   └── api_controller.py      # JSON REST endpoints for live status polling
│
├── templates/                 # [V] VIEW LAYER: HTML Jinja2 Templates
│   ├── base.html              # Shared base template with navbar & flash alerts
│   ├── 404.html               # Page not found error view
│   ├── 500.html               # Internal server error view
│   ├── auth/
│   │   ├── login.html         # Login form with 1-click test credentials
│   │   └── register.html      # Student registration form
│   ├── user/
│   │   ├── dashboard.html     # Service catalog & active token cards
│   │   ├── token_view.html    # Live digital queue ticket slip with sync
│   │   └── my_tokens.html     # Historical token log for user
│   └── admin/
│       ├── dashboard.html     # Admin command center & live queue actions
│       ├── services.html      # Manage/Add service counters
│       └── queue_history.html # Complete historical audit trail
│
├── static/                    # STATIC ASSETS
│   ├── css/
│   │   └── style.css          # Clean, responsive CSS stylesheet
│   └── js/
│       ├── main.js            # Flash auto-dismiss and dialog confirmations
│       ├── user_queue.js      # Live polling, countdown timer & audio chime
│       └── admin_queue.js     # Auto-refresh control for admin desk screen
│
└── tests/                     # AUTOMATED TESTS
    └── test_queueless.py      # Unit and integration test suite
```

---

## 🗄️ Database Schema

The database consists of three related tables in `queueless.db`:

1. **`users`**
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `username`: TEXT UNIQUE NOT NULL
   - `password_hash`: TEXT NOT NULL (hashed using PBKDF2/SHA256)
   - `full_name`: TEXT NOT NULL
   - `email`: TEXT
   - `phone`: TEXT
   - `role`: TEXT DEFAULT 'user' (`user` or `admin`)
   - `created_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP

2. **`services`**
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `service_code`: TEXT UNIQUE NOT NULL (e.g. `ADM`, `ACC`, `DOC`)
   - `service_name`: TEXT NOT NULL
   - `description`: TEXT
   - `avg_wait_per_token`: INTEGER DEFAULT 5 (average minutes per person)
   - `prefix`: TEXT DEFAULT 'T'
   - `is_active`: INTEGER DEFAULT 1 (1 = Open, 0 = Closed)
   - `created_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP

3. **`tokens`**
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `token_number`: TEXT NOT NULL (e.g. `ADM-101`)
   - `service_id`: INTEGER (FOREIGN KEY -> `services.id`)
   - `user_id`: INTEGER (FOREIGN KEY -> `users.id`)
   - `status`: TEXT DEFAULT 'Waiting' (`Waiting`, `Serving`, `Completed`, `Cancelled`)
   - `admin_notes`: TEXT
   - `created_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   - `called_at`: TIMESTAMP
   - `completed_at`: TIMESTAMP
   - `cancelled_at`: TIMESTAMP

---

## ⚡ Quick Setup & Execution Guide

### 1. Open Terminal or PowerShell
Navigate to the project directory:
```bash
cd queueless
```

### 2. Create the Python Virtual Environment
Keep the virtual environment isolated from the source code:
```bash
# Windows
python -m venv venv

# macOS / Linux
python3 -m venv venv
```

### 3. Activate the Virtual Environment
```bash
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Windows Command Prompt (CMD)
.\venv\Scripts\activate.bat

# macOS / Linux
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Initialize the Database (Optional - also auto-initializes on startup)
```bash
python init_db.py
```

### 6. Run the Application
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🔐 Default Pre-seeded Login Accounts

The database comes pre-configured with test accounts for quick evaluation:

| Role | Username | Password | Access Level |
|---|---|---|---|
| **Administrator** | `admin` | `admin123` | Full control: Call next token, complete/cancel tokens, manage services |
| **Student / User** | `student` | `student123` | Student view: Request tokens, view live position, cancel own tokens |

*(You can also register any new student account using the **Register** form on the website.)*

---

## 🧪 Running Automated Tests

A comprehensive test suite is included. Run it with:
```bash
# With venv activated:
python -m unittest discover -s tests
```

---

## 💡 How the Dynamic Live Queue Works

1. **Token Issuance:** When a student clicks "Get Digital Token", the system checks for existing active tokens, generates a sequential token (e.g. `ADM-101`), and redirects to the **Digital Ticket Slip**.
2. **Queue Position Calculation:**
   $$\text{Queue Position} = (\text{Count of older Waiting tokens for this service}) + 1$$
3. **Estimated Waiting Time:**
   $$\text{Estimated Wait} = (\text{Tokens Ahead} + \text{Desk Active Flag}) \times \text{Avg Wait Time}$$
4. **Live Polling:** The ticket page periodically requests `/api/token/<id>/status` every 5 seconds.
5. **Instant Status Transition:** When an admin calls the token (`status` transitions to `Serving`):
   - The badge updates to pulsing green.
   - An audio alert plays in the browser.
   - A banner notifies the student to proceed to the desk immediately!

---

## 📄 Academic Project Details
- **Project Name:** QueueLess – Virtual Queue System
- **Target Degree:** Bachelor of Computer Applications (BCA) / B.Tech CSE Project
- **Architecture:** Model-View-Controller (MVC)
- **Year:** 2026
