import sqlite3
from flask import Flask, jsonify, request, render_template, session, redirect, url_for
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = 'super_secret_daymes_key'

DB_FILE = "daymes.db"

# Global System Settings
SYSTEM_SETTINGS = {
    "auto_reorder_enabled": True
}

def add_column_if_missing(cursor, table, column, col_type):
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cursor.fetchall()]
    if column not in cols:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 1. Medicines Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            stockQuantity INTEGER NOT NULL,
            dailyUsage INTEGER NOT NULL,
            autoReordered BOOLEAN NOT NULL,
            expirationDate TEXT NOT NULL,
            supplier TEXT NOT NULL,
            orderStatus TEXT NOT NULL,
            expectedDelivery TEXT,
            unitPrice REAL DEFAULT 15.0,
            category TEXT DEFAULT 'General',
            batchNumber TEXT DEFAULT 'BAT-1001'
        )
    ''')
    add_column_if_missing(c, 'medicines', 'unitPrice', 'REAL DEFAULT 15.0')
    add_column_if_missing(c, 'medicines', 'category', "TEXT DEFAULT 'General'")
    add_column_if_missing(c, 'medicines', 'batchNumber', "TEXT DEFAULT 'BAT-1001'")
    
    # 2. Hospitals Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS hospitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            availableBeds INTEGER NOT NULL,
            availableDoctors INTEGER NOT NULL,
            location TEXT NOT NULL,
            totalBeds INTEGER DEFAULT 60,
            contactPhone TEXT DEFAULT '(555) 123-4567',
            status TEXT DEFAULT 'Normal'
        )
    ''')
    add_column_if_missing(c, 'hospitals', 'totalBeds', 'INTEGER DEFAULT 60')
    add_column_if_missing(c, 'hospitals', 'contactPhone', "TEXT DEFAULT '(555) 123-4567'")
    add_column_if_missing(c, 'hospitals', 'status', "TEXT DEFAULT 'Normal'")
    
    # 3. Suppliers Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contactPerson TEXT,
            phone TEXT,
            email TEXT,
            leadTimeDays INTEGER DEFAULT 3,
            rating REAL DEFAULT 4.8,
            status TEXT DEFAULT 'Active'
        )
    ''')
    
    # 4. Patients Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullName TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            roomBed TEXT,
            hospitalId INTEGER,
            condition TEXT,
            status TEXT DEFAULT 'Admitted',
            admissionDate TEXT
        )
    ''')
    
    # 5. Prescriptions Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patientId INTEGER NOT NULL,
            medicineId INTEGER NOT NULL,
            dosage TEXT NOT NULL,
            frequency TEXT NOT NULL,
            prescribedBy TEXT NOT NULL,
            startDate TEXT NOT NULL,
            status TEXT DEFAULT 'Active',
            lastAdministered TEXT,
            FOREIGN KEY (patientId) REFERENCES patients (id),
            FOREIGN KEY (medicineId) REFERENCES medicines (id)
        )
    ''')
    
    # 6. Orders Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicineId INTEGER NOT NULL,
            medicineName TEXT NOT NULL,
            supplierName TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unitCost REAL NOT NULL,
            totalCost REAL NOT NULL,
            orderDate TEXT NOT NULL,
            expectedDelivery TEXT,
            status TEXT DEFAULT 'In Transit',
            trackingCode TEXT,
            FOREIGN KEY (medicineId) REFERENCES medicines (id)
        )
    ''')
    
    # 7. Activity Log Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT NOT NULL
        )
    ''')
    
    # Seed Medicines if empty
    c.execute('SELECT COUNT(*) FROM medicines')
    if c.fetchone()[0] == 0:
        base_date = datetime.now()
        exp_good = (base_date + timedelta(days=120)).strftime('%Y-%m-%d')
        exp_soon = (base_date + timedelta(days=20)).strftime('%Y-%m-%d')
        exp_past = (base_date - timedelta(days=5)).strftime('%Y-%m-%d')
        
        seed_data = [
            ("Paracetamol", 50, 2, False, exp_good, "PharmaCorp Inc", "none", None, 8.50, "Analgesics / Antipyretic", "BAT-PA-991"),
            ("Amoxicillin", 8, 3, True, exp_good, "GlobalMeds Logistics", "ordered", (base_date + timedelta(days=2)).strftime('%Y-%m-%d'), 18.50, "Antibiotic", "BAT-AM-204"),
            ("Vitamin C", 30, 1, False, exp_past, "HealthSupply Co", "none", None, 12.00, "Dietary Supplement", "BAT-VC-115"),
            ("Ibuprofen", 12, 2, False, exp_soon, "PharmaCorp Inc", "none", None, 9.50, "NSAID / Pain Relief", "BAT-IB-774"),
            ("Lisinopril", 5, 1, True, exp_good, "MediLogistics Ltd", "ordered", (base_date + timedelta(days=1)).strftime('%Y-%m-%d'), 14.00, "Cardiovascular", "BAT-LS-331"),
            ("Metformin", 60, 2, False, exp_good, "GlobalMeds Logistics", "none", None, 11.00, "Antidiabetic", "BAT-MF-508")
        ]
        c.executemany('''
            INSERT INTO medicines 
            (name, stockQuantity, dailyUsage, autoReordered, expirationDate, supplier, orderStatus, expectedDelivery, unitPrice, category, batchNumber) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', seed_data)
    else:
        # Update existing records with friendly default categories and prices if empty/defaults
        c.execute("UPDATE medicines SET category = 'Analgesics / Antipyretic', unitPrice = 8.50, batchNumber = 'BAT-PA-991' WHERE name = 'Paracetamol' AND (category IS NULL OR category = 'General')")
        c.execute("UPDATE medicines SET category = 'Antibiotic', unitPrice = 18.50, batchNumber = 'BAT-AM-204' WHERE name = 'Amoxicillin' AND (category IS NULL OR category = 'General')")
        c.execute("UPDATE medicines SET category = 'Dietary Supplement', unitPrice = 12.00, batchNumber = 'BAT-VC-115' WHERE name = 'Vitamin C' AND (category IS NULL OR category = 'General')")
        c.execute("UPDATE medicines SET category = 'NSAID / Pain Relief', unitPrice = 9.50, batchNumber = 'BAT-IB-774' WHERE name = 'Ibuprofen' AND (category IS NULL OR category = 'General')")
        c.execute("UPDATE medicines SET category = 'Cardiovascular', unitPrice = 14.00, batchNumber = 'BAT-LS-331' WHERE name = 'Lisinopril' AND (category IS NULL OR category = 'General')")
        c.execute("UPDATE medicines SET category = 'Antidiabetic', unitPrice = 11.00, batchNumber = 'BAT-MF-508' WHERE name = 'Metformin' AND (category IS NULL OR category = 'General')")

    # Seed Hospitals if empty
    c.execute('SELECT COUNT(*) FROM hospitals')
    if c.fetchone()[0] == 0:
        hospital_data = [
            ("Central City Hospital", 45, 12, "Downtown Metro", 60, "(555) 123-4567", "Normal"),
            ("Mercy General", 12, 4, "Westside District", 20, "(555) 234-5678", "Busy"),
            ("St. Jude Medical Center", 89, 30, "North Hills", 110, "(555) 345-6789", "Normal"),
            ("Sunrise Community Clinic", 5, 2, "East End Suburbs", 10, "(555) 456-7890", "Critical")
        ]
        c.executemany('''
            INSERT INTO hospitals (name, availableBeds, availableDoctors, location, totalBeds, contactPhone, status) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', hospital_data)
        
    # Seed Suppliers if empty
    c.execute('SELECT COUNT(*) FROM suppliers')
    if c.fetchone()[0] == 0:
        supplier_data = [
            ("PharmaCorp Inc", "Dr. Sarah Jenkins", "(555) 123-4567", "orders@pharmacorp.com", 2, 4.9, "Active"),
            ("GlobalMeds Logistics", "Marcus Vance", "(555) 987-6543", "supply@globalmeds.org", 3, 4.7, "Active"),
            ("MediLogistics Ltd", "Elena Rostova", "(555) 555-0199", "dispatch@medilogistics.com", 5, 4.2, "Delayed"),
            ("HealthSupply Co", "James Wilson", "(555) 832-9011", "contact@healthsupply.co", 2, 4.8, "Active")
        ]
        c.executemany('''
            INSERT INTO suppliers (name, contactPerson, phone, email, leadTimeDays, rating, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', supplier_data)

    # Seed Patients if empty
    c.execute('SELECT COUNT(*) FROM patients')
    if c.fetchone()[0] == 0:
        patient_data = [
            ("Eleanor Vance", 68, "Female", "Room 304 - Bed A", 1, "Hypertension & T2 Diabetes", "Admitted", "2026-10-01"),
            ("Liam O'Connor", 42, "Male", "Room 210 - Bed B", 2, "Bacterial Pneumonia", "Admitted", "2026-10-08"),
            ("Sophia Martinez", 29, "Female", "Room 105 - Bed A", 1, "Post-Op Recovery & Pain", "Admitted", "2026-10-10"),
            ("Arthur Pendelton", 74, "Male", "Room 402 - Bed C", 3, "Chronic Heart Failure", "Admitted", "2026-09-28")
        ]
        c.executemany('''
            INSERT INTO patients (fullName, age, gender, roomBed, hospitalId, condition, status, admissionDate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', patient_data)

    # Seed Prescriptions if empty
    c.execute('SELECT COUNT(*) FROM prescriptions')
    if c.fetchone()[0] == 0:
        presc_data = [
            (1, 5, "10mg tablet", "Daily with breakfast", "Dr. Emily Hayes", "2026-10-02", "Active", "2026-10-13 08:30"),
            (1, 6, "500mg tablet", "Twice daily after meals", "Dr. Emily Hayes", "2026-10-02", "Active", "2026-10-13 12:45"),
            (2, 2, "500mg capsule", "3x daily every 8 hours", "Dr. David Kim", "2026-10-08", "Active", "2026-10-13 14:00"),
            (3, 4, "400mg tablet", "Every 6 hours as needed", "Dr. Sarah Chen", "2026-10-10", "Active", "2026-10-13 09:15"),
            (4, 5, "20mg tablet", "Daily at bedtime", "Dr. Robert Taylor", "2026-09-29", "Active", "2026-10-12 21:00")
        ]
        c.executemany('''
            INSERT INTO prescriptions (patientId, medicineId, dosage, frequency, prescribedBy, startDate, status, lastAdministered)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', presc_data)

    # Seed Orders if empty
    c.execute('SELECT COUNT(*) FROM orders')
    if c.fetchone()[0] == 0:
        base_date = datetime.now()
        order_data = [
            (2, "Amoxicillin", "GlobalMeds Logistics", 150, 18.50, 2775.0, (base_date - timedelta(days=2)).strftime('%Y-%m-%d'), (base_date + timedelta(days=2)).strftime('%Y-%m-%d'), "In Transit", "TRK-GM-88219"),
            (5, "Lisinopril", "MediLogistics Ltd", 100, 14.00, 1400.0, (base_date - timedelta(days=1)).strftime('%Y-%m-%d'), (base_date + timedelta(days=1)).strftime('%Y-%m-%d'), "Out for Delivery", "TRK-ML-49201"),
            (1, "Paracetamol", "PharmaCorp Inc", 200, 8.50, 1700.0, (base_date - timedelta(days=14)).strftime('%Y-%m-%d'), (base_date - timedelta(days=12)).strftime('%Y-%m-%d'), "Delivered", "TRK-PC-10294")
        ]
        c.executemany('''
            INSERT INTO orders (medicineId, medicineName, supplierName, quantity, unitCost, totalCost, orderDate, expectedDelivery, status, trackingCode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', order_data)

    # Seed Activity Log
    c.execute('SELECT COUNT(*) FROM activity_log')
    if c.fetchone()[0] == 0:
        c.execute('''
            INSERT INTO activity_log (timestamp, username, action, details)
            VALUES (?, ?, ?, ?)
        ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "System", "Initialization", "Daymes Medicare complete clinical & logistics system initialized."))

    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def log_activity(conn, username, action, details):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute(
        'INSERT INTO activity_log (timestamp, username, action, details) VALUES (?, ?, ?, ?)',
        (timestamp, username, action, details)
    )

@app.before_request
def require_login():
    allowed_routes = ['login', 'static']
    if request.endpoint not in allowed_routes and 'user' not in session:
        # Permit API requests so CLI and AJAX calls are supported seamlessly
        if request.path.startswith('/api/'):
            session['user'] = 'Admin (API)'
        else:
            return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username and password:
            session['user'] = username
            conn = get_db_connection()
            log_activity(conn, username, "Login", f"User '{username}' logged in.")
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
def logout():
    user = session.get('user')
    if user:
        conn = get_db_connection()
        log_activity(conn, user, "Logout", f"User '{user}' logged out.")
        conn.commit()
        conn.close()
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    return render_template('index.html', username=session.get('user', 'Guest'))

# ----------------- SYSTEM SETTINGS API -----------------

@app.route('/api/settings', methods=['GET'])
def get_settings():
    return jsonify(SYSTEM_SETTINGS)

@app.route('/api/settings/toggle_reorder', methods=['POST'])
def toggle_reorder():
    SYSTEM_SETTINGS['auto_reorder_enabled'] = not SYSTEM_SETTINGS['auto_reorder_enabled']
    status_str = "ENABLED" if SYSTEM_SETTINGS['auto_reorder_enabled'] else "DISABLED"
    conn = get_db_connection()
    log_activity(conn, session.get('user', 'Unknown'), "System Setting", f"Global Auto-Reorder System was {status_str}.")
    conn.commit()
    conn.close()
    return jsonify(SYSTEM_SETTINGS)

# ----------------- MEDICINES API -----------------

@app.route('/api/medicines', methods=['GET'])
def get_medicines():
    conn = get_db_connection()
    meds = conn.execute('SELECT * FROM medicines ORDER BY name ASC').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in meds])

@app.route('/api/medicines', methods=['POST'])
def add_medicine():
    data = request.json or {}
    name = data.get('name', '').strip()
    if not name:
        return jsonify({"error": "Medicine name is required"}), 400
        
    stockQuantity = int(data.get('stockQuantity', 0))
    dailyUsage = int(data.get('dailyUsage', 1))
    expirationDate = data.get('expirationDate', '2030-01-01')
    supplier = data.get('supplier', 'PharmaCorp Inc')
    category = data.get('category', 'General')
    unitPrice = float(data.get('unitPrice', 15.0))
    batchNumber = data.get('batchNumber', f"BAT-{datetime.now().strftime('%y%m%d%S')}")
    
    conn = get_db_connection()
    cursor = conn.execute(
        '''INSERT INTO medicines 
           (name, stockQuantity, dailyUsage, autoReordered, expirationDate, supplier, orderStatus, expectedDelivery, unitPrice, category, batchNumber) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (name, stockQuantity, dailyUsage, False, expirationDate, supplier, "none", None, unitPrice, category, batchNumber)
    )
    new_id = cursor.lastrowid
    
    log_activity(conn, session.get('user', 'Unknown'), "Add Medicine", f"Added '{name}' ({category}) with {stockQuantity} stock from {supplier}. Unit Price: ₹{unitPrice:.2f}, Batch: {batchNumber}")
    conn.commit()
    conn.close()
    
    return jsonify({"id": new_id, "name": name, "category": category}), 201

@app.route('/api/medicines/<int:med_id>', methods=['PUT'])
def update_medicine(med_id):
    data = request.json or {}
    conn = get_db_connection()
    med = conn.execute('SELECT * FROM medicines WHERE id = ?', (med_id,)).fetchone()
    if not med:
        conn.close()
        return jsonify({"error": "Medicine not found"}), 404
        
    name = data.get('name', med['name'])
    category = data.get('category', med['category'])
    unitPrice = float(data.get('unitPrice', med['unitPrice']))
    stockQuantity = int(data.get('stockQuantity', med['stockQuantity']))
    dailyUsage = int(data.get('dailyUsage', med['dailyUsage']))
    expirationDate = data.get('expirationDate', med['expirationDate'])
    supplier = data.get('supplier', med['supplier'])
    batchNumber = data.get('batchNumber', med['batchNumber'])
    
    conn.execute('''
        UPDATE medicines 
        SET name = ?, category = ?, unitPrice = ?, stockQuantity = ?, dailyUsage = ?, expirationDate = ?, supplier = ?, batchNumber = ?
        WHERE id = ?
    ''', (name, category, unitPrice, stockQuantity, dailyUsage, expirationDate, supplier, batchNumber, med_id))
    
    log_activity(conn, session.get('user', 'Unknown'), "Update Medicine", f"Updated details for '{name}' (Stock: {stockQuantity}, Price: ₹{unitPrice:.2f}, Batch: {batchNumber}).")
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Medicine updated successfully", "id": med_id}), 200

@app.route('/api/medicines/<int:med_id>/take', methods=['POST'])
def take_medicine(med_id):
    conn = get_db_connection()
    med = conn.execute('SELECT * FROM medicines WHERE id = ?', (med_id,)).fetchone()
    if not med:
        conn.close()
        return jsonify({"error": "Not found"}), 404
        
    med_dict = dict(med)
    username = session.get('user', 'Unknown')
    data = request.json or {}
    dispense_count = int(data.get('count', 1))
    reason = data.get('reason', 'Ward Dispense')
    
    if med_dict['stockQuantity'] >= dispense_count:
        med_dict['stockQuantity'] -= dispense_count
        log_activity(conn, username, "Dispense Medicine", f"Dispensed {dispense_count} unit(s) of {med_dict['name']} ({reason}). Remaining: {med_dict['stockQuantity']}")
    elif med_dict['stockQuantity'] > 0:
        actual_taken = med_dict['stockQuantity']
        med_dict['stockQuantity'] = 0
        log_activity(conn, username, "Dispense Medicine", f"Dispensed remaining {actual_taken} unit(s) of {med_dict['name']}. Out of stock!")
    else:
        conn.close()
        return jsonify({"error": "Stock depleted"}), 400
        
    # Check for auto-reorder condition
    auto_triggered = False
    if SYSTEM_SETTINGS['auto_reorder_enabled']:
        if med_dict['dailyUsage'] > 0 and (med_dict['stockQuantity'] / med_dict['dailyUsage']) <= 3:
            if not med_dict['autoReordered']:
                med_dict['autoReordered'] = True
                med_dict['orderStatus'] = "ordered"
                med_dict['expectedDelivery'] = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
                auto_triggered = True
                
                # Also log an order entry in orders table
                order_qty = max(50, med_dict['dailyUsage'] * 30)
                unit_cost = med_dict.get('unitPrice', 15.0)
                tot_cost = order_qty * unit_cost
                order_date = datetime.now().strftime('%Y-%m-%d')
                tracking = f"TRK-AUTO-{datetime.now().strftime('%M%S%f')[:8]}"
                
                conn.execute('''
                    INSERT INTO orders (medicineId, medicineName, supplierName, quantity, unitCost, totalCost, orderDate, expectedDelivery, status, trackingCode)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (med_id, med_dict['name'], med_dict['supplier'], order_qty, unit_cost, tot_cost, order_date, med_dict['expectedDelivery'], "In Transit", tracking))
                
                log_activity(conn, "System", "Auto-Reorder", f"Stock critically low for {med_dict['name']}. Placed auto-order of {order_qty} units with {med_dict['supplier']} (Tracking: {tracking}).")
            
    conn.execute(
        'UPDATE medicines SET stockQuantity = ?, autoReordered = ?, orderStatus = ?, expectedDelivery = ? WHERE id = ?',
        (med_dict['stockQuantity'], med_dict['autoReordered'], med_dict['orderStatus'], med_dict['expectedDelivery'], med_id)
    )
    conn.commit()
    conn.close()
    
    med_dict['autoTriggeredJustNow'] = auto_triggered
    return jsonify(med_dict), 200

@app.route('/api/medicines/<int:med_id>/reorder', methods=['POST'])
def manual_reorder_medicine(med_id):
    conn = get_db_connection()
    med = conn.execute('SELECT * FROM medicines WHERE id = ?', (med_id,)).fetchone()
    if not med:
        conn.close()
        return jsonify({"error": "Medicine not found"}), 404
        
    med_dict = dict(med)
    data = request.json or {}
    quantity = int(data.get('quantity', 50))
    supplier = data.get('supplier', med_dict['supplier'])
    delivery_days = int(data.get('days', 3))
    
    expected_date = (datetime.now() + timedelta(days=delivery_days)).strftime('%Y-%m-%d')
    order_date = datetime.now().strftime('%Y-%m-%d')
    unit_cost = med_dict.get('unitPrice', 15.0)
    total_cost = quantity * unit_cost
    tracking = f"TRK-ORD-{datetime.now().strftime('%d%H%M%S')}"
    
    # Insert purchase order
    conn.execute('''
        INSERT INTO orders (medicineId, medicineName, supplierName, quantity, unitCost, totalCost, orderDate, expectedDelivery, status, trackingCode)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (med_id, med_dict['name'], supplier, quantity, unit_cost, total_cost, order_date, expected_date, "In Transit", tracking))
    
    # Update medicine
    conn.execute('''
        UPDATE medicines SET autoReordered = 1, orderStatus = 'ordered', expectedDelivery = ?, supplier = ? WHERE id = ?
    ''', (expected_date, supplier, med_id))
    
    username = session.get('user', 'Unknown')
    log_activity(conn, username, "Manual Purchase Order", f"Ordered {quantity} units of {med_dict['name']} from {supplier}. Total: ₹{total_cost:.2f}, Tracking: {tracking}")
    
    conn.commit()
    conn.close()
    return jsonify({"message": "Order created successfully", "trackingCode": tracking, "expectedDelivery": expected_date}), 201

@app.route('/api/medicines/<int:med_id>/dispose', methods=['POST'])
def dispose_medicine(med_id):
    conn = get_db_connection()
    med = conn.execute('SELECT * FROM medicines WHERE id = ?', (med_id,)).fetchone()
    if not med:
        conn.close()
        return jsonify({"error": "Medicine not found"}), 404
        
    data = request.json or {}
    dispose_qty = int(data.get('quantity', med['stockQuantity']))
    reason = data.get('reason', 'Expired / Safety Write-off')
    
    actual_disposed = min(dispose_qty, med['stockQuantity'])
    new_stock = med['stockQuantity'] - actual_disposed
    
    conn.execute('UPDATE medicines SET stockQuantity = ? WHERE id = ?', (new_stock, med_id))
    username = session.get('user', 'Unknown')
    log_activity(conn, username, "Stock Disposal", f"Safely disposed {actual_disposed} units of {med['name']} (Batch: {med['batchNumber']}). Reason: {reason}. Remaining stock: {new_stock}")
    
    conn.commit()
    conn.close()
    return jsonify({"message": f"Successfully disposed {actual_disposed} units.", "remainingStock": new_stock}), 200

@app.route('/api/medicines/<int:med_id>/restock', methods=['POST'])
def restock_medicine(med_id):
    conn = get_db_connection()
    med = conn.execute('SELECT * FROM medicines WHERE id = ?', (med_id,)).fetchone()
    if not med:
        conn.close()
        return jsonify({"error": "Not found"}), 404
        
    med_dict = dict(med)
    username = session.get('user', 'Unknown')
    data = request.json or {}
    add_qty = int(data.get('quantity', 30))
    
    med_dict['stockQuantity'] += add_qty
    med_dict['autoReordered'] = False
    med_dict['orderStatus'] = "none"
    med_dict['expectedDelivery'] = None
    
    log_activity(conn, username, "Receive Shipment", f"Received shipment of {add_qty} {med_dict['name']} from {med_dict['supplier']}.")
    
    conn.execute(
        'UPDATE medicines SET stockQuantity = ?, autoReordered = ?, orderStatus = ?, expectedDelivery = ? WHERE id = ?',
        (med_dict['stockQuantity'], med_dict['autoReordered'], med_dict['orderStatus'], med_dict['expectedDelivery'], med_id)
    )
    conn.commit()
    conn.close()
    
    return jsonify(med_dict), 200

@app.route('/api/medicines/<int:med_id>', methods=['DELETE'])
def delete_medicine(med_id):
    conn = get_db_connection()
    med = conn.execute('SELECT * FROM medicines WHERE id = ?', (med_id,)).fetchone()
    if med:
        log_activity(conn, session.get('user', 'Unknown'), "Delete Medicine", f"Removed medicine '{med['name']}' from inventory.")
        conn.execute('DELETE FROM medicines WHERE id = ?', (med_id,))
    conn.commit()
    conn.close()
    return '', 204

# ----------------- HOSPITALS API -----------------

@app.route('/api/hospitals', methods=['GET'])
def get_hospitals():
    conn = get_db_connection()
    hospitals = conn.execute('SELECT * FROM hospitals ORDER BY name ASC').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in hospitals])

@app.route('/api/hospitals', methods=['POST'])
def add_hospital():
    data = request.json or {}
    name = data.get('name', '').strip()
    location = data.get('location', '').strip()
    if not name or not location:
        return jsonify({"error": "Hospital name and location are required"}), 400
        
    totalBeds = int(data.get('totalBeds', 50))
    availableBeds = int(data.get('availableBeds', totalBeds))
    availableDoctors = int(data.get('availableDoctors', 10))
    contactPhone = data.get('contactPhone', '(555) 000-0000')
    status = data.get('status', 'Normal')
    
    conn = get_db_connection()
    cursor = conn.execute('''
        INSERT INTO hospitals (name, availableBeds, availableDoctors, location, totalBeds, contactPhone, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (name, availableBeds, availableDoctors, location, totalBeds, contactPhone, status))
    new_id = cursor.lastrowid
    
    log_activity(conn, session.get('user', 'Unknown'), "Add Hospital", f"Registered new facility '{name}' in {location} ({availableBeds}/{totalBeds} beds, {availableDoctors} doctors).")
    conn.commit()
    conn.close()
    return jsonify({"id": new_id, "name": name}), 201

@app.route('/api/hospitals/<int:hosp_id>', methods=['PUT'])
def update_hospital(hosp_id):
    data = request.json or {}
    conn = get_db_connection()
    hosp = conn.execute('SELECT * FROM hospitals WHERE id = ?', (hosp_id,)).fetchone()
    if not hosp:
        conn.close()
        return jsonify({"error": "Hospital not found"}), 404
        
    name = data.get('name', hosp['name'])
    location = data.get('location', hosp['location'])
    totalBeds = int(data.get('totalBeds', hosp['totalBeds']))
    availableBeds = int(data.get('availableBeds', hosp['availableBeds']))
    availableDoctors = int(data.get('availableDoctors', hosp['availableDoctors']))
    contactPhone = data.get('contactPhone', hosp['contactPhone'])
    status = data.get('status', hosp['status'])
    
    conn.execute('''
        UPDATE hospitals 
        SET name = ?, location = ?, totalBeds = ?, availableBeds = ?, availableDoctors = ?, contactPhone = ?, status = ?
        WHERE id = ?
    ''', (name, location, totalBeds, availableBeds, availableDoctors, contactPhone, status, hosp_id))
    
    log_activity(conn, session.get('user', 'Unknown'), "Update Facility", f"Updated capacity for '{name}': {availableBeds}/{totalBeds} beds, {availableDoctors} MDs, Status: {status}.")
    conn.commit()
    conn.close()
    return jsonify({"message": "Hospital updated", "id": hosp_id}), 200

@app.route('/api/hospitals/<int:hosp_id>/adjust_beds', methods=['POST'])
def adjust_beds(hosp_id):
    data = request.json or {}
    delta = int(data.get('delta', 0))
    
    conn = get_db_connection()
    hosp = conn.execute('SELECT * FROM hospitals WHERE id = ?', (hosp_id,)).fetchone()
    if not hosp:
        conn.close()
        return jsonify({"error": "Hospital not found"}), 404
        
    new_beds = max(0, min(hosp['totalBeds'], hosp['availableBeds'] + delta))
    status = "Normal"
    if new_beds <= (hosp['totalBeds'] * 0.1):
        status = "Critical"
    elif new_beds <= (hosp['totalBeds'] * 0.3):
        status = "Busy"
        
    conn.execute('UPDATE hospitals SET availableBeds = ?, status = ? WHERE id = ?', (new_beds, status, hosp_id))
    action_type = "Patient Admitted" if delta < 0 else "Patient Discharged"
    log_activity(conn, session.get('user', 'Unknown'), action_type, f"{action_type} at {hosp['name']}. Available beds: {new_beds}/{hosp['totalBeds']}.")
    
    conn.commit()
    conn.close()
    return jsonify({"availableBeds": new_beds, "status": status}), 200

@app.route('/api/hospitals/<int:hosp_id>/adjust_doctors', methods=['POST'])
def adjust_doctors(hosp_id):
    data = request.json or {}
    delta = int(data.get('delta', 0))
    
    conn = get_db_connection()
    hosp = conn.execute('SELECT * FROM hospitals WHERE id = ?', (hosp_id,)).fetchone()
    if not hosp:
        conn.close()
        return jsonify({"error": "Hospital not found"}), 404
        
    new_docs = max(0, hosp['availableDoctors'] + delta)
    conn.execute('UPDATE hospitals SET availableDoctors = ? WHERE id = ?', (new_docs, hosp_id))
    log_activity(conn, session.get('user', 'Unknown'), "Staff Shift", f"Doctor roster updated at {hosp['name']}: {new_docs} active doctors on duty.")
    
    conn.commit()
    conn.close()
    return jsonify({"availableDoctors": new_docs}), 200

@app.route('/api/hospitals/<int:hosp_id>', methods=['DELETE'])
def delete_hospital(hosp_id):
    conn = get_db_connection()
    hosp = conn.execute('SELECT * FROM hospitals WHERE id = ?', (hosp_id,)).fetchone()
    if hosp:
        log_activity(conn, session.get('user', 'Unknown'), "Delete Facility", f"Removed facility '{hosp['name']}' from network.")
        conn.execute('DELETE FROM hospitals WHERE id = ?', (hosp_id,))
    conn.commit()
    conn.close()
    return '', 204

# ----------------- SUPPLIERS API -----------------

@app.route('/api/suppliers', methods=['GET'])
def get_suppliers():
    conn = get_db_connection()
    suppliers = conn.execute('SELECT * FROM suppliers ORDER BY name ASC').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in suppliers])

@app.route('/api/suppliers', methods=['POST'])
def add_supplier():
    data = request.json or {}
    name = data.get('name', '').strip()
    if not name:
        return jsonify({"error": "Supplier name is required"}), 400
        
    contactPerson = data.get('contactPerson', 'Operations Desk')
    phone = data.get('phone', '(555) 000-0000')
    email = data.get('email', 'contact@supplier.com')
    leadTimeDays = int(data.get('leadTimeDays', 3))
    rating = float(data.get('rating', 4.5))
    status = data.get('status', 'Active')
    
    conn = get_db_connection()
    cursor = conn.execute('''
        INSERT INTO suppliers (name, contactPerson, phone, email, leadTimeDays, rating, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (name, contactPerson, phone, email, leadTimeDays, rating, status))
    new_id = cursor.lastrowid
    
    log_activity(conn, session.get('user', 'Unknown'), "Add Supplier", f"Registered new supplier partner '{name}' (Contact: {contactPerson}, Lead time: {leadTimeDays}d).")
    conn.commit()
    conn.close()
    return jsonify({"id": new_id, "name": name}), 201

@app.route('/api/suppliers/<int:sup_id>', methods=['PUT'])
def update_supplier(sup_id):
    data = request.json or {}
    conn = get_db_connection()
    sup = conn.execute('SELECT * FROM suppliers WHERE id = ?', (sup_id,)).fetchone()
    if not sup:
        conn.close()
        return jsonify({"error": "Supplier not found"}), 404
        
    name = data.get('name', sup['name'])
    contactPerson = data.get('contactPerson', sup['contactPerson'])
    phone = data.get('phone', sup['phone'])
    email = data.get('email', sup['email'])
    leadTimeDays = int(data.get('leadTimeDays', sup['leadTimeDays']))
    rating = float(data.get('rating', sup['rating']))
    status = data.get('status', sup['status'])
    
    conn.execute('''
        UPDATE suppliers 
        SET name = ?, contactPerson = ?, phone = ?, email = ?, leadTimeDays = ?, rating = ?, status = ?
        WHERE id = ?
    ''', (name, contactPerson, phone, email, leadTimeDays, rating, status, sup_id))
    
    log_activity(conn, session.get('user', 'Unknown'), "Update Supplier", f"Updated supplier profile for '{name}'. Status: {status}, Lead time: {leadTimeDays}d.")
    conn.commit()
    conn.close()
    return jsonify({"message": "Supplier updated", "id": sup_id}), 200

@app.route('/api/suppliers/<int:sup_id>', methods=['DELETE'])
def delete_supplier(sup_id):
    conn = get_db_connection()
    sup = conn.execute('SELECT * FROM suppliers WHERE id = ?', (sup_id,)).fetchone()
    if sup:
        log_activity(conn, session.get('user', 'Unknown'), "Delete Supplier", f"Removed supplier '{sup['name']}' from registry.")
        conn.execute('DELETE FROM suppliers WHERE id = ?', (sup_id,))
    conn.commit()
    conn.close()
    return '', 204

# ----------------- ORDERS / SHIPMENTS API -----------------

@app.route('/api/orders', methods=['GET'])
def get_orders():
    conn = get_db_connection()
    orders = conn.execute('SELECT * FROM orders ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in orders])

@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.json or {}
    medicineId = int(data.get('medicineId', 0))
    quantity = int(data.get('quantity', 50))
    supplierName = data.get('supplierName', 'PharmaCorp Inc')
    
    conn = get_db_connection()
    med = conn.execute('SELECT * FROM medicines WHERE id = ?', (medicineId,)).fetchone()
    if not med:
        conn.close()
        return jsonify({"error": "Medicine not found"}), 404
        
    unitCost = float(med['unitPrice'])
    totalCost = quantity * unitCost
    orderDate = datetime.now().strftime('%Y-%m-%d')
    expectedDelivery = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
    trackingCode = f"TRK-{supplierName[:3].upper()}-{datetime.now().strftime('%m%d%H%M')}"
    
    cursor = conn.execute('''
        INSERT INTO orders (medicineId, medicineName, supplierName, quantity, unitCost, totalCost, orderDate, expectedDelivery, status, trackingCode)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (medicineId, med['name'], supplierName, quantity, unitCost, totalCost, orderDate, expectedDelivery, "Ordered", trackingCode))
    new_id = cursor.lastrowid
    
    # Update medicine order status
    conn.execute('UPDATE medicines SET orderStatus = "ordered", expectedDelivery = ? WHERE id = ?', (expectedDelivery, medicineId))
    
    log_activity(conn, session.get('user', 'Unknown'), "Place Order", f"Placed purchase order #{new_id} for {quantity}x {med['name']} from {supplierName}. Total: ₹{totalCost:.2f}, Tracking: {trackingCode}")
    conn.commit()
    conn.close()
    return jsonify({"id": new_id, "trackingCode": trackingCode, "status": "Ordered"}), 201

@app.route('/api/orders/<int:order_id>/advance', methods=['POST'])
def advance_order_status(order_id):
    conn = get_db_connection()
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    if not order:
        conn.close()
        return jsonify({"error": "Order not found"}), 404
        
    current_status = order['status']
    next_status = current_status
    if current_status == 'Ordered':
        next_status = 'In Transit'
    elif current_status == 'In Transit':
        next_status = 'Out for Delivery'
    elif current_status == 'Out for Delivery':
        next_status = 'Delivered'
        
    conn.execute('UPDATE orders SET status = ? WHERE id = ?', (next_status, order_id))
    
    # If Delivered, restock the medicine in inventory!
    if next_status == 'Delivered':
        med_id = order['medicineId']
        qty = order['quantity']
        conn.execute('''
            UPDATE medicines 
            SET stockQuantity = stockQuantity + ?, autoReordered = 0, orderStatus = 'none', expectedDelivery = NULL 
            WHERE id = ?
        ''', (qty, med_id))
        log_activity(conn, session.get('user', 'Unknown'), "Order Delivered", f"Shipment #{order_id} ({order['medicineName']}, {qty} units) delivered and added to inventory stock!")
    else:
        log_activity(conn, session.get('user', 'Unknown'), "Shipment Updated", f"Shipment #{order_id} ({order['trackingCode']}) status updated from {current_status} -> {next_status}.")
        
    conn.commit()
    conn.close()
    return jsonify({"id": order_id, "oldStatus": current_status, "status": next_status}), 200

# ----------------- PATIENTS & PRESCRIPTIONS API -----------------

@app.route('/api/patients', methods=['GET'])
def get_patients():
    conn = get_db_connection()
    patients = conn.execute('''
        SELECT p.*, h.name as hospitalName,
               (SELECT COUNT(*) FROM prescriptions pr WHERE pr.patientId = p.id AND pr.status = 'Active') as activePrescriptions
        FROM patients p
        LEFT JOIN hospitals h ON p.hospitalId = h.id
        ORDER BY p.id DESC
    ''').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in patients])

@app.route('/api/patients', methods=['POST'])
def add_patient():
    data = request.json or {}
    fullName = data.get('fullName', '').strip()
    if not fullName:
        return jsonify({"error": "Full name is required"}), 400
        
    age = int(data.get('age', 35))
    gender = data.get('gender', 'Other')
    roomBed = data.get('roomBed', 'Ward A - Bed 1')
    hospitalId = int(data.get('hospitalId', 1))
    condition = data.get('condition', 'General Observation')
    status = data.get('status', 'Admitted')
    admissionDate = data.get('admissionDate', datetime.now().strftime('%Y-%m-%d'))
    
    conn = get_db_connection()
    cursor = conn.execute('''
        INSERT INTO patients (fullName, age, gender, roomBed, hospitalId, condition, status, admissionDate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (fullName, age, gender, roomBed, hospitalId, condition, status, admissionDate))
    new_id = cursor.lastrowid
    
    log_activity(conn, session.get('user', 'Unknown'), "Patient Admission", f"Admitted patient '{fullName}' ({age}yo {gender}) to {roomBed} (Diagnosis: {condition}).")
    conn.commit()
    conn.close()
    return jsonify({"id": new_id, "fullName": fullName}), 201

@app.route('/api/patients/<int:patient_id>', methods=['PUT'])
def update_patient(patient_id):
    data = request.json or {}
    conn = get_db_connection()
    p = conn.execute('SELECT * FROM patients WHERE id = ?', (patient_id,)).fetchone()
    if not p:
        conn.close()
        return jsonify({"error": "Patient not found"}), 404
        
    fullName = data.get('fullName', p['fullName'])
    age = int(data.get('age', p['age']))
    gender = data.get('gender', p['gender'])
    roomBed = data.get('roomBed', p['roomBed'])
    hospitalId = int(data.get('hospitalId', p['hospitalId']))
    condition = data.get('condition', p['condition'])
    status = data.get('status', p['status'])
    
    conn.execute('''
        UPDATE patients 
        SET fullName = ?, age = ?, gender = ?, roomBed = ?, hospitalId = ?, condition = ?, status = ?
        WHERE id = ?
    ''', (fullName, age, gender, roomBed, hospitalId, condition, status, patient_id))
    
    log_activity(conn, session.get('user', 'Unknown'), "Update Patient", f"Updated medical chart for patient '{fullName}' (Status: {status}, Room: {roomBed}).")
    conn.commit()
    conn.close()
    return jsonify({"message": "Patient updated", "id": patient_id}), 200

@app.route('/api/patients/<int:patient_id>', methods=['DELETE'])
def delete_patient(patient_id):
    conn = get_db_connection()
    p = conn.execute('SELECT * FROM patients WHERE id = ?', (patient_id,)).fetchone()
    if p:
        log_activity(conn, session.get('user', 'Unknown'), "Discharge Patient", f"Discharged/removed patient record '{p['fullName']}' from active census.")
        conn.execute('DELETE FROM prescriptions WHERE patientId = ?', (patient_id,))
        conn.execute('DELETE FROM patients WHERE id = ?', (patient_id,))
    conn.commit()
    conn.close()
    return '', 204

@app.route('/api/prescriptions', methods=['GET'])
def get_prescriptions():
    conn = get_db_connection()
    prescs = conn.execute('''
        SELECT pr.*, p.fullName as patientName, p.roomBed, m.name as medicineName, m.stockQuantity as medicineStock, m.category as medicineCategory
        FROM prescriptions pr
        JOIN patients p ON pr.patientId = p.id
        JOIN medicines m ON pr.medicineId = m.id
        ORDER BY pr.id DESC
    ''').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in prescs])

@app.route('/api/prescriptions', methods=['POST'])
def add_prescription():
    data = request.json or {}
    patientId = int(data.get('patientId', 0))
    medicineId = int(data.get('medicineId', 0))
    dosage = data.get('dosage', '1 tablet').strip()
    frequency = data.get('frequency', 'Daily').strip()
    prescribedBy = data.get('prescribedBy', 'Attending Physician').strip()
    startDate = data.get('startDate', datetime.now().strftime('%Y-%m-%d'))
    
    conn = get_db_connection()
    p = conn.execute('SELECT * FROM patients WHERE id = ?', (patientId,)).fetchone()
    m = conn.execute('SELECT * FROM medicines WHERE id = ?', (medicineId,)).fetchone()
    if not p or not m:
        conn.close()
        return jsonify({"error": "Invalid patient or medicine selected"}), 400
        
    cursor = conn.execute('''
        INSERT INTO prescriptions (patientId, medicineId, dosage, frequency, prescribedBy, startDate, status, lastAdministered)
        VALUES (?, ?, ?, ?, ?, ?, 'Active', NULL)
    ''', (patientId, medicineId, dosage, frequency, prescribedBy, startDate))
    new_id = cursor.lastrowid
    
    log_activity(conn, session.get('user', 'Unknown'), "New Prescription", f"Prescribed {m['name']} ({dosage}, {frequency}) to patient {p['fullName']} by {prescribedBy}.")
    conn.commit()
    conn.close()
    return jsonify({"id": new_id, "patientName": p['fullName'], "medicineName": m['name']}), 201

@app.route('/api/prescriptions/<int:presc_id>/administer', methods=['POST'])
def administer_prescription(presc_id):
    conn = get_db_connection()
    presc = conn.execute('''
        SELECT pr.*, p.fullName as patientName, m.name as medicineName, m.stockQuantity, m.dailyUsage, m.autoReordered, m.supplier
        FROM prescriptions pr
        JOIN patients p ON pr.patientId = p.id
        JOIN medicines m ON pr.medicineId = m.id
        WHERE pr.id = ?
    ''', (presc_id,)).fetchone()
    
    if not presc:
        conn.close()
        return jsonify({"error": "Prescription not found"}), 404
        
    if presc['stockQuantity'] <= 0:
        conn.close()
        return jsonify({"error": f"Cannot administer: {presc['medicineName']} is out of stock!"}), 400
        
    new_stock = presc['stockQuantity'] - 1
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    username = session.get('user', 'Attending Nurse')
    
    # Update prescription lastAdministered timestamp
    conn.execute('UPDATE prescriptions SET lastAdministered = ? WHERE id = ?', (now_str, presc_id))
    
    # Update medicine stock & auto-reorder if necessary
    auto_triggered = False
    order_status = 'none'
    expected_delivery = None
    if SYSTEM_SETTINGS['auto_reorder_enabled'] and presc['dailyUsage'] > 0 and (new_stock / presc['dailyUsage']) <= 3:
        if not presc['autoReordered']:
            auto_triggered = True
            order_status = 'ordered'
            expected_delivery = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
            conn.execute('''
                UPDATE medicines 
                SET stockQuantity = ?, autoReordered = 1, orderStatus = 'ordered', expectedDelivery = ?
                WHERE id = ?
            ''', (new_stock, expected_delivery, presc['medicineId']))
            
            # Place order entry
            conn.execute('''
                INSERT INTO orders (medicineId, medicineName, supplierName, quantity, unitCost, totalCost, orderDate, expectedDelivery, status, trackingCode)
                VALUES (?, ?, ?, 50, 15.0, 750.0, ?, ?, 'In Transit', ?)
            ''', (presc['medicineId'], presc['medicineName'], presc['supplier'], datetime.now().strftime('%Y-%m-%d'), expected_delivery, f"TRK-RX-{datetime.now().strftime('%M%S')}"))
            
            log_activity(conn, "System", "Auto-Reorder", f"Administering dose caused critical stock for {presc['medicineName']}. Auto-reordered from {presc['supplier']}.")
    else:
        conn.execute('UPDATE medicines SET stockQuantity = ? WHERE id = ?', (new_stock, presc['medicineId']))
        
    log_activity(conn, username, "Administer Medication", f"Administered {presc['dosage']} of {presc['medicineName']} to patient '{presc['patientName']}'. Remaining stock: {new_stock} units.")
    conn.commit()
    conn.close()
    
    return jsonify({
        "message": f"Dose administered to {presc['patientName']} successfully.",
        "lastAdministered": now_str,
        "remainingStock": new_stock,
        "autoTriggered": auto_triggered
    }), 200

@app.route('/api/prescriptions/<int:presc_id>/toggle', methods=['POST'])
def toggle_prescription(presc_id):
    conn = get_db_connection()
    presc = conn.execute('SELECT * FROM prescriptions WHERE id = ?', (presc_id,)).fetchone()
    if not presc:
        conn.close()
        return jsonify({"error": "Prescription not found"}), 404
        
    new_status = 'Paused' if presc['status'] == 'Active' else 'Active'
    conn.execute('UPDATE prescriptions SET status = ? WHERE id = ?', (new_status, presc_id))
    log_activity(conn, session.get('user', 'Unknown'), "Prescription Status", f"Prescription #{presc_id} status changed to {new_status}.")
    conn.commit()
    conn.close()
    return jsonify({"id": presc_id, "status": new_status}), 200

@app.route('/api/prescriptions/<int:presc_id>', methods=['DELETE'])
def delete_prescription(presc_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM prescriptions WHERE id = ?', (presc_id,))
    log_activity(conn, session.get('user', 'Unknown'), "Delete Prescription", f"Prescription #{presc_id} discontinued.")
    conn.commit()
    conn.close()
    return '', 204

# ----------------- DYNAMIC REAL-TIME ANALYTICS API -----------------

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    conn = get_db_connection()
    
    # 1. Medicines & Inventory metrics
    meds = conn.execute('SELECT * FROM medicines').fetchall()
    total_med_types = len(meds)
    total_inventory_items = sum(m['stockQuantity'] for m in meds)
    total_inventory_value = sum(m['stockQuantity'] * (m['unitPrice'] or 15.0) for m in meds)
    monthly_burn_rate = sum(m['dailyUsage'] * 30 * (m['unitPrice'] or 15.0) for m in meds)
    
    today = datetime.now()
    critically_low_count = 0
    expired_count = 0
    expiring_soon_count = 0
    value_at_risk = 0.0
    category_summary = {}
    
    for m in meds:
        rem_days = m['stockQuantity'] // m['dailyUsage'] if m['dailyUsage'] > 0 else 999
        if rem_days <= 3:
            critically_low_count += 1
            
        try:
            exp_date = datetime.strptime(m['expirationDate'], '%Y-%m-%d')
            diff_days = (exp_date - today).days
            if diff_days < 0:
                expired_count += 1
                value_at_risk += m['stockQuantity'] * (m['unitPrice'] or 15.0)
            elif diff_days <= 30:
                expiring_soon_count += 1
                value_at_risk += m['stockQuantity'] * (m['unitPrice'] or 15.0)
        except Exception:
            pass
            
        cat = m['category'] or 'General'
        if cat not in category_summary:
            category_summary[cat] = {"count": 0, "stock": 0, "value": 0.0}
        category_summary[cat]["count"] += 1
        category_summary[cat]["stock"] += m['stockQuantity']
        category_summary[cat]["value"] += round(m['stockQuantity'] * (m['unitPrice'] or 15.0), 2)

    # 2. Hospitals Capacity metrics
    hospitals = conn.execute('SELECT * FROM hospitals').fetchall()
    total_hospitals = len(hospitals)
    total_network_beds = sum(h['totalBeds'] for h in hospitals) or 1
    total_available_beds = sum(h['availableBeds'] for h in hospitals)
    total_occupied_beds = max(0, total_network_beds - total_available_beds)
    bed_occupancy_rate = round((total_occupied_beds / total_network_beds) * 100, 1)
    total_doctors = sum(h['availableDoctors'] for h in hospitals)
    
    # 3. Patients & Prescriptions
    patient_count = conn.execute('SELECT COUNT(*) FROM patients').fetchone()[0]
    active_prescriptions = conn.execute('SELECT COUNT(*) FROM prescriptions WHERE status = "Active"').fetchone()[0]
    
    # 4. Orders & Shipments
    pending_orders = conn.execute('SELECT COUNT(*) FROM orders WHERE status != "Delivered"').fetchone()[0]
    
    # 5. Usage Trend Projection (dynamic based on actual monthly consumption)
    trend_labels = ['May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct']
    base_usage = sum(m['dailyUsage'] * 30 for m in meds)
    trend_data = [
        int(base_usage * 0.85),
        int(base_usage * 0.92),
        int(base_usage * 0.88),
        int(base_usage * 1.05),
        int(base_usage * 0.98),
        int(base_usage)
    ]
    
    conn.close()
    
    return jsonify({
        "total_med_types": total_med_types,
        "total_inventory_items": total_inventory_items,
        "total_inventory_value": round(total_inventory_value, 2),
        "monthly_burn_rate": round(monthly_burn_rate, 2),
        "value_at_risk": round(value_at_risk, 2),
        "critically_low_count": critically_low_count,
        "expired_count": expired_count,
        "expiring_soon_count": expiring_soon_count,
        "category_summary": category_summary,
        "total_hospitals": total_hospitals,
        "total_network_beds": total_network_beds,
        "total_available_beds": total_available_beds,
        "total_occupied_beds": total_occupied_beds,
        "bed_occupancy_rate": bed_occupancy_rate,
        "total_doctors": total_doctors,
        "patient_count": patient_count,
        "active_prescriptions": active_prescriptions,
        "pending_orders": pending_orders,
        "usage_trend": {
            "labels": trend_labels,
            "data": trend_data
        }
    })

# ----------------- ACTIVITY AUDIT LOG API -----------------

@app.route('/api/activity', methods=['GET'])
def get_activity():
    conn = get_db_connection()
    search = request.args.get('search', '').strip()
    action = request.args.get('action', '').strip()
    
    query = 'SELECT * FROM activity_log WHERE 1=1'
    params = []
    
    if search:
        query += ' AND (details LIKE ? OR username LIKE ?)'
        params.extend([f"%{search}%", f"%{search}%"])
    if action:
        query += ' AND action = ?'
        params.append(action)
        
    query += ' ORDER BY id DESC LIMIT 100'
    logs = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in logs])

if __name__ == '__main__':
    app.run(debug=True, port=8080)
