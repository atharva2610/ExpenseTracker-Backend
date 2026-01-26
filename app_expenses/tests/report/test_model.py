from django.test import TestCase
from app_expenses.models import Report, Transaction, TransactionType, FundAccount, Currency, Category
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, PermissionDenied
from datetime import date

User = get_user_model()

class ReportModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(username="user1")
        self.user2 = User.objects.create(username="user2")
        self.currency = Currency.objects.create(id="INR", symbol="₹", name="Indian Rupee")
        self.fund_acct_user1 = FundAccount.objects.create(user=self.user1, name="Wallet", balance=5000, currency=self.currency)
        self.category_user1 = Category.objects.create(user=self.user1, name="Food")

    # ------------ Missing field ---------------

    def test_report_with_missing_user_fails(self):
        """Report: fails when 'user' is missing"""
        report = Report(month=10, year=2025)
        with self.assertRaisesMessage(ValidationError, "User does not exists."):
            report.full_clean()

    def test_report_with_missing_month_fails(self):
        """Report: fails when 'month' is missing"""
        report = Report(user=self.user1, year=2025)
        with self.assertRaisesMessage(ValidationError, "Month is required."):
            report.full_clean()

    def test_report_with_missing_year_fails(self):
        """Report: fails when 'year' is missing"""
        report = Report(user=self.user1, month=10,)
        with self.assertRaisesMessage(ValidationError, "Year is required."):
            report.full_clean()

    # ---------- Non existing User/Currency --------------

    def test_report_with_non_existing_user_fails(self):
        """Report: fails to create with non existing 'user'"""
        non_existing_user = User(username="not-exists")
        report = Report(user=non_existing_user, month=10, year=2025)
        with self.assertRaises(ValidationError):
            report.full_clean()

    # ---------- Invalid data ----------

    def test_report_month_outoff_range_fails(self):
        """Report: fails with 'month' out-off range (1 to 12)"""
        report = Report(user=self.user1, month=13, year=2025)
        with self.assertRaises(ValidationError):
            report.full_clean()
    
    def test_report_year_outoff_range_fails(self):
        """Report: fails with 'year' out-off range (2000 to current year)"""
        for year in (1999, date.today().year+1):
            report = Report(user=self.user1, month=10, year=year)
            with self.assertRaisesMessage(ValidationError, "Year cannot be less than 2000 or in future."):
                report.full_clean()

    # ---------- Uniqueness ---------------
    
    def test_report_duplicate_month_year_same_user_fails(self):
        """Report: fails when duplicate 'month' and 'year' exists for same user"""
        Report.objects.create(user=self.user1, month=10, year=2025)
        duplicate = Report(user=self.user1, month=10, year=2025)
        with self.assertRaisesMessage(ValidationError, f"Report with Month Year: '{duplicate.month_year}' already exists."):
            duplicate.full_clean()

    def test_report_duplicate_month_year_different_user_success(self):
        """Report: succeeds when duplicate 'month' and 'year' exists for different users"""
        Report.objects.create(user=self.user1, month=10, year=2025)
        report = Report(user=self.user2, month=10, year=2025)
        report.full_clean()

    def test_report_update_to_duplicate_month_year_same_user_fails(self):
        """Report: fails when updating to duplicate 'month' and 'year' for same user"""
        report1 = Report.objects.create(user=self.user1, month=10, year=2025)
        report2 = Report.objects.create(user=self.user1, month=11, year=2025)
        report2.month = 10
        with self.assertRaisesMessage(ValidationError, f"Report with Month Year: '{report2.month_year}' already exists."):
            report2.full_clean()

    # ----------- Valid owned data ----------------

    def test_report_create_with_valid_values_success(self):
        """Report: success to create with valid 'user', 'month' & 'year' results correct 'total credit' & 'total debit'"""
        trx_data = (
            {"amount": 100, "trx_type": TransactionType.DEBIT, "trx_date": date(2025, 10, 26)},
            {"amount": 20, "trx_type": TransactionType.CREDIT, "trx_date": date(2025, 10, 30)},
            {"amount": 100, "trx_type": TransactionType.DEBIT, "trx_date": date(2025, 10, 26)},
            {"amount": 20, "trx_type": TransactionType.CREDIT, "trx_date": date(2025, 10, 30)},
        )
        for data in trx_data:
            Transaction.objects.create(
                user = self.user1,
                category = self.category_user1,
                amount = data["amount"],
                fund_account = self.fund_acct_user1,
                date = data["trx_date"],
                type = data["trx_type"]
            )
        report = Report.objects.create(user=self.user1, month=10, year=2025)

        expected_total_credit = sum(data["amount"] for data in trx_data if data["trx_type"] == TransactionType.CREDIT)
        expected_total_debit = sum(data["amount"] for data in trx_data if data["trx_type"] == TransactionType.DEBIT)
        self.assertEqual(report.user, self.user1)
        self.assertEqual(report.month, 10)
        self.assertEqual(report.year, 2025)
        self.assertEqual(report.total_credit, expected_total_credit)
        self.assertEqual(report.total_debit, expected_total_debit)

    def test_report_fetch_owned_success(self):
        """Report: success to fetch owned 'report'."""
        report = Report.objects.create(user=self.user1, month=10, year=2025)
        fetched = Report.get_for_user(self.user1, report.pk)
        self.assertEqual(fetched.pk, report.pk)

    def test_report_update_owned_success(self):
        """Report: success to update owned 'report'."""
        report = Report.objects.create(user=self.user1, month=10, year=2025)
        report.month = 11
        report.update_by(self.user1)
        self.assertEqual(report.month, 11)

    # ----------- Others owned data ---------------

    def test_report_fetch_others_owned_fails(self):
        """Report: fail to fetch others owned 'report'."""
        report = Report.objects.create(user=self.user2, month=11, year=2025)
        with self.assertRaisesMessage(PermissionDenied, "You are not the owner."):
            report.get_for_user(self.user1, report.pk)

    def test_report_update_others_owned_fails(self):
        """Report: fail to update others owned 'report'."""
        report = Report.objects.create(user=self.user2, month=11, year=2025)
        report.name = "Bank"
        with self.assertRaisesMessage(PermissionDenied, "You are not the owner."):
            report.update_by(self.user1)
