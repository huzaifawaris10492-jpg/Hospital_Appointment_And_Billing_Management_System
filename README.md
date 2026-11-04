# Hospital Management System

A Python appointment and billing system for a small clinic. It validates appointments, calculates bills (with insurance coverage and senior discounts), and generates doctor, patient, and clinic-wide reports.

## Project Structure

```
Hospital Management System/
├── Appointment_and_Billing_system.py   # Main application code
├── test_hospital_billing.py            # Unit tests (unittest)
├── .gitignore
└── README.md
```

## Requirements

- Python 3.8+
- No external packages needed (standard library only)

## Run the Program

```bash
python Appointment_and_Billing_system.py
```

This processes the sample appointments and prints the billing results, a cancellation test, the doctor/patient reports, the clinic dashboard, and a demo of the utility functions.

## Run the Tests

From the project folder:

```bash
python -m unittest -v
```

## Features

- **Appointment validation** – checks patient, doctor, doctor availability, status, tests, duplicate tests, and patient age and insurance. Malformed appointments are rejected with a clear reason instead of crashing.
- **Billing** – consultation fee + test charges, with:
  - Insurance: covers 20% of the consultation fee and 50% of test charges
  - Senior discount: 10% off the post-insurance amount for patients aged 60+
  - All rates are read from `CLINIC_CONFIG`; money is calculated with `Decimal` and rounded to 2 decimals
- **Appointment processing** – approves or rejects appointments and blocks duplicate and cancelled ones.
  - Only `completed` appointments are billed; `pending` ones are rejected until completed.
  - Appointment, patient, and doctor IDs are trimmed and upper-cased before matching (`" a1 "` equals `"A1"`).
- **Cancellation** – only `pending` appointments can be cancelled.
- **Reports** – per-doctor, per-patient, and clinic dashboard (revenue, top doctor, most requested doctor, insured/senior counts, etc.). Report inputs are validated.
- **Data validation** – `validate_patients`, `validate_doctors`, `validate_test_prices`, and `validate_clinic_config` check the reference data and rates.
- **Utilities** – `combine_bills(*bills)`, `search_patients(**criteria)` (unknown fields raise `ValueError`), `calculate_bill_kwargs(...)`.

## Configuration

Rates are set in `CLINIC_CONFIG` (rates must be between 0 and 1):

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
| `calculate_bill(fee, test_charges, has_insurance, age)` | Returns a full bill breakdown dict (`Decimal` values) |
| `process_appointment(appointment, processed_ids)` | Returns an `APPROVED` or `REJECTED` result |
| `process_all_appointments(appointments)` | Processes a list and blocks duplicate IDs |
| `cancel_appointment(appointment)` | Returns `(success, message)` |
| `generate_doctor_report(doctor_id, appointments, results)` | Doctor stats and revenue |
| `generate_patient_report(patient_id, appointments, results)` | Patient spending and savings |
| `generate_clinic_report(appointments, results)` | Clinic-wide dashboard |

## Billing Example

Insured patient, consultation 5000 + tests 2500:

- Subtotal: 7500
- Insurance coverage: 1000 + 1250 = 2250
- Patient pays: **5250**

## Error Handling

- Appointment problems (unknown patient or doctor, bad tests, pending status, missing ID) return a `REJECTED` result with a `reason`.
- Invalid data passed to billing, validation, or report functions raises `ValueError`.
- `calculate_bill_kwargs` returns `(None, error_message)` instead of raising.

## Sample Data

- Patients: `P001`–`P004`
- Doctors: `D001` (Cardiology), `D002` (Dermatology), `D003` (General)
- Tests: ECG, Blood Test, X-Ray, MRI