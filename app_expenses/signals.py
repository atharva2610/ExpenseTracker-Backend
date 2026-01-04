import calendar
from django.db.models.signals import post_save, post_delete, pre_save
from django.db.models import Sum
from django.dispatch import receiver
from .models import Transaction, Report, Loan, TransactionType
from datetime import date

@receiver(post_save, sender=Transaction)
@receiver(post_delete, sender=Transaction)
def mark_report_dirty_on_transaction_change(sender, instance, **kwargs):
    report = Report.objects.filter(
        user=instance.user,
        year=instance.date.year,
        month=instance.date.month
    ).first()
    if report:
        report.is_dirty = True
        report.save(update_fields=['is_dirty'])

@receiver(pre_save, sender=Transaction)
def mark_report_dirty_on_transaction_update(sender, instance, **kwargs):
    if not instance.pk:
        return
    old_instance = Transaction.objects.filter(pk=instance.pk).first()
    if (
        old_instance and (
        old_instance.amount != instance.amount or
        old_instance.fund_account_id != instance.fund_account_id or
        old_instance.date != instance.date)
    ):
        report = Report.objects.filter(
            user=old_instance.user,
            year=old_instance.date.year,
            month=old_instance.date.month
        ).first()
        if report:
            report.is_dirty = True
            report.save(update_fields=['is_dirty'])

@receiver(pre_save, sender=Loan)
def sync_completed_and_remaining(sender, instance, **kwargs):
    if instance.remaining_amount == 0:
        instance.completed = True
    elif instance.completed:
        instance.remaining_amount = 0

def last_day_of_month(year: int, month: int) -> date:
    # calendar.monthrange returns (weekday_of_first_day, number_of_days_in_month)
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, last_day)

@receiver(pre_save, sender=Report)
def calculate_total(sender, instance, **kwargs):
    start_date = date(instance.year, instance.month, 1)
    end_date = last_day_of_month(instance.year, instance.month)

    sum_credit = Transaction.objects.filter(user=instance.user, date__range=(start_date, end_date), type=TransactionType.CREDIT).aggregate(total=Sum("amount"))["total"] or 0
    sum_debit = Transaction.objects.filter(user=instance.user, date__range=(start_date, end_date), type=TransactionType.DEBIT).aggregate(total=Sum("amount"))["total"] or 0

    instance.total_credit = sum_credit
    instance.total_debit = sum_debit