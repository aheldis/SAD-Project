import time

from django.contrib.auth.models import Group
from django.http.response import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic.edit import FormView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import requests
import folium
from django.contrib import messages

from .models import User, FuelRequest
from .forms import LoginForm, RegisterForm, RequestFuelForm
from .utils import *


def index(request):
    if request.user.is_authenticated and not request.user.is_superuser:
        if request.user.role == User.Role.AGENT:
            return agent_page(request)
        elif request.user.role == User.Role.SUPERVISOR:
            redirect('admin:index')
        return redirect('Fuel:dashboard')
    return render(request, 'index.html')


def visitor_ip_address(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class LoginFormView(FormView):
    template_name = 'login.html'
    form_class = LoginForm
    success_url = 'Fuel:index'

    def form_valid(self, form):
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(self.request, username=username, password=password)
        if user:
            if user.role == User.Role.AGENT:
                login(self.request, user)
                return redirect("Fuel:agent_page")

            elif user.role == User.Role.SUPERVISOR:
                login(self.request, user)
                return redirect("admin:index")

            login(self.request, user)
            return redirect('Fuel:dashboard')
        else:
            return render(self.request, "index.html", {"error": True, "login_error": True})


class RequestFuelFormView(FormView):
    template_name = 'dashboard.html'
    form_class = RequestFuelForm
    success_url = 'Fuel:dashboard'

    def form_valid(self, form):
        address = requests.get('https://api.ipify.org').content.decode('utf8')
        amount = form.cleaned_data['amount']
        fuel_request = FuelRequest(address=address, amount=amount,
                                   user=User.objects.get(username=self.request.user.username))
        fuel_request.save()
        return redirect("Fuel:dashboard")

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        fuel_request = FuelRequest.objects.filter(
            user=self.request.user).exclude(status=FuelRequest.Status.SUCCESSFUL)
        assert len(fuel_request) in [1, 0]

        if len(fuel_request) == 0:
            context_data.update(
                {'no_open_request': True, 'request_assigned': False})
            return context_data

        fuel_request = fuel_request[0]
        if fuel_request.status == FuelRequest.Status.LOOKING_FOR_AGENT:
            context_data.update(
                {'no_open_request': False, 'request_assigned': False})
            return context_data
        context_data.update(
            {'no_open_request': False, 'request_assigned': True, 'agent_first_name': fuel_request.agent.first_name,
             'agent_last_name': fuel_request.agent.last_name, 'agent_car_licence': fuel_request.agent.car_licence,
             'agent_phone_number': fuel_request.agent.phone_number})
        return context_data


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
        role = form.cleaned_data['role']
        users = User.objects.filter(username=username)
        ip_address = requests.get('https://api.ipify.org').content.decode('utf8')

        if users:
            return render(self.request, "index.html", {"error": True, "username_unavailable": True})
        user = User(username=username, first_name=first_name, last_name=last_name, password=password,
                    car_licence=car_licence, phone_number=phone_number, ip_address=ip_address)
        user.set_password(password)
        user.role = role
        user.save()
        if user.role == User.Role.SUPERVISOR:
            Group.objects.get(name='supervisor').user_set.add(user)
        return redirect('Fuel:login')


@login_required
def agent_page(request):
    temp = User.objects.all().filter(username=request.user.username)
    if temp:
        if temp[0].status == User.StatusTypes.UNAVAILABLE:  # agent is unavailable
            return render(request, "agent.html", {'status': temp[0].status})

        fuel_request = FuelRequest.objects.filter(
            agent=temp[0], status=FuelRequest.Status.IN_PROGRESS)
        assert len(fuel_request) in [1, 0]
        if len(fuel_request) == 0:  # no fuel request assigned to agent
            return render(request, "agent.html", {'status': temp[0].status})

        else:  # a request is assigned to agent, his status becomes occupied
            temp[0].status = User.StatusTypes.OCCUPIED
            temp[0].save()
            fuel_request = fuel_request[0]
            response_data = {'status': temp[0].status}
            response_data['user_phone_number'] = fuel_request.user.phone_number
            response_data['user_first_name'] = fuel_request.user.first_name
            response_data['user_last_name'] = fuel_request.user.last_name
            response_data['user_address'] = fuel_request.address
            response_data['user_amount'] = fuel_request.amount
            response_data['user_car_licence'] = fuel_request.user.car_licence
            return render(request, "agent.html", response_data)

    return logout_user(request)


@login_required
def logout_user(request):
    logout(request)
    return redirect('Fuel:index')


@login_required
def change_status(request):
    users = User.objects.all().filter(username=request.user.username)
    if users:
        user = users[0]
        if user.status == User.StatusTypes.AVAILABLE:
            user.status = User.StatusTypes.UNAVAILABLE
        elif user.status == User.StatusTypes.UNAVAILABLE:
            user.status = User.StatusTypes.AVAILABLE
        user.save()
        return redirect("Fuel:agent_page")

    return logout_user(request)


@login_required
def mission_complete(request):
    users = User.objects.all().filter(username=request.user.username)
    if users:
        fuel_request = FuelRequest.objects.filter(
            agent=users[0], status=FuelRequest.Status.IN_PROGRESS)
        assert len(fuel_request) in [1, 0]

        if len(fuel_request) == 0:
            return redirect("Fuel:agent_page")
        else:
            fuel_request = fuel_request[0]
            fuel_request.status = FuelRequest.Status.SUCCESSFUL
            fuel_request.save()
            users[0].status = User.StatusTypes.AVAILABLE
            users[0].save()
            return redirect("Fuel:agent_page")

    return logout_user(request)


@login_required
def check_request_assigned(request):
    fuel_request = FuelRequest.objects.filter(
        agent=request.user).exclude(status=FuelRequest.Status.SUCCESSFUL)
    assert len(fuel_request) in [1, 0]
    if len(fuel_request) == 0:
        return HttpResponse("")

    fuel_request = fuel_request[0]
    assert fuel_request.status == FuelRequest.Status.IN_PROGRESS
    return HttpResponse('assigned')


@login_required
def check_fuel_request_assigned(request):
    fuel_request = FuelRequest.objects.filter(
        user=request.user).exclude(status=FuelRequest.Status.SUCCESSFUL)
    assert len(fuel_request) in [1, 0]
    if len(fuel_request) == 0:
        return HttpResponse("")

    fuel_request = fuel_request[0]
    if fuel_request.status == FuelRequest.Status.LOOKING_FOR_AGENT:
        return HttpResponse("")
    return HttpResponse('assigned')


def show_map(request):
    ips = []
    user = request.user
    role = user.role
    message = 'No IP address exists'
    colors = []
    if role == User.Role.AGENT:
        all_fuels = FuelRequest.objects.all()
        for fuels in all_fuels:
            if (fuels.agent == user) and (fuels.address not in ips):
                ips.append([fuels.address, 'Order'])
                colors.append('red')
        message = 'No fuel request exists'
    elif user.is_superuser:
        all_fuels = FuelRequest.objects.all()
        for fuels in all_fuels:
            if fuels.status != FuelRequest.Status.SUCCESSFUL and fuels.address not in ips:
                ips.append([fuels.address, 'Order'])
                color = 'blue' if fuels.status == FuelRequest.Status.LOOKING_FOR_AGENT else 'green'
                colors.append(color)
        all_users = User.objects.all()
        for user in all_users:
            if user.role == User.Role.AGENT and user.status == User.StatusTypes.AVAILABLE:
                if user.ip_address not in ips:
                    ips.append([user.ip_address, 'Agent'])
    elif role == User.Role.USER:
        return redirect('Fuel:dashboard')

    try:
        locations = []
        for ip in ips:
            ipDict = {}
            ipDict['query'] = ip[0]
            locations.append(ipDict)
        response = requests.post("http://ip-api.com/batch", json=locations).json()
        points = []
        for i in range(len(response)):
            points.append([response[i]['lat'], response[i]['lon'], ips[i][1]])

        print("points:---------", points)
        my_map = folium.Map(location=get_center_coordinates(points), zoom_start=get_zoom(points))

        feature_group = folium.FeatureGroup("Locations")

        for i in range(len(points)):
            feature_group.add_child(folium.Marker(location=[points[i][0], points[i][1]],
                                                  popup=points[i][2], icon=folium.Icon(color=colors[i])))

        my_map.add_child(feature_group)
        return render(request, 'map.html', {"map": my_map._repr_html_(), "error": False})
    except:
        return render(request, 'map.html', {"error": True, "message": message})
