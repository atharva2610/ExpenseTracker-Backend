from ...models import FundAccount, Category, Transaction
from django.db.models import Sum

def get_all_transactions(requested_user):
    trx_list = Transaction.get_for_user(requested_user=requested_user)
    return trx_list

def get_transaction_by_id(requested_user, trx_id):
    if not trx_id:
        raise Exception("Transaction ID is required.")
    trx = Transaction.get_for_user(requested_user=requested_user, id=trx_id)
    return trx

def get_credit_debit_summary(trx_list):
    total_credit = trx_list.filter(type='credit').aggregate(total_credit=Sum('amount'))['total_credit']
    total_debit = trx_list.filter(type='debit').aggregate(total_debit=Sum('amount'))['total_debit']
    return (total_credit, total_debit)

def get_transactions_by_fund_account(requested_user, fund_account_id):
    if not fund_account_id:
        raise Exception("Fund Account ID is required.")
    fund_acct = FundAccount.get_for_user(requested_user=requested_user, id=fund_account_id)
    trx_list = get_all_transactions(requested_user=requested_user).filter(fund_account__id=fund_account_id)
    return (trx_list, fund_acct) + get_credit_debit_summary(trx_list)

def get_transactions_by_category(requested_user, category_id):
    if not category_id:
        raise Exception("Category ID is required.")
    category = Category.get_for_user(requested_user=requested_user, id=category_id)
    trx_list = get_all_transactions(requested_user=requested_user).filter(category__id=category_id)
    return (trx_list, category) + get_credit_debit_summary(trx_list)
    