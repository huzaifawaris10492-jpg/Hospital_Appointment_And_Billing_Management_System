import copy
import unittest

import Appointment_and_Billing_system as hms
from Appointment_and_Billing_system import (
    CLINIC_CONFIG,
    calculate_bill,
    calculate_bill_kwargs,
    calculate_insurance_coverage,
    calculate_test_charges,
    calculate_total,
    cancel_appointment,
    combine_bills,
    generate_clinic_report,
    generate_doctor_report,
    generate_patient_report,
    get_senior_threshold,
    process_all_appointments,
    process_appointment,
    search_patients,
    validate_appointment,
    validate_doctors,
    validate_patients,
    validate_test_prices,
)


def make_appt(appointment_id="X1", patient_id="P001", doctor_id="D001",
              status="pending", tests=None):
    return {
        "appointment_id": appointment_id,
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "status": status,
        "tests": [] if tests is None else tests,
    }


def doctor_report_of(doctor_id, appts, results):
    report, status = generate_doctor_report(doctor_id, appts, results)
    assert report is not None, status
    return report


def patient_report_of(patient_id, appts, results):
    report, status = generate_patient_report(patient_id, appts, results)
    assert report is not None, status
    return report


class BaseTestCase(unittest.TestCase):
    """Snapshots the module-level data before each test and restores it after."""

    def setUp(self):
        self._backup = {
            name: copy.deepcopy(getattr(hms, name))
            for name in ("patients", "doctors", "appointments", "test_prices")
        }

    def tearDown(self):
        for name, value in self._backup.items():
            target = getattr(hms, name)
            if isinstance(target, dict):
                target.clear()
                target.update(value)
            else:
                target[:] = value


class TestValidateAppointment(BaseTestCase):

    def test_valid_appointment(self):
        ok, reason = validate_appointment(hms.appointments[0])
        self.assertTrue(ok)
        self.assertEqual(reason, "Valid")

    def test_not_a_dict(self):
        ok, _ = validate_appointment("not a dict")
        self.assertFalse(ok)

    def test_invalid_patient_id(self):
        ok, reason = validate_appointment(make_appt(patient_id="P999"))
        self.assertFalse(ok)
        self.assertIn("P999", reason)

    def test_invalid_doctor_id(self):
        ok, reason = validate_appointment(make_appt(doctor_id="D999"))
        self.assertFalse(ok)
        self.assertIn("D999", reason)

    def test_doctor_unavailable(self):
        hms.doctors["D001"]["available"] = False
        ok, reason = validate_appointment(make_appt())
        self.assertFalse(ok)
        self.assertIn("Dr. Hassan", reason)

    def test_invalid_status(self):
        ok, _ = validate_appointment(make_appt(status="bogus"))
        self.assertFalse(ok)

    def test_invalid_test(self):
        ok, reason = validate_appointment(make_appt(tests=["UNKNOWN"]))
        self.assertFalse(ok)
        self.assertIn("UNKNOWN", reason)

    def test_duplicate_test(self):
        ok, reason = validate_appointment(make_appt(tests=["ECG", "ECG"]))
        self.assertFalse(ok)
        self.assertIn("Duplicate", reason)

    def test_empty_test_list_is_valid(self):
        ok, _ = validate_appointment(make_appt(tests=[]))
        self.assertTrue(ok)

    def test_negative_age(self):
        hms.patients["P001"]["age"] = -5
        ok, _ = validate_appointment(make_appt())
        self.assertFalse(ok)

    def test_boolean_age_rejected(self):
        hms.patients["P001"]["age"] = True
        ok, _ = validate_appointment(make_appt())
        self.assertFalse(ok)


class TestValidateConfigData(BaseTestCase):

    def test_validate_doctors_ok(self):
        validate_doctors(hms.doctors)  # should not raise

    def test_validate_doctors_not_dict(self):
        with self.assertRaises(ValueError):
            validate_doctors([])

    def test_validate_doctors_bad_fee(self):
        bad = {"D1": {"name": "A", "specialization": "B", "fee": -1, "available": True}}
        with self.assertRaises(ValueError):
            validate_doctors(bad)

    def test_validate_doctors_bool_fee(self):
        bad = {"D1": {"name": "A", "specialization": "B", "fee": True, "available": True}}
        with self.assertRaises(ValueError):
            validate_doctors(bad)

    def test_validate_doctors_missing_name(self):
        bad = {"D1": {"specialization": "B", "fee": 10, "available": True}}
        with self.assertRaises(ValueError):
            validate_doctors(bad)

    def test_validate_doctors_available_not_bool(self):
        bad = {"D1": {"name": "A", "specialization": "B", "fee": 10, "available": "yes"}}
        with self.assertRaises(ValueError):
            validate_doctors(bad)

    def test_validate_test_prices_ok(self):
        validate_test_prices(hms.test_prices)  # should not raise

    def test_validate_test_prices_negative(self):
        with self.assertRaises(ValueError):
            validate_test_prices({"ECG": -10})

    def test_validate_test_prices_not_dict(self):
        with self.assertRaises(ValueError):
            validate_test_prices(["ECG"])

class TestValidatePatients(BaseTestCase):

    def test_valid_patients(self):
        validate_patients(hms.patients)  # should not raise

    def test_not_dict(self):
        with self.assertRaises(ValueError):
            validate_patients([])

    def test_missing_name(self):
        bad = {"P1": {"age": 30, "city": "X", "insurance": True}}
        with self.assertRaises(ValueError):
            validate_patients(bad)

    def test_negative_age(self):
        bad = {"P1": {"name": "A", "age": -1, "city": "X", "insurance": True}}
        with self.assertRaises(ValueError):
            validate_patients(bad)

    def test_insurance_not_bool(self):
        bad = {"P1": {"name": "A", "age": 30, "city": "X", "insurance": "yes"}}
        with self.assertRaises(ValueError):
            validate_patients(bad)

class TestBilling(BaseTestCase):

    def test_calculate_test_charges(self):
        self.assertEqual(calculate_test_charges(["ECG", "Blood Test"]), 2500)

    def test_calculate_test_charges_empty(self):
        self.assertEqual(calculate_test_charges([]), 0)

    def test_calculate_test_charges_unknown_test_counts_zero(self):
        self.assertEqual(calculate_test_charges(["UNKNOWN"]), 0)

    def test_calculate_total(self):
        self.assertEqual(calculate_total(5000, 1500, 1000), 7500)

    def test_calculate_total_default_other_charges(self):
        self.assertEqual(calculate_total(5000, 1500), 6500)

    def test_insurance_coverage(self):
        consult_cov, test_cov = calculate_insurance_coverage(5000, 2500, True)
        self.assertEqual(consult_cov, 1000)
        self.assertEqual(test_cov, 1250)

    def test_no_insurance_coverage(self):
        self.assertEqual(calculate_insurance_coverage(5000, 2500, False), (0, 0))

    def test_bill_with_insurance(self):
        bill = calculate_bill(5000, 2500, True, 32)
        self.assertEqual(bill["subtotal"], 7500)
        self.assertEqual(bill["total_coverage"], 2250)
        self.assertEqual(bill["after_insurance"], 5250)
        self.assertEqual(bill["senior_discount"], 0)
        self.assertEqual(bill["final_amount"], 5250)

    def test_bill_senior_discount(self):
        bill = calculate_bill(5000, 0, False, 65)
        self.assertEqual(bill["senior_discount"], 500)
        self.assertEqual(bill["final_amount"], 4500)

    def test_bill_senior_threshold_boundary(self):
        self.assertEqual(calculate_bill(5000, 0, False, 59)["senior_discount"], 0)
        self.assertEqual(calculate_bill(5000, 0, False, 60)["senior_discount"], 500)

    def test_bill_insurance_and_senior(self):
        bill = calculate_bill(5000, 2500, True, 70)
        self.assertEqual(bill["final_amount"], 4725)

    def test_get_senior_threshold(self):
        self.assertEqual(get_senior_threshold(), CLINIC_CONFIG["senior_age_threshold"])
        self.assertEqual(get_senior_threshold(), 60)

    def test_bill_rounded_to_two_decimals(self):
        bill = calculate_bill(3333, 0, True, 67)
        self.assertEqual(bill["consultation_coverage"], 666.6)
        self.assertEqual(bill["senior_discount"], 266.64)
        self.assertEqual(bill["final_amount"], 2399.76)

class TestCalculateBillKwargs(BaseTestCase):

    def test_basic(self):
        result, error = calculate_bill_kwargs(5000, insurance=False, senior_discount=False, tests=[])
        self.assertEqual(result, 5000)
        self.assertIsNone(error)

    def test_insurance_senior_and_tests(self):
        result, error = calculate_bill_kwargs(
            5000, insurance=True, senior_discount=True, age=67, tests=["ECG"]
        )
        self.assertIsNone(error)
        self.assertIsNotNone(result)
        self.assertAlmostEqual(float(result or 0), 4275)

    def test_senior_flag_but_too_young(self):
        result, _ = calculate_bill_kwargs(5000, senior_discount=True, age=30)
        self.assertEqual(result, 5000)

    def test_include_tests_false_ignores_tests(self):
        result, _ = calculate_bill_kwargs(5000, tests=["ECG"], include_tests=False)
        self.assertEqual(result, 5000)

    def test_unknown_option(self):
        result, error = calculate_bill_kwargs(5000, bogus=1)
        self.assertIsNone(result)
        self.assertIn("bogus", str(error))

    def test_invalid_types(self):
        for kwargs, fragment in [
            ({"insurance": "yes"}, "insurance"),
            ({"senior_discount": 1}, "senior_discount"),
            ({"include_tests": "no"}, "include_tests"),
            ({"age": "old"}, "age"),
            ({"age": True}, "age"),
            ({"tests": "ECG"}, "tests"),
        ]:
            with self.subTest(kwargs=kwargs):
                result, error = calculate_bill_kwargs(5000, **kwargs)
                self.assertIsNone(result)
                self.assertIn(fragment, str(error))


class TestProcessAppointment(BaseTestCase):

    def test_approved_insured(self):
        result = process_appointment(hms.appointments[0])
        self.assertEqual(result["status"], "APPROVED")
        self.assertEqual(result["bill"]["final_amount"], 5250)

    def test_approved_senior_uninsured(self):
        result = process_appointment(hms.appointments[3])
        self.assertEqual(result["status"], "APPROVED")
        self.assertEqual(result["bill"]["final_amount"], 5850)

    def test_rejected_invalid_patient(self):
        result = process_appointment(make_appt(patient_id="P999"))
        self.assertEqual(result["status"], "REJECTED")

    def test_rejected_cancelled(self):
        result = process_appointment(make_appt(status="cancelled"))
        self.assertEqual(result["status"], "REJECTED")
        self.assertIn("cancelled", result["reason"])

    def test_duplicate_processing_rejected_with_shared_set(self):
        processed = set()
        first = process_appointment(hms.appointments[0], processed)
        second = process_appointment(hms.appointments[0], processed)
        self.assertEqual(first["status"], "APPROVED")
        self.assertEqual(second["status"], "REJECTED")
        self.assertIn("already processed", second["reason"])

    def test_without_shared_set_each_call_is_independent(self):
        r1 = process_appointment(hms.appointments[0])
        r2 = process_appointment(hms.appointments[0])
        self.assertEqual(r1["bill"]["final_amount"], r2["bill"]["final_amount"])

    def test_process_all_appointments(self):
        results = process_all_appointments(hms.appointments)
        self.assertEqual([r["status"] for r in results],
                         ["APPROVED", "APPROVED", "REJECTED", "APPROVED"])

    def test_process_all_rejects_duplicate_ids(self):
        appts = [hms.appointments[0], copy.deepcopy(hms.appointments[0])]
        results = process_all_appointments(appts)
        self.assertEqual(results[0]["status"], "APPROVED")
        self.assertEqual(results[1]["status"], "REJECTED")
    
    def test_pending_appointment_not_billed(self):
        result = process_appointment(make_appt(status="pending", tests=["MRI"]))
        self.assertEqual(result["status"], "REJECTED")
        self.assertIn("Pending", result["reason"])
        
    def test_missing_appointment_id_rejected(self):
        appt = make_appt(status="completed")
        del appt["appointment_id"]
        self.assertEqual(process_appointment(appt)["status"], "REJECTED")

    def test_blank_appointment_id_rejected(self):
        result = process_appointment(make_appt(appointment_id="   ", status="completed"))
        self.assertEqual(result["status"], "REJECTED")

    def test_ids_compared_case_and_space_insensitive(self):
        processed = set()
        first = process_appointment(make_appt(appointment_id="A1", status="completed"), processed)
        second = process_appointment(make_appt(appointment_id=" a1 ", status="completed"), processed)
        self.assertEqual(first["status"], "APPROVED")
        self.assertEqual(second["status"], "REJECTED")
        
    def test_process_with_custom_data(self):
        pts = {"X1": {"name": "Z", "age": 70, "city": "C", "insurance": False}}
        docs = {"Q1": {"name": "Dr Q", "specialization": "S", "fee": 1000, "available": True}}
        prices = {"ECG": 100}
        appt = make_appt(appointment_id="1", patient_id="X1", doctor_id="Q1",
                         status="completed", tests=["ECG"])
        result = process_appointment(appt, None, pts, docs, prices)
        self.assertEqual(result["status"], "APPROVED")
        self.assertEqual(result["bill"]["final_amount"], 990)
    
class TestCancelAppointment(BaseTestCase):

    def test_cancel_pending(self):
        appt = make_appt(status="pending")
        ok, msg = cancel_appointment(appt)
        self.assertTrue(ok)
        self.assertEqual(appt["status"], "cancelled")
        self.assertIn("cancelled successfully", msg)

    def test_cancel_completed_fails(self):
        appt = make_appt(status="completed")
        ok, _ = cancel_appointment(appt)
        self.assertFalse(ok)
        self.assertEqual(appt["status"], "completed")

    def test_cancel_already_cancelled_fails(self):
        ok, _ = cancel_appointment(make_appt(status="cancelled"))
        self.assertFalse(ok)

    def test_cancel_invalid_status_fails(self):
        ok, msg = cancel_appointment(make_appt(status="weird"))
        self.assertFalse(ok)
        self.assertIn("Invalid status", msg)


class TestReports(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.results = process_all_appointments(hms.appointments)

    def test_doctor_report_valid(self):
        report = doctor_report_of("D001", hms.appointments, self.results)
        self.assertEqual(report["name"], "Dr. Hassan")
        self.assertEqual(report["total_appointments"], 2)
        self.assertEqual(report["completed"], 2)
        self.assertEqual(report["cancelled"], 0)
        self.assertEqual(report["pending"], 0)
        self.assertEqual(report["revenue"], 11100)
        self.assertEqual(report["average_bill"], 5550)

    def test_doctor_report_invalid_id(self):
        report, status = generate_doctor_report("D999", hms.appointments, self.results)
        self.assertIsNone(report)
        self.assertIn("D999", status)

    def test_doctor_report_with_cancelled_appointment(self):
        report = doctor_report_of("D002", hms.appointments, self.results)
        self.assertEqual(report["cancelled"], 1)
        self.assertEqual(report["revenue"], 0)
        self.assertEqual(report["average_bill"], 0)

    def test_doctor_with_no_appointments(self):
        hms.doctors["D_EMPTY"] = {"name": "Dr. Empty", "specialization": "None",
                                  "fee": 1000, "available": True}
        report = doctor_report_of("D_EMPTY", hms.appointments, self.results)
        self.assertEqual(report["total_appointments"], 0)
        self.assertEqual(report["revenue"], 0)
        self.assertEqual(report["average_bill"], 0)

    def test_patient_report_valid(self):
        report = patient_report_of("P001", hms.appointments, self.results)
        self.assertEqual(report["name"], "Ali Khan")
        self.assertEqual(report["completed_visits"], ["A001"])
        self.assertEqual(report["total_spent"], 5250)
        self.assertEqual(report["total_saved"], 2250)

    def test_patient_report_senior_savings(self):
        report = patient_report_of("P004", hms.appointments, self.results)
        self.assertEqual(report["total_spent"], 5850)
        self.assertEqual(report["total_saved"], 650)

    def test_patient_report_no_approved_visits(self):
        report = patient_report_of("P003", hms.appointments, self.results)
        self.assertEqual(report["completed_visits"], [])
        self.assertEqual(report["total_spent"], 0)

    def test_patient_report_invalid_id(self):
        report, status = generate_patient_report("P999", hms.appointments, self.results)
        self.assertIsNone(report)
        self.assertIn("P999", status)

    def test_clinic_report(self):
        dash = generate_clinic_report(hms.appointments, self.results)
        self.assertEqual(dash["total_appointments"], 4)
        self.assertEqual(dash["completed"], 3)
        self.assertEqual(dash["cancelled"], 1)
        self.assertEqual(dash["pending"], 0)
        self.assertEqual(dash["total_revenue"], 13100)
        self.assertEqual(dash["top_doctor"], ["Dr. Hassan"])
        self.assertEqual(dash["most_requested_doctor"], ["Dr. Hassan"])
        self.assertEqual(dash["insured_patient_count"], 2)
        self.assertEqual(dash["senior_patient_count"], 1)
        self.assertEqual(dash["highest_spending_patient"], ["Usman Ali"])
        self.assertEqual(dash["patients_no_completed_appointment"], ["Sara Ahmed"])

    def test_clinic_report_empty_appointments(self):
        dash = generate_clinic_report([], [])
        self.assertEqual(dash["total_appointments"], 0)
        self.assertEqual(dash["total_revenue"], 0)
        self.assertEqual(dash["completed"], 0)
        self.assertEqual(dash["most_requested_doctor"], [])
    
    def test_most_requested_doctor_tie_returns_all(self):
        appts = [make_appt("T1", doctor_id="D001", status="completed"),
                 make_appt("T2", doctor_id="D002", status="completed")]
        results = process_all_appointments(appts)
        dash = generate_clinic_report(appts, results)
        self.assertEqual(dash["most_requested_doctor"], ["Dr. Hassan", "Dr. Sara"])

class TestArgsKwargs(BaseTestCase):

    def test_combine_bills(self):
        self.assertEqual(combine_bills(100, 200, 300), 600)

    def test_combine_bills_empty(self):
        self.assertEqual(combine_bills(), 0)

    def test_search_by_insurance(self):
        result = search_patients(insurance=True)
        self.assertEqual(sorted(result), ["P001", "P003"])

    def test_search_multiple_criteria(self):
        self.assertEqual(sorted(search_patients(insurance=True, city="Lahore")),
                         ["P001", "P003"])

    def test_search_no_match(self):
        self.assertEqual(search_patients(city="Karachi"), [])

    def test_search_no_criteria_returns_all(self):
        self.assertEqual(len(search_patients()), len(hms.patients))

    def test_search_unknown_field_raises(self):
        with self.assertRaises(ValueError):
            search_patients(cty="Lahore")

if __name__ == "__main__":
    unittest.main(verbosity=2)