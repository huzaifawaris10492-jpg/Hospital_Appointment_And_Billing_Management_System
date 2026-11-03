# Hospital Management System

A Python appointment and billing system for a small clinic. It validates appointments, calculates bills (with insurance coverage and senior discounts), and generates doctor, patient, and clinic-wide reports.

## Project Structure

```
Hospital Management System/
├── Appointment_and_Bolling_system.py   # Main application code
├── Test_file.py                        # Unit tests (unittest)
└── README.md
```

## Requirements

- Python 3.8+
- No external packages needed (standard library only)

## Run the Program

```bash
python Appointment_and_Bolling_system.py
```

This processes the sample appointments and prints the billing results, a cancellation test, the doctor/patient reports, and the clinic dashboard.

## Run the Tests

From the project folder:

```bash
python -m unittest Test_file -v
```

## Features

- **Appointment validation** – checks patient, doctor, doctor availability, status, tests, duplicate tests, and patient age.
- **Billing** – consultation fee + test charges, with:
  - Insurance: covers 20% of the consultation fee and 50% of test charges
  - Senior discount: 10% off the post-insurance amount for patients aged 60+
- **Appointment processing** – approves or rejects appointments and blocks duplicate/cancelled ones.
  - Only completed appointments are billed; pending ones are rejected until completed.
- **Cancellation** – only `pending` appointments can be cancelled.
- **Reports** – per-doctor, per-patient, and clinic dashboard (revenue, top doctor, most requested doctor, insured/senior counts, etc.).
- **Utilities** – `combine_bills(*bills)`, `search_patients(**criteria)`, `calculate_bill_kwargs(...)`.

## Configuration

Rates are set in `CLINIC_CONFIG`:

| Key | Default | Meaning |
|---|---|---|
| `senior_age_threshold` | 60 | Age at which the senior discount applies |
| `insurance_consultation_rate` | 0.20 | Insurance share of consultation fee |
| `insurance_test_rate` | 0.50 | Insurance share of test charges |
| `senior_discount_rate` | 0.10 | Senior discount rate |

## Main Functions

| Function | Purpose |
|---|---|
| `validate_appointment(appointment)` | Returns `(is_valid, reason)` |
| `calculate_bill(fee, test_charges, has_insurance, age)` | Returns a full bill breakdown dict |
| `process_appointment(appointment, processed_ids)` | Returns an `APPROVED` or `REJECTED` result |
| `cancel_appointment(appointment)` | Returns `(success, message)` |
| `generate_doctor_report(doctor_id, appointments, results)` | Doctor stats and revenue |
| `generate_patient_report(patient_id, appointments, results)` | Patient spending and savings |
| `generate_clinic_report(appointments, results)` | Clinic-wide dashboard |

## Billing Example

Insured patient, consultation 5000 + tests 2500:

- Subtotal: 7500
- Insurance coverage: 1000 + 1250 = 2250
- Patient pays: **5250**

## Sample Data

- Patients: `P001`–`P004`
- Doctors: `D001` (Cardiology), `D002` (Dermatology), `D003` (General)
- Tests: ECG, Blood Test, X-Ray, MRI# Hospital_Appointment_And_Billing_Management_System
