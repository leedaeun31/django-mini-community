from django.urls import path

from . import views

app_name='main_page'

urlpatterns = [ 
    path('',views.main, name='main'),
]