from functools import wraps
from django.db import transaction as db_transaction
from django.core.exceptions import ValidationError

def balance_updater(func):
    """
    Decorator to ensure fund account balances are updated atomically
    when a transaction is created or updated.
    
    Works for both model methods and DRF serializer methods.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        with db_transaction.atomic():
            # Capture old state BEFORE saving 
            is_update = not self._state.adding
            old_trx = None
            if is_update:
                old_trx = self.__class__.objects.get(pk=self.pk)

            # Call the original function (save/create/update) 
            trx = func(self, *args, **kwargs)
            if trx is None: # model.save() returns None and serailizer.save() returns instance
                trx = self

            latest_fund_acct = trx.fund_account

            # Handle update case
            if is_update and old_trx:
                if old_trx.fund_account.pk != latest_fund_acct.pk:
                    # Fund account changed → revert old balance
                    if old_trx.type == "credit":
                        old_trx.fund_account.balance -= old_trx.amount
                    elif old_trx.type == "debit":
                        old_trx.fund_account.balance += old_trx.amount
                    old_trx.fund_account.save(update_fields=["balance"])
                else:
                    # Same fund account → adjust old amount
                    if old_trx.type == "credit":
                        latest_fund_acct.balance -= old_trx.amount
                    elif old_trx.type == "debit":
                        latest_fund_acct.balance += old_trx.amount

            if latest_fund_acct.balance < trx.amount:
                raise ValidationError({'amount': 'Insufficient Balance'})

            # Apply new balance
            if trx.type == "credit":
                latest_fund_acct.balance += trx.amount
            elif trx.type == "debit":
                latest_fund_acct.balance -= trx.amount
            latest_fund_acct.save(update_fields=["balance"])
            return trx
    return wrapper