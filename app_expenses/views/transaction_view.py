from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from ..models import Transaction, TransactionType, Tag
from ..utilities import get_fund_account_list, get_category_list, get_tag_list, get_fund_account_by_id, get_category_by_id, get_tag_by_id
from ..services import user_transactions

def get_form_common_context():
    context = {
        'fund_account_list': get_fund_account_list(),
        'category_list': get_category_list(),
        'tag_list': get_tag_list(),
        'trx_type': TransactionType.choices
    }
    return context

def paginated_transaction_list(request, trx_list):
    paginator = Paginator(trx_list, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj

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
    context = {}
    try:
        trx_list = user_transactions.get_all_transactions(requested_user=request.user)
        context['total_credit'], context['total_debit'] = user_transactions.get_credit_debit_summary(trx_list)
        context['page_obj'] = paginated_transaction_list(request, trx_list)
    except ValidationError as ve:
        context['errors'] = ve
    except Exception as e:
        messages.error(request, str(e))
    return render(request, 'transaction/index.html', context)

@login_required(login_url='login')
def transactions_by_fund_account(request, fund_acct_id):
    context = {}
    try:
        returned_data = user_transactions.get_transactions_by_fund_account(requested_user=request.user, fund_account_id=fund_acct_id)
        trx_list = returned_data[0]
        context['selected_fund_account'] = returned_data[1]
        context['total_credit'] = returned_data[2]
        context['total_debit'] = returned_data[3]
        context['page_obj'] = paginated_transaction_list(request, trx_list)
    except ValidationError as ve:
        context['errors'] = ve
    except Exception as e:
        messages.error(request, str(e))
    return render(request, 'transaction/index.html', context)

@login_required(login_url='login')
def transactions_by_category(request, category_id):
    context = {}
    try:
        returned_data = user_transactions.get_transactions_by_category(requested_user=request.user, category_id=category_id)
        trx_list = returned_data[0]
        context['selected_category'] = returned_data[1]
        context['total_credit'] = returned_data[2]
        context['total_debit'] = returned_data[3]
        context['page_obj'] = paginated_transaction_list(request, trx_list)
    except ValidationError as ve:
        context['errors'] = ve
    except Exception as e:
        messages.error(request, str(e))
    return render(request, 'transaction/index.html', context)

@login_required(login_url='login')
def create_transaction(request):
    try:
        context = get_form_common_context()
        if request.POST:
            trx, valid_tags = form_proccessing(request)
            trx.user = request.user
            trx = trx.create_by(requested_user=request.user)
            trx.tags.set(valid_tags)
            messages.success(request, 'Transaction added successfully!!!')
    except ValidationError as ve:
        context['errors'] = ve
    except Exception as e:
        messages.error(request, str(e))
    return render(request, 'transaction/form_create.html', context)

@login_required(login_url='login')
def update_transaction(request, id):
    try:
        context = get_form_common_context()
        context['trx'] = user_transactions.get_transaction_by_id(requested_user=request.user, id=id)
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
    except Exception as e:
        messages.error(request, str(e))
    return render(request, 'transaction/form_update.html', context)