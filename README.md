# Daymes-Medicare 🏥

Enterprise Clinical Inventory & Hospital Logistics Management System.

Daymes Medicare is an integrated hospital and pharmacy logistics solution designed to monitor medicine stocks, automate restock orders, manage hospital bed capacities, track patient prescriptions, and provide real-time healthcare network analytics.

---

## 🌟 Key Features

- **Pharmaceutical Inventory Management**: Real-time stock tracking, expiration alert warnings, and automated supplier reordering.
- **Hospital Network & Bed Capacity**: Live monitoring of available beds, active physician rosters, and ward capacities.
- **Patient Census & Prescription Administration**: Patient tracking, admission statuses, dosage schedules, and medication administration records.
- **Procurement & Supply Chain**: Supplier lead times, tracking codes, and order pipeline lifecycle management.
- **Audit Logging & Analytics**: Comprehensive audit logs for clinical dispensing actions, monthly burn rates, and financial inventory valuations.
- **Dual Interfaces**: Full-featured interactive Web Dashboard and standalone Terminal CLI.

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.10+
- SQLite3 (included with Python)
- Java 17+ & Maven (for optional Java microservice)

### 2. Setup Python Environment

```bash
# Clone the repository
git clone https://github.com/frhnkhn/Daymes-Medicare.git
cd Daymes-Medicare

# Create virtual environment & install dependencies
python3 -m venv venv
source venv/bin/activate
pip install flask
```

### 3. Run the Web Application

```bash
python app.py
```

The web dashboard will start at **http://localhost:8080**.

- **Default Web Login**: Enter any username and password (e.g. `admin` / `admin`).
- Database initializes and seeds automatically upon first run.

### 4. Run the Terminal CLI Frontend

While the web server is running in the background, open a new terminal:

```bash
python DaymesMedicareFrontend.py
```

---

## 📁 Project Structure

```
Daymes-Medicare/
├── app.py                       # Core Flask REST API & Web Server
├── DaymesMedicareFrontend.py    # Interactive CLI Client
├── templates/
│   ├── index.html               # Main Web Dashboard
│   └── login.html               # Authentication Portal
├── java-backend/                # Enterprise Spring Boot Microservice
│   ├── pom.xml
│   └── src/
├── daymes.db                    # SQLite Database (auto-generated)
├── .gitignore
└── README.md
```

---

## 📄 License

This project is licensed under the MIT License.
