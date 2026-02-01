from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.db.models import Sum
from datetime import date
from ..models import Transaction, Report
from ..utilities import is_valid_for_report, monthly_report_csv


def get_csv(user, month, year):
    if not is_valid_for_report(month, year):
        raise ValidationError({'month': f'{month}-{year} is invalid month year'})
    trx_list = Transaction.get_for_user(requested_user=user).filter(date__year=int(year), date__month=int(month))
    month = date(year=int(year), month=int(month), day=1).strftime("%b")
    FILENAME = month+year+"_transations.csv"
    report_content = monthly_report_csv(trx_list)
    csv_report = HttpResponse(content=report_content, content_type="text/csv")
    csv_report["Content-Disposition"] = (f'attachment; filename={FILENAME}')
    return csv_report, trx_list

@login_required(login_url='login')
def report(request):
    context = {}
    if request.POST:
        try:
            year, month = request.POST.get('month').split('-')
            csv_report, trx_list = get_csv(request.user, month, year)

            if request.POST.get('generate_report'):
                total_credit_amount = trx_list.filter(type='credit').aggregate(total_credit_amount=Sum('amount'))['total_credit_amount']
                total_debit_amount = trx_list.filter(type='credit').aggregate(total_debit_amount=Sum('amount'))['total_debit_amount']
                report = Report(user=request.user, month=int(month), year=int(year), total_credit=total_credit_amount, total_debit=total_debit_amount)
                report = report.create_by(requested_user=request.user)
            return csv_report
        except ValidationError as ve:
            context['errors'] = ve
        except Exception as e:
            messages.error(request, str(e))
    context['reports_list'] = Report.get_for_user(requested_user=request.user)
    return render(request, 'report/index.html', context)

def update_report(request, id):
    context = {}
    report = Report.get_for_user(requested_user=request.user, id=id)
    context['month_year'] = f"{report.year}-{str(report.month).rjust(2, "0")}"
    if request.POST:
        try:
            year, month = request.POST.get('month').split('-')
            csv_report, trx_list = get_csv(request.user, month, year)

            report.total_credit = trx_list.filter(type='credit').aggregate(total_credit_amount=Sum('amount'))['total_credit_amount']
            report.total_debit = trx_list.filter(type='credit').aggregate(total_debit_amount=Sum('amount'))['total_debit_amount']
            report.is_dirty = False
            report = report.update_by(requested_user=request.user)

            return csv_report
        except ValidationError as ve:
            context['errors'] = ve
        except Exception as e:
            messages.error(request, str(e))
    return render(request, 'report/form_update.html', context)
