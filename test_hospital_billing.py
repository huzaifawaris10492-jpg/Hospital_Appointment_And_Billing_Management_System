import copy
import unittest
from decimal import Decimal

import Appointment_and_Billing_system as hms
from Appointment_and_Billing_system import (
    CLINIC_CONFIG,
    calculate_bill,
    calculate_bill_kwargs,
    calculate_insurance_coverage,
    calculate_test_charges,
    cancel_appointment,
    is_valid_age,
    find_double_bookings,
    combine_bills,
    generate_clinic_report,
    generate_doctor_report,
    generate_patient_report,
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
        
    def test_doctor_record_not_a_dict(self):
        hms.doctors["D001"] = "bad"  # type: ignore
        ok, reason = validate_appointment(make_appt())
        self.assertFalse(ok)
        self.assertIn("D001", reason)

    def test_doctor_missing_fee(self):
        del hms.doctors["D001"]["fee"]
        ok, reason = validate_appointment(make_appt())
        self.assertFalse(ok)
        self.assertIn("fee", reason)

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

    def test_patient_record_not_a_dict(self):
        hms.patients["P001"] = "bad"  # type: ignore
        ok, reason = validate_appointment(make_appt())
        self.assertFalse(ok)
        self.assertIn("P001", reason)

    def test_patient_missing_age(self):
        del hms.patients["P001"]["age"]
        ok, reason = validate_appointment(make_appt())
        self.assertFalse(ok)
        self.assertIn("age", reason)

    def test_patient_missing_insurance(self):
        del hms.patients["P001"]["insurance"]
        ok, reason = validate_appointment(make_appt())
        self.assertFalse(ok)
        self.assertIn("insurance", reason)

    def test_patient_insurance_not_bool(self):
        hms.patients["P001"]["insurance"] = "yes"
        ok, _ = validate_appointment(make_appt())
        self.assertFalse(ok)

    def test_nan_age_rejected(self):
        hms.patients["P001"]["age"] = float("nan")
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
    
    def test_validate_doctors_empty_name(self):
        bad = {"D1": {"name": "  ", "specialization": "B", "fee": 10, "available": True}}
        with self.assertRaises(ValueError):
            validate_doctors(bad)

    def test_validate_doctors_bad_key(self):
        bad = {1: {"name": "A", "specialization": "B", "fee": 10, "available": True}}
        with self.assertRaises(ValueError):
            validate_doctors(bad)  # type: ignore

    def test_validate_doctors_nan_fee(self):
        bad = {"D1": {"name": "A", "specialization": "B", "fee": float("nan"), "available": True}}
        with self.assertRaises(ValueError):
            validate_doctors(bad)

    def test_validate_test_prices_empty_name(self):
        with self.assertRaises(ValueError):
            validate_test_prices({"": 100})

    def test_validate_test_prices_bad_key(self):
        with self.assertRaises(ValueError):
            validate_test_prices({5: 100})  # type: ignore
            
    def test_validate_doctors_record_not_a_dict(self):
        with self.assertRaises(ValueError):
            validate_doctors({"D1": "bad"})  # type: ignore

    def test_validate_patients_record_not_a_dict(self):
        with self.assertRaises(ValueError):
            validate_patients({"P1": "bad"})  # type: ignore
            
    def test_validate_test_prices_case_collision(self):
        with self.assertRaises(ValueError):
            validate_test_prices({"X-Ray": 2500, "x-ray": 9999})

    def test_validate_test_prices_whitespace_collision(self):
        with self.assertRaises(ValueError):
            validate_test_prices({"ECG": 1500, " ecg ": 1500})

    def test_calculate_test_charges_uses_correct_price_no_collision(self):
        result = calculate_test_charges(["ECG"], {"ECG": 1500, "X-Ray": 2500})
        self.assertEqual(result, 1500)

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
            
    def test_empty_name(self):
        bad = {"P1": {"name": "", "age": 30, "city": "X", "insurance": True}}
        with self.assertRaises(ValueError):
            validate_patients(bad)

    def test_bad_key(self):
        bad = {7: {"name": "A", "age": 30, "city": "X", "insurance": True}}
        with self.assertRaises(ValueError):
            validate_patients(bad)  # type: ignore
            
    def test_age_at_cap_is_valid(self):
        self.assertTrue(is_valid_age(130))

    def test_age_over_cap_is_invalid(self):
        self.assertFalse(is_valid_age(131))

    def test_age_unrealistically_large_is_invalid(self):
        self.assertFalse(is_valid_age(1_000_000_000))

    def test_patients_rejects_age_over_cap(self):
        bad = {"P1": {"name": "A", "age": 131, "city": "X", "insurance": True}}
        with self.assertRaises(ValueError):
            validate_patients(bad)

class TestBilling(BaseTestCase):

    def test_calculate_test_charges(self):
        self.assertEqual(calculate_test_charges(["ECG", "Blood Test"]), 2500)

    def test_calculate_test_charges_empty(self):
        self.assertEqual(calculate_test_charges([]), 0)

    def test_calculate_test_charges_unknown_test_raises(self):
        with self.assertRaises(ValueError):
            calculate_test_charges(["UNKNOWN"])

    def test_calculate_test_charges_non_string_raises(self):
        with self.assertRaises(ValueError):
            calculate_test_charges([["ECG"]])

    def test_bill_rejects_negative_fee(self):
        with self.assertRaises(ValueError):
            calculate_bill(-5000, 0, False, 30)

    def test_bill_rejects_negative_test_charges(self):
        with self.assertRaises(ValueError):
            calculate_bill(5000, -1000, False, 30)

    def test_bill_rejects_nan_and_infinity(self):
        for bad in (float("nan"), float("inf")):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    calculate_bill(bad, 0, False, 30)

    def test_bill_rejects_bad_age(self):
        for bad in ("old", -5, None, True):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    calculate_bill(5000, 0, False, bad)

    def test_bill_rejects_bad_config_rates(self):
        original = dict(CLINIC_CONFIG)
        try:
            for key, bad in [("insurance_consultation_rate", 1.5),
                             ("insurance_test_rate", -0.1),
                             ("senior_discount_rate", 5.0),
                             ("senior_discount_rate", -1),
                             ("senior_age_threshold", "sixty")]:
                with self.subTest(key=key, bad=bad):
                    CLINIC_CONFIG[key] = bad
                    with self.assertRaises(ValueError):
                        calculate_bill(5000, 0, True, 70)
                    CLINIC_CONFIG.update(original)
        finally:
            CLINIC_CONFIG.update(original)

    def test_insurance_coverage(self):
        consult_cov, test_cov = calculate_insurance_coverage(5000, 2500, True)
        self.assertEqual(consult_cov, 1000)
        self.assertEqual(test_cov, 1250)

    def test_no_insurance_coverage(self):
        self.assertEqual(calculate_insurance_coverage(5000, 2500, False), (0, 0))
        
    def test_calculate_bill_custom_config(self):
        custom_config = dict(CLINIC_CONFIG)
        custom_config["senior_discount_rate"] = 0.25
        bill = calculate_bill(5000, 0, False, 65, custom_config)
        self.assertEqual(bill["senior_discount"], 1250)
        
    def test_bill_rejects_huge_amounts(self):
        with self.assertRaises(ValueError):
            calculate_bill(1e30, 0, False, 30)

    def test_bill_rejects_non_bool_insurance(self):
        for bad in ("yes", "no", None, 1):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    calculate_bill(5000, 0, bad, 30)  # type: ignore
                    
    def test_calculate_bill_rejects_age_over_cap(self):
        with self.assertRaises(ValueError):
            calculate_bill(5000, 0, False, 1_000_000_000, CLINIC_CONFIG)

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

    def test_bill_rounded_to_two_decimals(self):
        bill = calculate_bill(3333, 0, True, 67)
        self.assertEqual(bill["consultation_coverage"], Decimal("666.60"))
        self.assertEqual(bill["senior_discount"], Decimal("266.64"))
        self.assertEqual(bill["final_amount"], Decimal("2399.76"))
        
    def test_bill_amounts_are_decimal(self):
        bill = calculate_bill(5000, 2500, True, 32)
        for key, value in bill.items():
            with self.subTest(key=key):
                self.assertIsInstance(value, Decimal)

    def test_bill_has_no_float_error(self):
        bill = calculate_bill(0.1, 0.2, False, 30)
        self.assertEqual(bill["final_amount"], Decimal("0.30"))

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
        
    def test_none_appointment_is_rejected(self):
        result = process_appointment(None)
        self.assertEqual(result["status"], "REJECTED")
        self.assertIsNone(result["appointment_id"])

    def test_non_dict_appointment_is_rejected(self):
        for bad in ([], "A001", 5, ("a",)):
            with self.subTest(bad=bad):
                result = process_appointment(bad)
                self.assertEqual(result["status"], "REJECTED")
                self.assertIn("dictionary", result["reason"])

    def test_none_in_batch_does_not_stop_others(self):
        good = copy.deepcopy(hms.appointments[0])
        other = copy.deepcopy(hms.appointments[1])
        results = process_all_appointments([good, None, other])
        self.assertEqual(
            [r["status"] for r in results],
            ["APPROVED", "REJECTED", "APPROVED"],
        )

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
        
    def test_bad_patient_record_rejected_not_crash(self):
        del hms.patients["P001"]["age"]
        result = process_appointment(make_appt(status="completed"))
        self.assertEqual(result["status"], "REJECTED")

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
        self.assertEqual(result["status"], "PENDING")
        self.assertIn("Pending", result["reason"])
        
    def test_bad_doctor_fee_rejected_not_crash(self):
        hms.doctors["D001"]["fee"] = -100
        result = process_appointment(make_appt(status="completed"))
        self.assertEqual(result["status"], "REJECTED")
        
    def test_invalid_status_message(self):
        ok, reason = validate_appointment(make_appt(status="bogus"))
        self.assertFalse(ok)
        self.assertIn("Invalid status", reason)
        self.assertIn("completed, cancelled or pending", reason)
        
    def test_missing_appointment_id_rejected(self):
        appt = make_appt(status="completed")
        del appt["appointment_id"]
        self.assertEqual(process_appointment(appt)["status"], "REJECTED")
        
    def test_ids_with_spaces_and_lowercase_are_accepted(self):
        result = process_appointment(
            make_appt(patient_id=" p001 ", doctor_id="d001", status="completed"))
        self.assertEqual(result["status"], "APPROVED")
        self.assertEqual(result["patient_id"], "P001")
        self.assertEqual(result["doctor_id"], "D001")

    def test_unknown_id_still_rejected_after_normalizing(self):
        result = process_appointment(make_appt(patient_id=" p999 ", status="completed"))
        self.assertEqual(result["status"], "REJECTED")

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
    
    def test_process_all_rejects_non_list(self):
        for bad in (None, "text", 5, {"a": 1}):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    process_all_appointments(bad)

    def test_processed_ids_must_be_a_set(self):
        with self.assertRaises(ValueError):
            process_appointment(hms.appointments[0], [])
            
    def test_huge_doctor_fee_rejected_not_crash(self):
        hms.doctors["D001"]["fee"] = 10**40
        result = process_appointment(make_appt(status="completed"))
        self.assertEqual(result["status"], "REJECTED")
    
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
        
    def test_cancel_none_fails(self):
        ok, msg = cancel_appointment(None)  # type: ignore
        self.assertFalse(ok)
        self.assertIn("dictionary", msg)

    def test_cancel_without_id_fails(self):
        appt = make_appt(status="pending")
        del appt["appointment_id"]
        ok, msg = cancel_appointment(appt)
        self.assertFalse(ok)
        self.assertEqual(appt["status"], "pending")

    def test_cancel_blank_id_fails(self):
        ok, _ = cancel_appointment(make_appt(appointment_id="  ", status="pending"))
        self.assertFalse(ok)

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
        
    def test_reports_count_appointments_with_messy_ids(self):
        appts = [make_appt("M1", patient_id=" p001 ", doctor_id="d001", status="completed")]
        results = process_all_appointments(appts)
        doc, _ = generate_doctor_report("d001", appts, results)
        pat, _ = generate_patient_report(" p001", appts, results)
        assert doc is not None and pat is not None
        self.assertEqual(doc["total_appointments"], 1)
        self.assertEqual(pat["total_appointments"], 1)

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

    def test_senior_count_uses_config_threshold(self):
        original = CLINIC_CONFIG["senior_age_threshold"]
        try:
            CLINIC_CONFIG["senior_age_threshold"] = 70
            dash = generate_clinic_report(hms.appointments, self.results)
            self.assertEqual(dash["senior_patient_count"], 0)
        finally:
            CLINIC_CONFIG["senior_age_threshold"] = original

    def test_top_doctor_empty_when_no_revenue(self):
        dash = generate_clinic_report([], [])
        self.assertEqual(dash["top_doctor"], [])

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
        
    def test_reports_reject_non_numeric_bill_values(self):
        bad = [{"appointment_id": "A", "status": "APPROVED", "patient_id": "P001",
                "doctor_id": "D001",
                "bill": {"final_amount": "x", "total_coverage": 1, "senior_discount": 1}}]
        with self.assertRaises(ValueError):
            generate_clinic_report([], bad)

    def test_report_with_list_id_returns_not_found(self):
        report, status = generate_doctor_report(["D001"], [], [])  # type: ignore
        self.assertIsNone(report)
        report, status = generate_patient_report(["P001"], [], [])  # type: ignore
        self.assertIsNone(report)

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
        
    def test_reports_normalize_mixed_case_status(self):
        appts = [
            make_appt("M2", patient_id="P001", doctor_id="D001", status="Completed"),
            make_appt("M3", patient_id="P002", doctor_id="D001", status=" CANCELLED "),
            make_appt("M4", patient_id="P003", doctor_id="D001", status="PENDING"),
        ]
        results = process_all_appointments(appts)

        dash = generate_clinic_report(appts, results)
        self.assertEqual(dash["completed"], 1)
        self.assertEqual(dash["cancelled"], 1)
        self.assertEqual(dash["pending"], 1)

        doc = doctor_report_of("D001", appts, results)
        self.assertEqual(doc["completed"], 1)
        self.assertEqual(doc["cancelled"], 1)
        self.assertEqual(doc["pending"], 1)

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

    def test_reports_reject_bad_appointments_list(self):
        for bad in (None, "text", [None], [{"x": 1}]):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    generate_doctor_report("D001", bad, [])  
                with self.assertRaises(ValueError):
                    generate_patient_report("P001", bad, [])  
                with self.assertRaises(ValueError):
                    generate_clinic_report(bad, [])  

    def test_reports_reject_bad_results(self):
        bad_results = [None, "text", [None], [{"status": "APPROVED"}],
                       [{"appointment_id": "A", "status": "APPROVED",
                         "patient_id": "P001", "doctor_id": "D001"}],
                       [{"appointment_id": "A", "status": "APPROVED",
                         "patient_id": "P001", "doctor_id": "D001", "bill": {}}]]
        for bad in bad_results:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    generate_doctor_report("D001", hms.appointments, bad)  
                with self.assertRaises(ValueError):
                    generate_patient_report("P001", hms.appointments, bad)  # type: ignore
                with self.assertRaises(ValueError):
                    generate_clinic_report(hms.appointments, bad)  # type: ignore

    def test_highest_spending_patient_empty_when_nobody_spent(self):
        results = process_all_appointments([])
        dash = generate_clinic_report([], results)
        self.assertEqual(dash["highest_spending_patient"], [])

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
            
    def test_kwargs_rejects_negative_fee(self):
        result, error = calculate_bill_kwargs(-5000)
        self.assertIsNone(result)
        self.assertIn("consultation_fee", str(error))

    def test_kwargs_rejects_non_numeric_fee(self):
        result, error = calculate_bill_kwargs("5000")
        self.assertIsNone(result)

    def test_kwargs_rejects_negative_age(self):
        result, error = calculate_bill_kwargs(5000, age=-5)
        self.assertIsNone(result)
        self.assertIn("age", str(error))

    def test_kwargs_rejects_unknown_test(self):
        result, error = calculate_bill_kwargs(5000, tests=["NOPE"])
        self.assertIsNone(result)
        self.assertIn("NOPE", str(error))

    def test_kwargs_rejects_non_string_test(self):
        result, error = calculate_bill_kwargs(5000, tests=[["x"]])
        self.assertIsNone(result)
        
    def test_combine_bills_rejects_bad_values(self):
        for bad in ("a", None, -5, float("nan"), True):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    combine_bills(100, bad)  # type: ignore
                    
    def test_senior_discount_requires_age(self):
        result, error = calculate_bill_kwargs(5000, senior_discount=True)
        self.assertIsNone(result)
        self.assertIn("age", str(error))

    def test_custom_config_is_used(self):
        cfg = dict(CLINIC_CONFIG, insurance_consultation_rate=0.5)
        result, error = calculate_bill_kwargs(5000, insurance=True, config=cfg)
        self.assertIsNone(error)
        self.assertEqual(result, Decimal("2500.00"))

    def test_custom_config_changes_senior_threshold(self):
        cfg = dict(CLINIC_CONFIG, senior_age_threshold=70)
        # age 67 is below the custom threshold, so no senior discount
        result, error = calculate_bill_kwargs(
            5000, senior_discount=True, age=67, config=cfg
        )
        self.assertIsNone(error)
        self.assertEqual(result, Decimal("5000.00"))

    def test_default_config_used_when_not_given(self):
        with_default, _ = calculate_bill_kwargs(5000, insurance=True)
        explicit, _ = calculate_bill_kwargs(5000, insurance=True, config=CLINIC_CONFIG)
        self.assertEqual(with_default, explicit)

    def test_invalid_config_returns_error(self):
        result, error = calculate_bill_kwargs(5000, config={"x": 1})
        self.assertIsNone(result)
        self.assertIsNotNone(error)
        assert error is not None
        self.assertIn("insurance_consultation_rate", error)

    def test_calculate_bill_kwargs_rejects_age_over_cap(self):
        result, error = calculate_bill_kwargs(
            5000, insurance=False, senior_discount=True, age=1_000_000_000
        )
        self.assertIsNone(result)
        self.assertIsNotNone(error)

    def test_config_not_a_dict_returns_error(self):
        result, error = calculate_bill_kwargs(5000, config="bad")
        self.assertIsNone(result)
        self.assertIsNotNone(error)
        assert error is not None
        self.assertIn("config", error.lower())

    def test_config_is_not_modified(self):
        cfg = dict(CLINIC_CONFIG, insurance_consultation_rate=0.5)
        before = copy.deepcopy(cfg)
        calculate_bill_kwargs(5000, insurance=True, config=cfg)
        self.assertEqual(cfg, before)
        
    def test_duplicate_tests_different_case_rejected(self):
        result, error = calculate_bill_kwargs(5000, tests=["ECG", "ecg"])
        self.assertIsNone(result)
        self.assertIsNotNone(error)
        assert error is not None
        self.assertIn("Duplicate", error)

    def test_duplicate_tests_with_spaces_rejected(self):
        result, error = calculate_bill_kwargs(5000, tests=[" ECG", "ecg "])
        self.assertIsNone(result)
        self.assertIsNotNone(error)
        assert error is not None
        self.assertIn("Duplicate", error)

    def test_different_tests_still_accepted(self):
        result, error = calculate_bill_kwargs(5000, tests=["ECG", "blood test"])
        self.assertIsNone(error)
        self.assertEqual(result, Decimal("7500.00"))
        
class TestExtraHardening(BaseTestCase):

    def test_is_valid_amount_huge_int_is_false(self):
        self.assertFalse(hms.is_valid_amount(10**400))

    def test_is_valid_amount_still_accepts_normal_values(self):
        self.assertTrue(hms.is_valid_amount(5))
        self.assertTrue(hms.is_valid_amount(0))
        self.assertFalse(hms.is_valid_amount(-1))
        self.assertFalse(hms.is_valid_amount(float("nan")))

    # --- #4 ---
    def test_validate_appointment_rejects_decimal_age(self):
        patients = copy.deepcopy(hms.patients)
        patients["P001"]["age"] = 32.5
        appt = copy.deepcopy(hms.appointments[0])
        ok, _ = validate_appointment(appt, patients)
        self.assertFalse(ok)

    def test_validate_patients_rejects_unnormalised_key(self):
        data = {" p001 ": {"name": "A", "city": "X", "age": 30, "insurance": True}}
        with self.assertRaises(ValueError):
            validate_patients(data)

    def test_validate_doctors_rejects_unnormalised_key(self):
        data = {"d001": {"name": "A", "specialization": "X", "fee": 100, "available": True}}
        with self.assertRaises(ValueError):
            validate_doctors(data)

    def test_calculate_test_charges_rejects_duplicates(self):
        with self.assertRaises(ValueError):
            calculate_test_charges(["ECG", "ecg"])

    def test_calculate_test_charges_unique_ok(self):
        self.assertEqual(calculate_test_charges(["ECG", "Blood Test"]), Decimal("2500"))

    def test_insurance_coverage_rejects_bad_fee(self):
        with self.assertRaises(ValueError):
            calculate_insurance_coverage("x", 5, True)

    def test_insurance_coverage_rejects_non_bool_insurance(self):
        with self.assertRaises(ValueError):
            calculate_insurance_coverage(5000, 0, "yes")

    def test_insurance_coverage_valid(self):
        self.assertEqual(
            calculate_insurance_coverage(5000, 2500, True),
            (Decimal("1000.00"), Decimal("1250.00")),
        )

    def test_kwargs_custom_test_prices(self):
        result, error = calculate_bill_kwargs(1000, tests=["CT"], test_prices={"CT": 500})
        self.assertIsNone(error)
        self.assertEqual(result, Decimal("1500.00"))

    def test_kwargs_invalid_test_prices(self):
        result, error = calculate_bill_kwargs(1000, test_prices="x")
        self.assertIsNone(result)
        self.assertIsNotNone(error)

    def test_kwargs_default_prices_still_work(self):
        result, error = calculate_bill_kwargs(5000, tests=["ECG"])
        self.assertIsNone(error)
        self.assertEqual(result, Decimal("6500.00"))
        
class TestFindDoubleBookings(BaseTestCase):

    def test_no_conflict_when_no_time_slots(self):
        appts = [
            make_appt("D1", doctor_id="D001", status="completed"),
            make_appt("D2", doctor_id="D001", status="completed"),
        ]
        self.assertEqual(find_double_bookings(appts), [])

    def test_detects_real_conflict(self):
        appts = [
            {**make_appt("D1", doctor_id="D001", status="completed"), "time_slot": "2026-11-10 10:00"},
            {**make_appt("D2", doctor_id="D001", status="completed"), "time_slot": "2026-11-10 10:00"},
        ]
        self.assertEqual(find_double_bookings(appts), [("D001", "2026-11-10 10:00")])

    def test_ignores_cancelled_duplicate(self):
        appts = [
            {**make_appt("D1", doctor_id="D001", status="completed"), "time_slot": "2026-11-10 10:00"},
            {**make_appt("D2", doctor_id="D001", status="cancelled"), "time_slot": "2026-11-10 10:00"},
        ]
        self.assertEqual(find_double_bookings(appts), [])

    def test_different_doctors_same_slot_no_conflict(self):
        appts = [
            {**make_appt("D1", doctor_id="D001", status="completed"), "time_slot": "2026-11-10 10:00"},
            {**make_appt("D2", doctor_id="D002", status="completed"), "time_slot": "2026-11-10 10:00"},
        ]
        self.assertEqual(find_double_bookings(appts), [])

    def test_not_a_list_raises(self):
        with self.assertRaises(ValueError):
            find_double_bookings("not a list")  # type: ignore

if __name__ == "__main__":
    unittest.main(verbosity=2)