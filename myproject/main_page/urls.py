from django.urls import path

from . import views

app_name='main_page'

urlpatterns = [ 
    #path('guidelines/',views.guidelines_view,name='guidelines'),
    path('',views.main, name='main'),
]