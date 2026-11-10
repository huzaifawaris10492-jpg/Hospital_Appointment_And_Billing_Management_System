import copy
import math
from decimal import Decimal, ROUND_HALF_UP


MAX_AGE = 130
MAX_AMOUNT = 10**12  
CENT = Decimal("0.01")
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

def normalize_id(value):
    return value.strip().upper() if isinstance(value, str) else value

def normalize_status(value):
    return value.strip().lower() if isinstance(value, str) else value

def find_double_bookings(appointments):
    """Return a list of (doctor_id, time_slot) pairs with more than one active appointment."""
    if not isinstance(appointments, (list, tuple)):
        raise ValueError("appointments must be a list")
    seen = {}
    conflicts = []
    for a in appointments:
        if not isinstance(a, dict):
            continue
        if normalize_status(a.get("status")) == "cancelled":
            continue
        key = (normalize_id(a.get("doctor_id")), a.get("time_slot"))
        if key[1] is None:
            continue
        if key in seen:
            conflicts.append(key)
        else:
            seen[key] = a.get("appointment_id")
    return conflicts

def validate_appointment(appointment, patients=patients, doctors=doctors, test_prices=test_prices):
    if not isinstance(appointment, dict):
        return False, "Appointment must be a dictionary"
    
    patient_id = normalize_id(appointment.get("patient_id"))
    doctor_id = normalize_id(appointment.get("doctor_id"))
    if not isinstance(patient_id, str) or patient_id not in patients:
        return False, f"Unknown patient {patient_id}"
    elif not isinstance(doctor_id, str) or doctor_id not in doctors:
        return False, f"Unknown doctor {doctor_id}"
    
    appointment_id = appointment.get("appointment_id")
    if not isinstance(appointment_id, str) or not appointment_id.strip():
        return False, "Invalid or missing appointment_id"
    
    doctor = doctors[doctor_id]
    if not isinstance(doctor, dict):
        return False, f"Invalid record for doctor {doctor_id}"
    if not is_valid_amount(doctor.get("fee")):
        return False, f"Invalid fee for doctor {doctor_id}"

    available = doctor.get("available")
    doctor_name = doctor.get("name")
    if not isinstance(available, bool):
        return False, f"Doctor {doctor_id}: available must be a bool"
    if available is not True:
        return False, f"{doctor_name} is not available"

    status = appointment.get("status")
    if isinstance(status, str):
        status = normalize_status(status)
    if status not in ("completed", "cancelled", "pending"):
        return False, f"Invalid status: {status} (expected completed, cancelled or pending)"
    
    patient = patients[patient_id]
    if not isinstance(patient, dict):
        return False, f"Invalid record for patient {patient_id}"

    age = patient.get("age")
    if not is_valid_age(age):
        return False, f"Invalid age for patient {patient_id}: {age}"

    if not isinstance(patient.get("insurance"), bool):
        return False, f"Invalid insurance value for patient {patient_id}"

    tests = appointment.get("tests", [])
    if not isinstance(tests, list) or not all(isinstance(t, str) for t in tests):
        return False, "tests must be a list of strings"

    test_prices_upper = {k.upper(): k for k in test_prices}
    normalized_tests = [normalize_id(t) for t in tests]
    invalid_tests = [t for t, n in zip(tests, normalized_tests) if n not in test_prices_upper]
    if invalid_tests:
        return False, f"Invalid test(s): {invalid_tests}"

    if len(normalized_tests) != len(set(normalized_tests)):
        return False, f"Duplicate test(s) in: {tests}"

    return True, "Valid"

def is_valid_age(age):
    if isinstance(age, bool):
        return False
    if not isinstance(age, (int, float, Decimal)) or not math.isfinite(age):
        return False
    return 0 <= age <= MAX_AGE and age == int(age)

def validate_doctors(doctors):
    if not isinstance(doctors, dict):
        raise ValueError("doctors must be a dict")
    for doctor_id, doctor in doctors.items():
        if not isinstance(doctor_id, str) or not doctor_id.strip():
            raise ValueError(f"Invalid doctor id: {doctor_id!r}")
        if not isinstance(doctor, dict):
            raise ValueError(f"{doctor_id}: doctor must be a dict")
        if doctor_id != normalize_id(doctor_id):
            raise ValueError(f"Doctor id {doctor_id!r} must be trimmed and upper-case")
        for key in ("name", "specialization"):
            value = doctor.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{doctor_id}: missing or invalid {key}")
        if not is_valid_amount(doctor.get("fee")):
            raise ValueError(f"{doctor_id}: invalid fee")
        if not isinstance(doctor.get("available"), bool):
            raise ValueError(f"{doctor_id}: available must be a bool")
        
def validate_patients(patients):
    if not isinstance(patients, dict):
        raise ValueError("patients must be a dict")
    for patient_id, patient in patients.items():
        if not isinstance(patient_id, str) or not patient_id.strip():
            raise ValueError(f"Invalid patient id: {patient_id!r}")
        if patient_id != normalize_id(patient_id):
            raise ValueError(f"Patient id {patient_id!r} must be trimmed and upper-case")
        if not isinstance(patient, dict):
            raise ValueError(f"{patient_id}: patient must be a dict")
        name = patient.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"{patient_id}: missing or invalid name")
        city = patient.get("city")
        if not isinstance(city, str) or not city.strip():
            raise ValueError(f"{patient_id}: missing or invalid city")
        if not is_valid_age(patient.get("age")):
            raise ValueError(f"{patient_id}: invalid age")
        if not isinstance(patient.get("insurance"), bool):
            raise ValueError(f"{patient_id}: insurance must be a bool")

def validate_test_prices(test_prices):
    if not isinstance(test_prices, dict):
        raise ValueError("test_prices must be a dict")
    for test_name, price in test_prices.items():
        if not isinstance(test_name, str) or not test_name.strip():
            raise ValueError(f"Invalid test name: {test_name!r}")
        if not is_valid_amount(price):
            raise ValueError(f"{test_name}: invalid price")
    normalized_names = [normalize_id(t) for t in test_prices]
    if len(normalized_names) != len(set(normalized_names)):
        raise ValueError(f"Duplicate test name(s) after normalization: {test_prices}")

def to_money(value):
    """Convert a number to Decimal (via str, so 0.1 stays exactly 0.1)."""
    return Decimal(str(value))

def round_money(value):
    """Round a Decimal to 2 decimal places (half up, like a normal bill)."""
    return value.quantize(CENT, rounding=ROUND_HALF_UP)

def is_valid_amount(value):
    """True for a real, finite number from 0 to MAX_AMOUNT (bool is not accepted)."""
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        return False
    try:
        return math.isfinite(value) and 0 <= value <= MAX_AMOUNT
    except OverflowError:
        return False

def validate_clinic_config(config):
    if not isinstance(config, dict):
        raise ValueError("clinic config must be a dict")
    for key in ("insurance_consultation_rate", "insurance_test_rate", "senior_discount_rate"):
        rate = config.get(key)
        if not is_valid_amount(rate) or not isinstance(rate, (int, float, Decimal)) or rate > 1:
            raise ValueError(f"CLINIC_CONFIG[{key!r}] must be a number between 0 and 1")
    if not is_valid_age(config.get("senior_age_threshold")):
        raise ValueError("CLINIC_CONFIG['senior_age_threshold'] must be a non-negative number")
    
def calculate_test_charges(tests, test_prices=test_prices):
    if not isinstance(tests, list):
        raise ValueError("tests must be a list")
    test_prices_upper = {k.upper(): v for k, v in test_prices.items()}
    
    for t in tests:
        if not isinstance(t, str):
            raise ValueError(f"Invalid test name: {t!r}")
    normalized = [normalize_id(t) for t in tests]
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"Duplicate test(s) in: {tests}")
    
    total = Decimal("0")
    for t in tests:
        key = t.strip().upper()
        if key not in test_prices_upper:
            raise ValueError(f"Unknown test: {t}")
        price = test_prices_upper[key]
        if not is_valid_amount(price):
            raise ValueError(f"Invalid price for test {t!r}: {price!r}")
        total += to_money(price)
    return total

def calculate_insurance_coverage(consultation_fee, test_charges, has_insurance, config=CLINIC_CONFIG):
    if not is_valid_amount(consultation_fee):
        raise ValueError(f"Invalid consultation fee: {consultation_fee!r}")
    if not is_valid_amount(test_charges):
        raise ValueError(f"Invalid test charges: {test_charges!r}")
    if not isinstance(has_insurance, bool):
        raise ValueError(f"has_insurance must be True or False, not {has_insurance!r}")
    validate_clinic_config(config)
    if not has_insurance:
        return Decimal("0.00"), Decimal("0.00")
    consultation_coverage = to_money(consultation_fee) * to_money(config["insurance_consultation_rate"])
    test_coverage = to_money(test_charges) * to_money(config["insurance_test_rate"])
    return round_money(consultation_coverage), round_money(test_coverage)

def calculate_bill(consultation_fee, test_charges, has_insurance, age, config=CLINIC_CONFIG):
    if not is_valid_amount(consultation_fee):
        raise ValueError(f"Invalid consultation fee: {consultation_fee!r}")
    if not is_valid_amount(test_charges):
        raise ValueError(f"Invalid test charges: {test_charges!r}")
    if not is_valid_age(age):
        raise ValueError(f"Invalid age: {age!r}")
    if not isinstance(has_insurance, bool):
        raise ValueError(f"has_insurance must be True or False, not {has_insurance!r}")
    validate_clinic_config(config)
    fee = to_money(consultation_fee)
    tests_total = to_money(test_charges)

    subtotal = round_money(fee + tests_total)
    consultation_coverage, test_coverage = calculate_insurance_coverage(
        fee, tests_total, has_insurance, config
    )
    total_coverage = round_money(consultation_coverage + test_coverage)
    after_insurance = round_money(subtotal - total_coverage)

    senior_discount = Decimal("0.00")
    if age >= config["senior_age_threshold"]:
        senior_discount = round_money(after_insurance * to_money(config["senior_discount_rate"]))

    final_amount = round_money(after_insurance - senior_discount)

    return {
        "subtotal": subtotal,
        "consultation_coverage": consultation_coverage,
        "test_coverage": test_coverage,
        "total_coverage": total_coverage,
        "after_insurance": after_insurance,
        "senior_discount": senior_discount,
        "final_amount": final_amount
    }
    
def validate_report_inputs(appointments, processed_results):
    if not isinstance(appointments, (list, tuple)):
        raise ValueError("appointments must be a list")
    if not isinstance(processed_results, (list, tuple)):
        raise ValueError("processed_results must be a list")
    for a in appointments:
        if not isinstance(a, dict):
            raise ValueError("each appointment must be a dictionary")
        for key in ("patient_id", "doctor_id", "status"):
            if key not in a:
                raise ValueError(f"appointment is missing '{key}'")
    for r in processed_results:
        if not isinstance(r, dict):
            raise ValueError("each processed result must be a dictionary")
        for key in ("appointment_id", "status", "patient_id", "doctor_id"):
            if key not in r:
                raise ValueError(f"processed result is missing '{key}'")
        if r["status"] == "APPROVED":
            bill = r.get("bill")
            if not isinstance(bill, dict):
                raise ValueError("approved result is missing its bill")
            for key in ("final_amount", "total_coverage", "senior_discount"):
                if key not in bill:
                    raise ValueError(f"bill is missing '{key}'")
                if not is_valid_amount(bill[key]):
                    raise ValueError(f"bill has an invalid '{key}'")

def process_appointment(appointment, processed_appointment_ids=None,
                        patients=patients, doctors=doctors, test_prices=test_prices, config=CLINIC_CONFIG):
    if processed_appointment_ids is None:
        processed_appointment_ids = set()
    elif not isinstance(processed_appointment_ids, set):
        raise ValueError("processed_appointment_ids must be a set")
    
    if not isinstance(appointment, dict):
        return {"appointment_id": None, "status": "REJECTED",
                "reason": "Appointment must be a dictionary",
                "patient_id": None, "doctor_id": None}

    status = appointment.get("status")
    if isinstance(status, str):
        status = normalize_status(status)
        
    patient_id = normalize_id(appointment.get("patient_id"))
    doctor_id = normalize_id(appointment.get("doctor_id"))

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

    if status == "cancelled":
        return {"appointment_id": appointment_id, "status": "REJECTED",
                "reason": "Cannot process a cancelled appointment",
                "patient_id": patient_id, "doctor_id": doctor_id}
    is_valid, reason = validate_appointment(appointment, patients, doctors, test_prices)
    if not is_valid:
        return {"appointment_id": appointment_id, "status": "REJECTED",
                "reason": reason,
                "patient_id": patient_id, "doctor_id": doctor_id}

    if status == "pending":
        return {"appointment_id": appointment_id, "status": "PENDING",
                "reason": "Pending appointments cannot be billed until completed",
                "patient_id": patient_id, "doctor_id": doctor_id}

    patient_id = normalize_id(appointment["patient_id"])
    doctor_id = normalize_id(appointment["doctor_id"])
    patient = patients[patient_id]
    doctor = doctors[doctor_id]
    consultation_fee = doctor["fee"]
    try:
        test_charges = calculate_test_charges(appointment.get("tests", []), test_prices)
        bill = calculate_bill(
            consultation_fee,
            test_charges,
            patient["insurance"],
            patient["age"],
            config
        )
    except ValueError as e:
        return {"appointment_id": appointment_id, "status": "REJECTED",
                "reason": str(e),
                "patient_id": patient_id, "doctor_id": doctor_id}
    processed_appointment_ids.add(appointment_id)

    return {
    "appointment_id": appointment_id,
    "status": "APPROVED",
    "patient_id": patient_id,
    "doctor_id": doctor_id,
    "bill": bill
}
     
def cancel_appointment(appointment):
    if not isinstance(appointment, dict):
        return False, "Cannot cancel: appointment must be a dictionary"

    appointment_id = appointment.get("appointment_id")
    if not isinstance(appointment_id, str) or not appointment_id.strip():
        return False, "Cannot cancel: appointment_id is required"

    status = appointment.get("status")
    if isinstance(status, str):
        status = normalize_status(status)
    if status == "completed":
        return False, f"Cannot cancel: appointment {appointment.get('appointment_id')} is already completed"
    if status == "cancelled":
        return False, f"Cannot cancel: appointment {appointment.get('appointment_id')} is already cancelled"
    if status == "pending":
        appointment["status"] = "cancelled"
        return True, f"Appointment {appointment.get('appointment_id')} cancelled successfully"

    return False, f"Invalid status: {status}"

def process_all_appointments(appointments, patients=patients, doctors=doctors, test_prices=test_prices, config=CLINIC_CONFIG):
    if not isinstance(appointments, (list, tuple)):
        raise ValueError("appointments must be a list")
    processed_ids = set()
    results = []
    for a in appointments:
        result = process_appointment(a, processed_ids, patients, doctors, test_prices, config)
        results.append(result)
    return results

def generate_doctor_report(doctor_id, appointments, processed_results, doctors=doctors):
    validate_report_inputs(appointments, processed_results)
    doctor_id = normalize_id(doctor_id)
    doctor = doctors.get(doctor_id) if isinstance(doctor_id, str) else None
    if not doctor:
        return None, f"Doctor {doctor_id} does not exist"

    doctor_appointments = [a for a in appointments if normalize_id(a["doctor_id"]) == doctor_id]
    total = len(doctor_appointments)
    completed = len([a for a in doctor_appointments if normalize_status(a["status"]) == "completed"])
    cancelled = len([a for a in doctor_appointments if normalize_status(a["status"]) == "cancelled"])
    pending = len([a for a in doctor_appointments if normalize_status(a["status"]) == "pending"])

    doctor_results = [r for r in processed_results if r["doctor_id"] == doctor_id]
    bills = [r["bill"]["final_amount"] for r in doctor_results if r["status"] == "APPROVED"]

    revenue = sum(bills, Decimal("0.00"))
    average_bill = round_money(revenue / len(bills)) if bills else Decimal("0.00")


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
    validate_report_inputs(appointments, processed_results)
    patient_id = normalize_id(patient_id)
    patient = patients.get(patient_id) if isinstance(patient_id, str) else None
    if not patient:
        return None, f"Patient {patient_id} does not exist"
    patient_appointments = [a for a in appointments if normalize_id(a["patient_id"]) == patient_id]
    patient_results = [r for r in processed_results if r["patient_id"] == patient_id]
    total_spent = Decimal("0.00")
    total_saved = Decimal("0.00")
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
    
def generate_clinic_report(appointments, processed_results, patients=patients, doctors=doctors, config=CLINIC_CONFIG):
    validate_report_inputs(appointments, processed_results)
    total_appointments = len(appointments)
    completed = [a for a in appointments if normalize_status(a["status"]) == "completed"]
    cancelled = [a for a in appointments if normalize_status(a["status"]) == "cancelled"]
    pending = [a for a in appointments if normalize_status(a["status"]) == "pending"]

    total_revenue = sum(
        (r["bill"]["final_amount"] for r in processed_results if r["status"] == "APPROVED"),
        Decimal("0.00")
    )

    appts_per_doctor = {d: len([a for a in appointments if normalize_id(a["doctor_id"]) == d]) for d in doctors}
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
        top_doctor = (
            [name for name, rev in doctor_revenue.items() if rev == highest_revenue]
            if highest_revenue > 0 else []
        )
    else:
        top_doctor = []

    insured_patients = [p for p in patients.values() if p["insurance"]]
    senior_patients = [p for p in patients.values() if p["age"] >= config["senior_age_threshold"]]

    patient_reports = []
    for p in patients:
        report, _ = generate_patient_report(p, appointments, processed_results, patients)
        patient_reports.append(report)

    if patient_reports:
        highest_spent = max(r["total_spent"] for r in patient_reports)
        highest_spending_patient = (
            [r["name"] for r in patient_reports if r["total_spent"] == highest_spent]
            if highest_spent > 0 else []
        )
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
    for bill in bills:
        if not is_valid_amount(bill):
            raise ValueError(f"Invalid bill amount: {bill!r}")
    return sum((to_money(bill) for bill in bills), Decimal("0"))

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

def calculate_bill_kwargs(consultation_fee, **options):
    allowed_keys = {"insurance", "senior_discount", "age", "tests", "include_tests", "config", "test_prices"}
    unknown = set(options) - allowed_keys
    if unknown:
        return None, f"Unknown option(s): {', '.join(sorted(unknown))}"

    has_insurance = options.get("insurance", False)
    apply_senior = options.get("senior_discount", False)
    include_tests = options.get("include_tests", True)
    config = options.get("config", CLINIC_CONFIG)
    prices = options.get("test_prices", test_prices)
    tests = options.get("tests", [])

    if apply_senior and "age" not in options:
        return None, "age is required when senior_discount is True"

    age = options.get("age", 0)

    if not isinstance(has_insurance, bool):
        return None, "insurance must be a bool"
    if not isinstance(apply_senior, bool):
        return None, "senior_discount must be a bool"
    if not isinstance(include_tests, bool):
        return None, "include_tests must be a bool"
    if not is_valid_amount(consultation_fee):
        return None, "consultation_fee must be a non-negative number"
    if not is_valid_age(age):
        return None, "age must be a non-negative number"
    if not isinstance(tests, list):
        return None, "tests must be a list"
    if not all(isinstance(t, str) for t in tests):
        return None, f"tests must be a list of strings: {tests}"
    normalized_tests = [normalize_id(t) for t in tests]
    if len(normalized_tests) != len(set(normalized_tests)):
        return None, f"Duplicate test(s) in: {tests}"

    tests = tests if include_tests else []
    try:
        validate_test_prices(prices)
        test_charges = calculate_test_charges(tests, prices)
        bill = calculate_bill(
            consultation_fee,
            test_charges,
            has_insurance,
            age if apply_senior else 0,
            config
        )
    except ValueError as e:
        return None, str(e)
    return bill["final_amount"], None

def main():
    appts = copy.deepcopy(appointments)
    validate_clinic_config(CLINIC_CONFIG)
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
            print(f"{result['appointment_id']} -> {result['status']} | Reason: {result['reason']}")
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
    print("   UTILITY FUNCTIONS ")
    print("=" * 40)
    print("combine_bills(5850, 2250, 1000) ->", combine_bills(5850, 2250, 1000))
    print("search_patients(insurance=True) ->", search_patients(insurance=True))
    result, error = calculate_bill_kwargs(5000, insurance=True, senior_discount=True, age=67, tests=["ECG"])
    print("calculate_bill_kwargs demo ->", result)
    
    print("\n" + "=" * 40)
    print("   DOUBLE-BOOKING CHECK")
    print("=" * 40)
    double_booking_demo = [
        {"appointment_id": "DB1", "patient_id": "P001", "doctor_id": "D001",
         "status": "completed", "tests": [], "time_slot": "2026-11-10 10:00"},
        {"appointment_id": "DB2", "patient_id": "P002", "doctor_id": "D001",
         "status": "completed", "tests": [], "time_slot": "2026-11-10 10:00"},
    ]
    conflicts = find_double_bookings(double_booking_demo)
    if conflicts:
        for doctor_id, slot in conflicts:
            print(f"Conflict: doctor {doctor_id} double-booked at {slot}")
    else:
        print("No conflicts found")

if __name__ == "__main__":
    main()
