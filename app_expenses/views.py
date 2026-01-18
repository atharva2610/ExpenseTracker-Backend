from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .services.auth_service.user_login_service import user_login
from .model_forms import MyLoginForm

@login_required(login_url='login')
def dashboard(request):
    return render(request, 'dashboard/index.html')

def transactions(request):
    return render(request, 'transaction/index.html')

def fund_accounts(request):
    return render(request, 'fund_account/index.html')

def categories(request):
    return render(request, 'category/index.html')

def tags(request):
    return render(request, 'tag/index.html')

def shortcuts(request):
    return render(request, 'shortcut/index.html')

def reports(request):
    return render(request, 'report/index.html')

def loans(request):
    return render(request, 'loan/index.html')

def login(request):
    form = MyLoginForm()
    if request.POST:
        form = MyLoginForm(request.POST)
        if form.is_valid():
            success, msg = user_login(request, form.data.get('email'), form.data.get('password'))
            if success:
                messages.success(request, msg)
                return redirect('dashboard')
        else:
            messages.error(request, msg)
    return render(request, 'authentication/login.html', context={'form': form})

def logout(request):
    return render(request, 'authentication/logout.html')

def register(request):
    return render(request, 'authentication/register.html')

def not_found_404(request):
    return render(request, 'shared/404.html')

def no_permission(request):
    return render(request, 'shared/no_permission.html')
