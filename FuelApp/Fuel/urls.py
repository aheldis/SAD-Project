from django.urls import path

from . import views
app_name = 'Fuel'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/',views.LoginFormView.as_view(), name='login'),
    path('signup/',views.UserCreateView.as_view(), name='signup')
]