from django.contrib.admin import register, ModelAdmin
from .models import *

@register(Currency)
class CurrencyAdmin(ModelAdmin):
    list_display = ('id', 'name', 'symbol')  # adjust fields
    search_fields = ('id', 'name')

@register(FundAccount)
class FundAccountAdmin(ModelAdmin):
    list_display = ('user', 'name', 'balance', 'currency')
    search_fields = ('name',)
    list_filter = ('user',)

@register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('user', 'name')
    search_fields = ('name',)
    list_filter = ('user',)

@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ('user', 'name')
    search_fields = ('name',)
    list_filter = ('user',)

@register(Transaction)
class TransactionAdmin(ModelAdmin):
    list_display = ('user', 'amount', 'type', 'fund_account', 'date', 'category')
    search_fields = ('description',)
    list_filter = ('user', 'type', 'fund_account', 'date', 'category')

@register(Shortcut)
class ShortcutAdmin(ModelAdmin):
    list_display = ('user', 'name')
    search_fields = ('name',)
    list_filter = ('user',)

@register(Report)
class ReportAdmin(ModelAdmin):
    list_display = ('user', 'month_year', 'total_debit', 'total_credit', 'is_dirty')
    search_fields = ('month', 'year', 'month_year')
    list_filter = ('user', 'year', 'is_dirty')

@register(Loan)
class LoanAdmin(ModelAdmin):
    list_display = ('user', 'type', 'from_entity', 'currency', 'amount', 'remaining_amount', 'completed', 'interest_rate', 'due_date')
    search_fields = ('from_entity', 'description')
    list_filter = ('user', 'completed', 'type')