from django.shortcuts import render, redirect
from django.views.generic.edit import FormView
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm, RegisterForm
from .models import User


def index(request):
    return render(request, 'index.html')


class LoginFormView(FormView):
    template_name = 'login.html'
    form_class = LoginForm
    success_url = 'Fuel:index'

    def form_valid(self, form):
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(self.request, username=username, password=password)
        if user is not None:
            login(self.request, user)
            return redirect("Fuel:index")
        else:
            return render(self.request, "index.html", {"error": True, "login_error": True})


class RegisterFormView(FormView):
    template_name = 'register.html'
    form_class = RegisterForm
    success_url = 'Fuel:login'

    def form_valid(self, form):
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        car_licence = form.cleaned_data['car_licence']
        phone_number = form.cleaned_data['phone_number']
        users = User.objects.filter(username=username)
        if users:
            return render(self.request, "index.html", {"error": True, "username_unavailable": True})
        else:
            user = User(username=username, first_name=first_name, last_name=last_name, password=password,
                        car_licence=car_licence, phone_number=phone_number)
            user.set_password(password)
            user.save()
            return redirect('Fuel:login')


def logout_user(request):
    logout(request)
    return redirect('/')
