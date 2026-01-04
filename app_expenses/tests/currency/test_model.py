from django.test import TestCase
from django.core.exceptions import ValidationError
from app_expenses.models import Currency

class CurrencyModelTest(TestCase):
    # ------------ Missing field ---------------

    def test_currency_missing_id_fails(self):
        """Currency: fails when 'id' is missing"""
        currency = Currency(symbol="₹", name="Indian Rupee")
        with self.assertRaisesMessage(ValidationError, "ID is required."):
            currency.full_clean()
    
    def test_currency_missing_symbol_fails(self):
        """Currency: fails when 'symbol' is missing"""
        currency = Currency(id="INR", name="Indian Rupee")
        with self.assertRaisesMessage(ValidationError, "Symbol is required."):
            currency.full_clean()

    def test_currency_missing_name_fails(self):
        """Currency: fails when 'name' is missing"""
        currency = Currency(id="INR", symbol="₹")
        with self.assertRaisesMessage(ValidationError, "Name is required."):
            currency.full_clean()
    
    # ---------- Uniqueness ---------------

    def test_currency_duplicate_field_fails(self):
        """Currency: fails when a duplicate value (case-insensitive) exists"""
        Currency.objects.create(id="INR", symbol="₹", name="Indian Rupee")
        # duplicate id
        duplicate = Currency(id="INR", symbol="$", name="US Dollar")
        with self.assertRaisesMessage(ValidationError, "Currency with this Id already exists."):
            duplicate.full_clean()
        # duplicate sybmol
        duplicate = Currency(id="USD", symbol="₹", name="US Dollar")
        with self.assertRaisesMessage(ValidationError, f"Currency with Symbol: '{duplicate.symbol}' already exists."):
            duplicate.full_clean()
        # duplicate name
        duplicate = Currency(id="USD", symbol="$", name="Indian Rupee")
        with self.assertRaisesMessage(ValidationError, f"Currency with Name: '{duplicate.name}' already exists."):
            duplicate.full_clean()

    # ---------- Whitespace Normalization ----------

    def test_currency_whitespace_trimmed_success(self):
        """Currency: success to trim leading/trailing whitespace."""
        currency = Currency.objects.create(id="  INR  ", symbol="  ₹  ", name="  Indian Rupee  ")
        self.assertEqual(currency.id, "INR")
        self.assertEqual(currency.symbol, "₹")
        self.assertEqual(currency.name, "Indian Rupee")

    def test_currency_whitespace_only_fails(self):
        """Currency: fails when a field is only whitespace value"""
        # for id
        currency = Currency(id="  ", symbol="₹", name="Indian Rupee")
        with self.assertRaisesMessage(ValidationError, "ID cannot be blank or whitespace."):
            currency.full_clean()
        # for symbol
        currency = Currency(id="INR", symbol="  ", name="Indian Rupee")
        with self.assertRaisesMessage(ValidationError, "Symbol cannot be blank or whitespace."):
            currency.full_clean()
        # for name
        currency = Currency(id="INR", symbol="₹", name="  ")
        with self.assertRaisesMessage(ValidationError, "Name cannot be blank or whitespace."):
            currency.full_clean()

    # ----------- Character limit -------------

    def test_currency_exceeded_max_length_fails(self):
        """Currency: fails with exceeding max_length field value."""
        # for id
        with self.assertRaises(ValidationError):
            fund_account = Currency(id="x"*5, symbol="#", name="X")
            fund_account.full_clean()
        # for symbol
        with self.assertRaises(ValidationError):
            fund_account = Currency(id="x", symbol="#"*9, name="X")
            fund_account.full_clean()
        # for name
        with self.assertRaises(ValidationError):
            fund_account = Currency(id="x", symbol="#", name="X"*65)
            fund_account.full_clean()

    # ------------ Valid data -------------

    def test_currency_create_success(self):
        """Currency: success to create with valid values."""
        currency = Currency.objects.create(id="INR", symbol="₹", name="Indian Rupee")
        self.assertEqual(currency.id, "INR")
        self.assertEqual(currency.symbol, "₹")
        self.assertEqual(currency.name, "Indian Rupee")

    def test_currency_update_success(self):
        """Currency: success to update with valid values."""
        currency = Currency.objects.create(id="USD", symbol="$", name="US Dollar")
        currency.id="INR"
        currency.symbol="₹"
        currency.name="Indian Rupee"
        currency.full_clean()
        currency.save()
        self.assertEqual(currency.id, "INR")
        self.assertEqual(currency.symbol, "₹")
        self.assertEqual(currency.name, "Indian Rupee")