from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormView, CreateView
from Fuel.forms import LoginForm
from Fuel.models import User

def index(request):
    return render(request, 'index.html')

class LoginFormView(FormView):
    template_name = 'login.html'
    form_class = LoginForm
    success_url = '/dashboard/'

    def form_valid(self, form):
        # login function
        return super().form_valid(form)


class UserCreateView(CreateView):
    template_name = 'signup.html'
    model = User
    fields = ['first_name', 'last_name', 'username', 'password', 'car_licence', 'phone_number']