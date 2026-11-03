import copy

CLINIC_CONFIG = {
    "senior_age_threshold": 60,
    "insurance_consultation_rate": 0.20,
    "insurance_test_rate": 0.50,
    "senior_discount_rate": 0.10
}

patients = {
    "P001": {"name": "Ali Khan", "age": 32, "city": "Lahore", "insurance": True},
    "P002": {"name": "Ahmed Raza", "age": 45, "city": "Multan", "insurance": False},
    "P003": {"name": "Sara Ahmed", "age": 28, "city": "Lahore", "insurance": True},
    "P004": {"name": "Usman Ali", "age": 67, "city": "Islamabad", "insurance": False}
}

doctors = {
    "D001": {"name": "Dr. Hassan", "specialization": "Cardiology", "fee": 5000, "available": True},
    "D002": {"name": "Dr. Sara", "specialization": "Dermatology", "fee": 3000, "available": True},
    "D003": {"name": "Dr. Ahmed", "specialization": "General", "fee": 2000, "available": True}
}

appointments = [
    {"appointment_id": "A001", "patient_id": "P001", "doctor_id": "D001",
     "status": "completed", "tests": ["ECG", "Blood Test"]},
    {"appointment_id": "A002", "patient_id": "P002", "doctor_id": "D003",
     "status": "completed", "tests": []},
    {"appointment_id": "A003", "patient_id": "P003", "doctor_id": "D002",
     "status": "cancelled", "tests": []},
    {"appointment_id": "A004", "patient_id": "P004", "doctor_id": "D001",
     "status": "completed", "tests": ["ECG"]}
]

test_prices = {
    "ECG": 1500,
    "Blood Test": 1000,
    "X-Ray": 2500,
    "MRI": 8000
}

def validate_appointment(appointment, patients=patients, doctors=doctors, test_prices=test_prices):
    if not isinstance(appointment, dict):
        return False, "Appointment must be a dictionary"
    patient_id = appointment.get("patient_id")
    doctor_id = appointment.get("doctor_id")
    if not isinstance(patient_id, str) or patient_id not in patients:
        return False, f"Unknown patient {patient_id}"
    elif not isinstance(doctor_id, str) or doctor_id not in doctors:
        return False, f"Unknown doctor {doctor_id}"
    
    available = doctors[doctor_id].get("available")
    doctor_name = doctors[doctor_id].get("name")
    if not available:
        return False, f"{doctor_name} is not available"

    status = appointment.get("status")
    if status not in ("completed", "cancelled", "pending"):
        return False, f"{status} not in options"
    
    age = patients[patient_id]["age"]
    if isinstance(age, bool) or not isinstance(age, (int, float)) or age < 0:
        return False, f"Invalid age for patient {patient_id}: {age}"

    tests = appointment.get("tests", [])
    if not isinstance(tests, list) or not all(isinstance(t, str) for t in tests):
        return False, "tests must be a list of strings"

    invalid_tests = [t for t in tests if t not in test_prices]
    if invalid_tests:
        return False, f"Invalid test(s): {invalid_tests}"

    if len(tests) != len(set(tests)):
        return False, f"Duplicate test(s) in: {tests}"

    return True, "Valid"

def validate_doctors(doctors):
    if not isinstance(doctors, dict):
        raise ValueError("doctors must be a dict")
    for doctor_id, doctor in doctors.items():
        if not isinstance(doctor, dict):
            raise ValueError(f"{doctor_id}: doctor must be a dict")
        for key in ("name", "specialization"):
            if not isinstance(doctor.get(key), str):
                raise ValueError(f"{doctor_id}: missing or invalid {key}")
        fee = doctor.get("fee")
        if isinstance(fee, bool) or not isinstance(fee, (int, float)) or fee < 0:
            raise ValueError(f"{doctor_id}: invalid fee")
        if not isinstance(doctor.get("available"), bool):
            raise ValueError(f"{doctor_id}: available must be a bool")

def validate_patients(patients):
    if not isinstance(patients, dict):
        raise ValueError("patients must be a dict")
    for patient_id, patient in patients.items():
        if not isinstance(patient, dict):
            raise ValueError(f"{patient_id}: patient must be a dict")
        for key in ("name", "city"):
            if not isinstance(patient.get(key), str):
                raise ValueError(f"{patient_id}: missing or invalid {key}")
        age = patient.get("age")
        if isinstance(age, bool) or not isinstance(age, (int, float)) or age < 0:
            raise ValueError(f"{patient_id}: invalid age")
        if not isinstance(patient.get("insurance"), bool):
            raise ValueError(f"{patient_id}: insurance must be a bool")

def validate_test_prices(test_prices):
    if not isinstance(test_prices, dict):
        raise ValueError("test_prices must be a dict")
    for test_name, price in test_prices.items():
        if isinstance(price, bool) or not isinstance(price, (int, float)) or price < 0:
            raise ValueError(f"{test_name}: invalid price")

def calculate_test_charges(tests, test_prices=test_prices):
    return sum(test_prices.get(t, 0) for t in tests)

def calculate_insurance_coverage(consultation_fee, test_charges, has_insurance):
    if not has_insurance:
        return 0, 0
    consultation_coverage = consultation_fee * CLINIC_CONFIG["insurance_consultation_rate"]
    test_coverage = test_charges * CLINIC_CONFIG["insurance_test_rate"]
    return round(consultation_coverage, 2), round(test_coverage, 2)

def calculate_bill(consultation_fee, test_charges, has_insurance, age):
    subtotal = consultation_fee + test_charges
    consultation_coverage, test_coverage = calculate_insurance_coverage(
        consultation_fee, test_charges, has_insurance
    )
    total_coverage = round(consultation_coverage + test_coverage, 2)
    after_insurance = round(subtotal - total_coverage, 2)
    
    senior_discount = 0
    if age >= CLINIC_CONFIG["senior_age_threshold"]:
        senior_discount = round(after_insurance * CLINIC_CONFIG["senior_discount_rate"], 2)

    final_amount = round(after_insurance - senior_discount, 2)

    return {
        "subtotal": subtotal,
        "consultation_coverage": consultation_coverage,
        "test_coverage": test_coverage,
        "total_coverage": total_coverage,
        "after_insurance": after_insurance,
        "senior_discount": senior_discount,
        "final_amount": final_amount
    }    
    
def process_appointment(appointment, processed_appointment_ids=None,
                        patients=patients, doctors=doctors, test_prices=test_prices):
    if processed_appointment_ids is None:
        processed_appointment_ids = set()

    if not isinstance(appointment, dict):
        return {"appointment_id": None, "status": "REJECTED",
                "reason": "Appointment must be a dictionary",
                "patient_id": None, "doctor_id": None}
    patient_id = appointment.get("patient_id")
    doctor_id = appointment.get("doctor_id")

    raw_id = appointment.get("appointment_id")
    if not isinstance(raw_id, str) or not raw_id.strip():
        return {"appointment_id": None, "status": "REJECTED",
                "reason": "appointment_id is required and must be a non-empty string",
                "patient_id": patient_id, "doctor_id": doctor_id}
    appointment_id = raw_id.strip().upper()
    if appointment_id in processed_appointment_ids:
        return {"appointment_id": appointment_id, "status": "REJECTED",
                "reason": f"Appointment {appointment_id} already processed",
                "patient_id": patient_id, "doctor_id": doctor_id}

    if appointment.get("status") == "cancelled":
        return {"appointment_id": appointment_id, "status": "REJECTED",
                "reason": "Cannot process a cancelled appointment",
                "patient_id": patient_id, "doctor_id": doctor_id}
    is_valid, reason = validate_appointment(appointment, patients, doctors, test_prices)
    if not is_valid:
        return {"appointment_id": appointment_id, "status": "REJECTED",
                "reason": reason,
                "patient_id": patient_id, "doctor_id": doctor_id}

    if appointment["status"] == "pending":
        return {"appointment_id": appointment_id, "status": "REJECTED",
                "reason": "Pending appointments cannot be billed until completed",
                "patient_id": patient_id, "doctor_id": doctor_id}

    patient_id = appointment["patient_id"]
    doctor_id = appointment["doctor_id"]
    patient = patients[patient_id]
    doctor = doctors[doctor_id]
    consultation_fee = doctor["fee"]
    test_charges = calculate_test_charges(appointment.get("tests", []), test_prices)
    bill = calculate_bill(
        consultation_fee,
        test_charges,
        patient["insurance"],
        patient["age"]
    )
    processed_appointment_ids.add(appointment_id)

    return {
        "appointment_id": appointment.get("appointment_id"),
        "status": "APPROVED",
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "bill": bill
    }
     
def cancel_appointment(appointment):
    status = appointment.get("status")

    if status == "completed":
        return False, f"Cannot cancel: appointment {appointment.get('appointment_id')} is already completed"
    if status == "cancelled":
        return False, f"Cannot cancel: appointment {appointment.get('appointment_id')} is already cancelled"
    if status == "pending":
        appointment["status"] = "cancelled"
        return True, f"Appointment {appointment.get('appointment_id')} cancelled successfully"

    return False, f"Invalid status: {status}"

def process_all_appointments(appointments, patients=patients, doctors=doctors, test_prices=test_prices):
    processed_ids = set()
    results = []
    for a in appointments:
        result = process_appointment(a, processed_ids, patients, doctors, test_prices)
        results.append(result)
    return results

def generate_doctor_report(doctor_id, appointments, processed_results, doctors=doctors):
    doctor = doctors.get(doctor_id)
    if not doctor:
        return None, f"Doctor {doctor_id} does not exist"

    doctor_appointments = [a for a in appointments if a["doctor_id"] == doctor_id]
    total = len(doctor_appointments)
    completed = len([a for a in doctor_appointments if a["status"] == "completed"])
    cancelled = len([a for a in doctor_appointments if a["status"] == "cancelled"])
    pending = len([a for a in doctor_appointments if a["status"] == "pending"])

    complete = ([a for a in doctor_appointments if a["status"] == "completed"])
    doctor_results = [r for r in processed_results if r["doctor_id"] == doctor_id]
    bills = [r["bill"]["final_amount"] for r in doctor_results if r["status"] == "APPROVED"]

    revenue = sum(bills)
    average_bill = revenue / len(bills) if bills else 0


    return {
        "doctor_id": doctor_id,
        "name": doctor["name"],
        "specialization": doctor["specialization"],
        "total_appointments": total,
        "completed": completed,
        "cancelled": cancelled,
        "pending": pending,
        "revenue": revenue,
        "average_bill" : average_bill,
    }, "OK"
    
def generate_patient_report(patient_id, appointments, processed_results, patients=patients):
    patient = patients.get(patient_id)
    if not patient:
        return None, f"Patient {patient_id} does not exist"
    patient_appointments = [a for a in appointments if a["patient_id"] == patient_id]
    patient_results = [r for r in processed_results if r["patient_id"] == patient_id]
    total_spent = 0
    total_saved = 0
    visits = []
    for r in patient_results:
        if r["status"] == "APPROVED":
            bill = r["bill"]
            total_spent += bill["final_amount"]
            total_saved += bill["total_coverage"] + bill["senior_discount"]
            visits.append(r["appointment_id"])

    return {
        "patient_id": patient_id,
        "name": patient["name"],
        "age": patient["age"],
        "insurance": patient["insurance"],
        "total_appointments": len(patient_appointments),
        "completed_visits": visits,
        "total_spent": total_spent,
        "total_saved": total_saved
    }, "OK"
    
def generate_clinic_report(appointments, processed_results, patients=patients, doctors=doctors):
    total_appointments = len(appointments)
    completed = [a for a in appointments if a["status"] == "completed"]
    cancelled = [a for a in appointments if a["status"] == "cancelled"]
    pending = [a for a in appointments if a["status"] == "pending"]

    total_revenue = sum(
        r["bill"]["final_amount"] for r in processed_results if r["status"] == "APPROVED"
    )

    appts_per_doctor = {d: len([a for a in appointments if a["doctor_id"] == d]) for d in doctors}
    max_requests = max(appts_per_doctor.values(), default=0)
    most_requested_doctors = (
        [doctors[d]["name"] for d, count in appts_per_doctor.items() if count == max_requests]
        if max_requests > 0 else []
    )

    doctor_revenue = {}
    for doctor_id in doctors:
        report, _ = generate_doctor_report(doctor_id, appointments, processed_results, doctors)
        if report is None:
            continue
        doctor_revenue[report["name"]] = report["revenue"]

    if doctor_revenue:
        highest_revenue = max(doctor_revenue.values())
        top_doctor = [name for name, rev in doctor_revenue.items() if rev == highest_revenue]
    else:
        top_doctor = []

    insured_patients = [p for p in patients.values() if p["insurance"]]
    senior_patients = [p for p in patients.values() if p["age"] >= 60]

    patient_reports = []
    for p in patients:
        report, _ = generate_patient_report(p, appointments, processed_results, patients)
        patient_reports.append(report)

    if patient_reports:
        highest_spent = max(r["total_spent"] for r in patient_reports)
        highest_spending_patient = [r["name"] for r in patient_reports if r["total_spent"] == highest_spent]
    else:
        highest_spending_patient = []

    no_completed = [r["name"] for r in patient_reports if not r["completed_visits"]]

    return {
        "total_appointments": total_appointments,
        "completed": len(completed),
        "cancelled": len(cancelled),
        "pending": len(pending),
        "total_revenue": total_revenue,
        "top_doctor": top_doctor,
        "insured_patient_count": len(insured_patients),
        "senior_patient_count": len(senior_patients),
        "most_requested_doctor": most_requested_doctors,
        "highest_spending_patient": highest_spending_patient,
        "patients_no_completed_appointment": no_completed
    }
    
   
def combine_bills(*bills):
    return sum(bills)

def search_patients(patients_data=None, **criteria):
    if patients_data is None:
        patients_data = patients
    allowed_keys = {"name", "age", "city", "insurance"}
    unknown = set(criteria) - allowed_keys
    if unknown:
        raise ValueError(f"Unknown search field(s): {', '.join(sorted(unknown))}")
    results = []
    for pid, info in patients_data.items():
        match = all(info.get(key) == value for key, value in criteria.items())
        if match:
            results.append(pid)
    return results

def get_senior_threshold():
    return CLINIC_CONFIG["senior_age_threshold"]

def calculate_total(consultation_fee, test_charges, other_charges=0):
    return consultation_fee + test_charges + other_charges

def calculate_bill_kwargs(consultation_fee, **options):
    allowed_keys = {"insurance", "senior_discount", "age", "tests", "include_tests"}
    unknown = set(options) - allowed_keys
    if unknown:
        return None, f"Unknown option(s): {', '.join(sorted(unknown))}"

    has_insurance = options.get("insurance", False)
    apply_senior = options.get("senior_discount", False)
    age = options.get("age", 0)
    include_tests = options.get("include_tests", True)
    tests = options.get("tests", [])

    if not isinstance(has_insurance, bool):
        return None, "insurance must be a bool"
    if not isinstance(apply_senior, bool):
        return None, "senior_discount must be a bool"
    if not isinstance(include_tests, bool):
        return None, "include_tests must be a bool"
    if isinstance(age, bool) or not isinstance(age, (int, float)):
        return None, "age must be a number"
    if not isinstance(tests, list):
        return None, "tests must be a list"

    tests = tests if include_tests else []
    test_charges = calculate_test_charges(tests)

    bill = calculate_bill(
        consultation_fee,
        test_charges,
        has_insurance,
        age if apply_senior else 0
    )
    return bill["final_amount"], None

def main():
    appts = copy.deepcopy(appointments)
    validate_patients(patients)
    validate_doctors(doctors)
    validate_test_prices(test_prices)

    results = process_all_appointments(appts)

    print("     PROCESSING ALL APPOINTMENTS")
    print("=" * 40)
    for result in results:
        if result["status"] == "APPROVED":
            print(f"{result['appointment_id']} -> APPROVED | "
                  f"Patient pays: {result['bill']['final_amount']:.2f}")
        else:
            print(f"{result['appointment_id']} -> REJECTED | Reason: {result['reason']}")
    print("\n" + "=" * 40)
    print("     CANCELLATION TEST")
    print("=" * 40)
    test_appt = {"appointment_id": "A999", "patient_id": "P001", "doctor_id": "D001",
                 "status": "pending", "tests": []}
    ok, msg = cancel_appointment(test_appt)
    print(msg)
    ok, msg = cancel_appointment(appts[0])
    print(msg)
 
    print("\n" + "=" * 40)
    print("     DOCTOR REPORT ")
    print("=" * 40)
    results = process_all_appointments(appts)
    report, _ = generate_doctor_report("D001", appts, results)
    if report is not None:
        for k, v in report.items():
            print(f"{k}: {v}")
 
    print("\n" + "=" * 40)
    print("     PATIENT REPORT ")
    print("=" * 40)
    report, _ = generate_patient_report("P001", appts, results)
    if report is not None:
        for k, v in report.items():
            print(f"{k}: {v}")
 
    print("\n" + "=" * 40)
    print("      CLINIC DASHBOARD")
    print("=" * 40)
    dashboard = generate_clinic_report(appts, results)
    for k, v in dashboard.items():
        print(f"{k}: {v}")
 
    print("\n" + "=" * 40)
    print("   UTILITY FUNCTIONS DEMO")
    print("=" * 40)
    print("combine_bills(5850, 2250, 1000) ->", combine_bills(5850, 2250, 1000))
    print("search_patients(insurance=True) ->", search_patients(insurance=True))
    result, error = calculate_bill_kwargs(5000, insurance=True, senior_discount=True, age=67, tests=["ECG"])
    print("calculate_bill_kwargs demo ->", result)


if __name__ == "__main__":
    main()
