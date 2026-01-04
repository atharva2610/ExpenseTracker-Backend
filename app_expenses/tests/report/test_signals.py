from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model
from app_expenses.models import Report, Transaction, TransactionType, FundAccount, Category, Currency

User = get_user_model()

class ReportDirtySignalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="user1")
        self.category = Category.objects.create(name="Food", user=self.user)
        self.currency = Currency.objects.create(id="INR", symbol="₹", name="Indian Rupee")
        self.fund_account = FundAccount.objects.create(user=self.user, name="Wallet", balance=1000, currency=self.currency)
        self.report = Report.objects.create(user=self.user, month=10, year=2025, is_dirty=False)

    def test_report_marked_dirty_on_transaction_create(self):
        """Signal: Report.is_dirty becomes True when a new transaction is created"""
        Transaction.objects.create(
            user=self.user,
            category=self.category,
            amount=100,
            fund_account=self.fund_account,
            date=date(2025, 10, 5),
            type=TransactionType.DEBIT,
        )
        self.report.refresh_from_db()
        self.assertTrue(self.report.is_dirty)

    def test_report_marked_dirty_on_transaction_delete(self):
        """Signal: Report.is_dirty becomes True when a transaction is deleted"""
        trx = Transaction.objects.create(
            user=self.user,
            category=self.category,
            amount=50,
            fund_account=self.fund_account,
            date=date(2025, 10, 10),
            type=TransactionType.CREDIT,
        )
        self.report.is_dirty = False
        self.report.save()

        trx.delete()
        self.report.refresh_from_db()
        self.assertTrue(self.report.is_dirty)

    def test_report_marked_dirty_on_transaction_update_amount(self):
        """Signal: Report.is_dirty becomes True when transaction amount changes"""
        trx = Transaction.objects.create(
            user=self.user,
            category=self.category,
            amount=200,
            fund_account=self.fund_account,
            date=date(2025, 10, 15),
            type=TransactionType.DEBIT,
        )
        self.report.is_dirty = False
        self.report.save()

        trx.amount = 300
        trx.save()
        self.report.refresh_from_db()
        self.assertTrue(self.report.is_dirty)

    def test_report_marked_dirty_on_transaction_update_date(self):
        """Signal: Report.is_dirty becomes True when transaction date changes"""
        trx = Transaction.objects.create(
            user=self.user,
            category=self.category,
            amount=100,
            fund_account=self.fund_account,
            date=date(2025, 10, 20),
            type=TransactionType.CREDIT,
        )
        self.report.is_dirty = False
        self.report.save()

        trx.date = date(2025, 10, 25)
        trx.save()
        self.report.refresh_from_db()
        self.assertTrue(self.report.is_dirty)

    def test_report_marked_dirty_on_transaction_update_fund_account(self):
        """Signal: Report.is_dirty becomes True when transaction fund account changes"""
        trx = Transaction.objects.create(
            user=self.user,
            category=self.category,
            amount=150,
            fund_account=self.fund_account,
            date=date(2025, 10, 22),
            type=TransactionType.DEBIT,
        )
        self.report.is_dirty = False
        self.report.save()

        new_fund = FundAccount.objects.create(user=self.user, name="Bank", balance=500, currency=self.currency)
        trx.fund_account = new_fund
        trx.save()
        self.report.refresh_from_db()
        self.assertTrue(self.report.is_dirty)