from .views import login, logout, register, dashboard, not_found_404, no_permission
from .fund_account_view import fund_accounts, create_fund_account, update_fund_account
from .category_view import categories, create_category, update_category
from .tag_view import tags, create_tag, update_tag
from .transaction_view import transactions, transactions_by_fund_account, transactions_by_category, create_transaction, update_transaction
from .report_view import report, update_report