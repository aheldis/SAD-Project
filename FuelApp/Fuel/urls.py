from django.urls import path

from .views import *

app_name = 'Fuel'
urlpatterns = [
    path('', index, name='index'),
    path('login/', LoginFormView.as_view(), name='login'),
    path('register/', RegisterFormView.as_view(), name='register'),
    path('logout/', logout_user, name='logout'),
]
