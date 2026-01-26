from django.shortcuts import render
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import FundAccount
from ..utilities import get_currency_by_id, get_currency_list

@login_required(login_url='login')
def fund_accounts(request):
    fund_accounts_list = FundAccount.get_for_user(requested_user=request.user)
    return render(request, 'fund_account/index.html', {'fund_accounts_list': fund_accounts_list})

@login_required(login_url='login')
def create_fund_account(request):
    try:
        context = {'currency_list': get_currency_list()}
        if request.POST:
            data = {}
            for field in ('name', 'balance', 'currency'):
                data[field] = request.POST.get(field)
                data['currency'] = get_currency_by_id(data['currency'])
                fund_acct = FundAccount(user=request.user, name=data['name'], balance=data['balance'], currency=data['currency'])
                fund_acct = fund_acct.create_by(requested_user=request.user)
                messages.success(request, 'Fund Account added successfully!!!')
    except ValidationError as ve:
        context['errors'] = ve
        print("VALIDATION ERROR:")
        print(ve)
        print("----------------------------")
    except Exception as e:
        messages.error(request, str(e))
        print("EXECPTION:")
        print(e)
        print("----------------------------")
    return render(request, 'fund_account/form_create.html', context)

@login_required(login_url='login')
def update_fund_account(request, id):
    try:
        context = {
            'currency_list': get_currency_list(),
            'fund_account': FundAccount.get_for_user(requested_user=request.user, id=id)
        }
        if request.POST:
            context['fund_account'].name = request.POST.get('name')
            context['fund_account'].balance = request.POST.get('balance')
            context['fund_account'].currency = get_currency_by_id(request.POST.get('currency'))
            context['fund_account'] = context['fund_account'].update_by(requested_user=request.user)
            messages.success(request, 'Fund Account updated successfully!!!')
    except ValidationError as ve:
        context['errors'] = ve
        print("VALIDATION ERROR:")
        print(ve)
        print("----------------------------")
    except Exception as e:
        messages.error(request, str(e))
        print("EXECPTION:")
        print(e)
        print("----------------------------")
    return render(request, 'fund_account/form_update.html', context)