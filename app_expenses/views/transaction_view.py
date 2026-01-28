from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from ..models import Transaction, TransactionType, Tag
from ..utilities import get_fund_account_list, get_category_list, get_tag_list, get_fund_account_by_id, get_category_by_id, get_tag_by_id

def get_common_context():
    context = {
        'fund_account_list': get_fund_account_list(),
        'category_list': get_category_list(),
        'tag_list': get_tag_list(),
        'trx_type': TransactionType.choices
    }
    return context

def form_proccessing(request):
    data = {}
    for field in ('fund_account', 'amount', 'date','type', 'category', 'description'):
        data[field] = request.POST.get(field)
    data['fund_account'] = get_fund_account_by_id(data['fund_account'])
    data['category'] = get_category_by_id(data['category'])
    data['tags'] = request.POST.getlist("tags")

    try:
        valid_tags = Tag.objects.filter(id__in=data['tags'])
    except Exception as e:
        raise ValidationError({'tags': e})
    if len(valid_tags) != len(data['tags']):
        raise ValidationError({'tags': 'One or more selected tags are invalid.'})

    trx = Transaction(
        fund_account = data.get('fund_account'),
        amount = data.get('amount'),
        date = data.get('date'),
        type = data.get('type'),
        category = data.get('category'),
        description = data.get('description')
    )
    return (trx, valid_tags)

@login_required(login_url='login')
def transactions(request):
    trx_list = Transaction.get_for_user(requested_user=request.user)
    paginator = Paginator(trx_list, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'transaction/index.html', {'page_obj': page_obj})

@login_required(login_url='login')
def create_transaction(request):
    try:
        context = get_common_context()
        if request.POST:
            trx, valid_tags = form_proccessing(request)
            trx.user = request.user
            trx = trx.create_by(requested_user=request.user)
            trx.tags.set(valid_tags)
            messages.success(request, 'Transaction added successfully!!!')
    except ValidationError as ve:
        context['errors'] = ve
        print("VALIDATION ERROR:")
        print(ve)
        print("-"*20)
    except Exception as e:
        messages.error(request, str(e))
        print("EXECPTION:")
        print(e)
        print("-"*20)
    return render(request, 'transaction/form_create.html', context)

@login_required(login_url='login')
def update_transaction(request, id):
    try:
        context = get_common_context()
        context['trx'] = Transaction.get_for_user(requested_user=request.user, id=id)
        if request.POST:
            trx, valid_tags = form_proccessing(request)
            context['trx'].amount = trx.amount
            context['trx'].fund_account = trx.fund_account
            context['trx'].category = trx.category
            context['trx'].date = trx.date
            context['trx'].type = trx.type
            context['trx'].description = trx.description
            context['trx'] = context['trx'].update_by(requested_user=request.user)
            context['trx'].tags.set(valid_tags)
            messages.success(request, 'Transaction updated successfully!!!')
    except ValidationError as ve:
        context['errors'] = ve
        print("VALIDATION ERROR:")
        print(ve)
        print("-"*20)
    except Exception as e:
        messages.error(request, str(e))
        print("EXECPTION:")
        print(e)
        print("-"*20)
    return render(request, 'transaction/form_update.html', context)