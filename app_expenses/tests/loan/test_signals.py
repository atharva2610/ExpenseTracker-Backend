from django.test import TestCase
from django.contrib.auth.models import User
from app_expenses.models import Loan, Currency

class LoanSignalsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser")
        self.currency = Currency.objects.create(id="inr", symbol="₹", name="Rupee")

    def test_signal_sets_completed_when_remaining_zero(self):
        loan = Loan.objects.create(
            user=self.user,
            from_entity="testuser2",
            currency=self.currency,
            amount=1500,
            remaining_amount=0
        )
        loan.refresh_from_db()
        self.assertTrue(loan.completed)

    def test_signal_sets_remaining_zero_when_completed(self):
        loan = Loan.objects.create(
            user=self.user,
            from_entity="testuser2",
            currency=self.currency,
            amount=150000,
            completed=True,
            remaining_amount=50000)
        loan.refresh_from_db()
        self.assertEqual(loan.remaining_amount, 0)