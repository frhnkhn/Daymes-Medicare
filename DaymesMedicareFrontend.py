# DaymesMedicareFrontend.py
# Python CLI Frontend for Daymes Medicare Clinical & Logistics System

import urllib.request
import urllib.error
import json
import sys

BASE_URL = "http://localhost:8080/api"

def make_request(endpoint, data=None, method="GET"):
    url = f"{BASE_URL}/{endpoint}"
    headers = {"Content-Type": "application/json"}
    payload = json.dumps(data).encode("utf-8") if data else None
    
    req = urllib.request.Request(url, data=payload, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as res:
            if res.status == 204:
                return {}
            content = res.read().decode("utf-8")
            return json.loads(content) if content else {}
    except urllib.error.URLError as e:
        print(f"\n[Error] Cannot connect to server at {url}. Is the Flask server running? ({e})")
        return None

def print_banner():
    print("\n" + "=" * 55)
    print("      🏥 DAYMES MEDICARE CLINICAL & LOGISTICS CLI")
    print("=" * 55)
    print(" 1. View Inventory & Expiration Alerts")
    print(" 2. Dispense Medicine (Ward / Clinic)")
    print(" 3. Add New Medicine to Inventory")
    print(" 4. Manual Purchase Reorder / Fast Restock")
    print(" 5. Hospital Network & Bed Capacity")
    print(" 6. Patient Census & Administer Prescriptions")
    print(" 7. Real-Time Network Analytics & KPIs")
    print(" 8. Exit")
    print("=" * 55)

def view_medicines():
    data = make_request("medicines")
    if data is None:
        return
    if not data:
        print("\nNo medicines found in the system.")
        return
        
    print("\n" + "-" * 75)
    print(f"{'ID':<4} | {'Name':<18} | {'Category':<16} | {'Stock':<6} | {'Daily':<5} | {'Price(₹)':<8} | {'Status'}")
    print("-" * 75)
    for m in data:
        stock = m.get('stockQuantity', 0)
        daily = m.get('dailyUsage', 1)
        rem = stock // daily if daily > 0 else 0
        price = m.get('unitPrice', 15.0)
        
        status = "Healthy"
        if m.get('orderStatus') == 'ordered':
            status = "🚚 Order Pending"
        elif rem <= 3:
            status = "⚠️ Critically Low"
            
        print(f"{m.get('id'):<4} | {m.get('name', 'Unknown')[:18]:<18} | {m.get('category', 'General')[:16]:<16} | {stock:<6} | {daily:<5} | ₹{price:<7.2f} | {status}")
    print("-" * 75)

def dispense_medicine():
    print("\n--- DISPENSE MEDICINE ---")
    try:
        med_id = int(input("Enter Medicine ID to dispense: "))
        count = int(input("Units to dispense (default 1): ") or "1")
        reason = input("Dispensing Reason / Department (e.g. Ward 3, ER): ") or "Ward Dispense"
    except ValueError:
        print("Invalid input.")
        return
        
    result = make_request(f"medicines/{med_id}/take", data={"count": count, "reason": reason}, method="POST")
    if result:
        print(f"\n[Success] Dispensed {count} unit(s) of {result.get('name')}. Remaining Stock: {result.get('stockQuantity')}")
        if result.get('autoTriggeredJustNow'):
            print("🚨 NOTICE: Stock reached critical threshold. Auto-order placed with supplier!")

def add_medicine():
    print("\n--- ADD NEW MEDICINE ---")
    name = input("Medicine Name: ").strip()
    if not name:
        print("Name cannot be empty.")
        return
    category = input("Category (e.g. Antibiotic, Analgesics, Cardiovascular): ").strip() or "General"
    try:
        stock = int(input("Initial Stock Quantity (e.g. 50): "))
        daily = int(input("Estimated Daily Usage (e.g. 2): "))
        unit_price = float(input("Unit Cost / Price in USD (e.g. 12.50): ") or "15.0")
    except ValueError:
        print("Invalid numbers entered.")
        return
        
    supplier = input("Supplier Name (default PharmaCorp Inc): ").strip() or "PharmaCorp Inc"
    expiration = input("Expiration Date (YYYY-MM-DD): ").strip() or "2028-12-31"
    
    payload = {
        "name": name,
        "category": category,
        "stockQuantity": stock,
        "dailyUsage": daily,
        "unitPrice": unit_price,
        "supplier": supplier,
        "expirationDate": expiration
    }
    res = make_request("medicines", data=payload, method="POST")
    if res:
        print(f"\n[Success] Added {name} (ID: {res.get('id')}) to system database!")

def manual_reorder():
    print("\n--- MANUAL PURCHASE REORDER ---")
    try:
        med_id = int(input("Medicine ID to reorder: "))
        quantity = int(input("Quantity to order (e.g. 100): "))
        days = int(input("Expected delivery lead time in days (e.g. 3): ") or "3")
    except ValueError:
        print("Invalid number input.")
        return
        
    res = make_request(f"medicines/{med_id}/reorder", data={"quantity": quantity, "days": days}, method="POST")
    if res:
        print(f"\n[Success] Purchase Order confirmed! Tracking: {res.get('trackingCode')}, ETA: {res.get('expectedDelivery')}")

def view_hospitals():
    hospitals = make_request("hospitals")
    if not hospitals:
        return
    print("\n" + "=" * 70)
    print("                HOSPITAL NETWORK CAPACITY")
    print("=" * 70)
    for h in hospitals:
        total = h.get('totalBeds', 60)
        avail = h.get('availableBeds', 0)
        occ = round(((total - avail) / total) * 100) if total > 0 else 0
        print(f"🏥 {h.get('name')} ({h.get('location')}) - Status: [{h.get('status', 'Normal')}]")
        print(f"   Available Beds: {avail}/{total} ({occ}% occupied) | Doctors On Duty: {h.get('availableDoctors')}")
        print(f"   Contact: {h.get('contactPhone')}\n")

def view_prescriptions():
    prescs = make_request("prescriptions")
    if not prescs:
        return
    print("\n" + "=" * 80)
    print("              ACTIVE PATIENT PRESCRIPTIONS")
    print("=" * 80)
    for pr in prescs:
        print(f"Rx #{pr.get('id')} | Patient: {pr.get('patientName')} ({pr.get('roomBed')})")
        print(f"   Medication: {pr.get('medicineName')} | Dosage: {pr.get('dosage')} ({pr.get('frequency')})")
        print(f"   Prescribed By: {pr.get('prescribedBy')} | Status: {pr.get('status')} | Last Admin: {pr.get('lastAdministered') or 'Never'}")
        print("-" * 80)
        
    admin_opt = input("\nAdminister dose now? Enter Rx ID or press Enter to skip: ").strip()
    if admin_opt:
        try:
            rx_id = int(admin_opt)
            res = make_request(f"prescriptions/{rx_id}/administer", method="POST")
            if res:
                print(f"\n[Success] {res.get('message')} (Remaining Stock: {res.get('remainingStock')})")
        except ValueError:
            print("Invalid Rx ID.")

def view_analytics():
    data = make_request("analytics")
    if not data:
        return
    print("\n" + "=" * 60)
    print("        📊 REAL-TIME CLINICAL & FINANCIAL ANALYTICS")
    print("=" * 60)
    print(f"Total Medicine Formulations : {data.get('total_med_types')}")
    print(f"Total Physical Inventory    : {data.get('total_inventory_items')} units")
    print(f"Total Valuation             : ₹{data.get('total_inventory_value'):,.2f}")
    print(f"Monthly Consumption Burn    : ₹{data.get('monthly_burn_rate'):,.2f} / month")
    print(f"Value at Risk (Expiring)    : ₹{data.get('value_at_risk'):,.2f}")
    print(f"Critically Low Stock Items  : {data.get('critically_low_count')}")
    print(f"Network Bed Occupancy       : {data.get('bed_occupancy_rate')}% ({data.get('total_occupied_beds')}/{data.get('total_network_beds')} beds)")
    print(f"Active Doctors on Duty      : {data.get('total_doctors')}")
    print(f"Admitted Patients           : {data.get('patient_count')}")
    print(f"Active Prescriptions        : {data.get('active_prescriptions')}")
    print(f"Incoming Shipments          : {data.get('pending_orders')}")
    print("=" * 60)

def main():
    while True:
        print_banner()
        choice = input("Enter choice (1-8): ").strip()
        if choice == '1':
            view_medicines()
        elif choice == '2':
            dispense_medicine()
        elif choice == '3':
            add_medicine()
        elif choice == '4':
            manual_reorder()
        elif choice == '5':
            view_hospitals()
        elif choice == '6':
            view_prescriptions()
        elif choice == '7':
            view_analytics()
        elif choice == '8':
            print("\nExiting Daymes Medicare... Stay healthy!\n")
            sys.exit(0)
        else:
            print("Invalid choice, please select between 1 and 8.")

if __name__ == "__main__":
    main()
