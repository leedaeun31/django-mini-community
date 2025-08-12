from django.urls import path
from . import views

app_name = "moderation"
urlpatterns = [
    path("report/<str:model_name>/<str:object_id>/", views.create_report, name="create"),
]
