from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..services import user_login_service, user_register_service
from ..model_forms import MyLoginForm, MyUserRegisterForm


@login_required(login_url='login')
def dashboard(request):
    # messages.success(request, "Sample success MEssage.")
    # messages.error(request, "Sample Error MEssage, jsut a random test message.")
    return render(request, 'dashboard/index.html')

# def shortcuts(request):
#     return render(request, 'shortcut/index.html')

# def loans(request):
#     return render(request, 'loan/index.html')

def login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = MyLoginForm()
    if request.POST:
        form = MyLoginForm(request.POST)
        if form.is_valid():
            success, msg = user_login_service.user_login(request, form.data.get('email'), form.data.get('password'))
            if success:
                messages.success(request, msg)
                return redirect('dashboard')
        else:
            if form.errors:
                for field_errors in form.errors.as_data.get('__all__', []):
                    for err in field_errors:
                        messages.error(request, err)
    return render(request, 'authentication/login.html', context={'form': form})

@login_required(login_url='login')
def logout(request):
    return render(request, 'authentication/logout.html')

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = MyUserRegisterForm()
    if request.POST:
        form = MyUserRegisterForm(data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            success, msg = user_register_service.user_register(email=email, username=username, password=password)
            if success:
                messages.success(request, msg)
                return redirect('login')
        else:
            if form.errors:
                for err in form.errors.as_data().get('__all__', []):
                    for e in err:
                        messages.error(request, e)
    return render(request, 'authentication/register.html', context={'form': form})

def not_found_404(request):
    return render(request, 'shared/404.html')

def no_permission(request):
    return render(request, 'shared/no_permission.html')