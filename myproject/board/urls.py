from django.urls import path
from . import views

app_name='board'

urlpatterns=[
    path('<uuid:slug>/', views.room_detail, name='room_detail'),
    path('create/', views.create_room, name='create_room'), # room생성
]