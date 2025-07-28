from django.db import models
from django.contrib.auth.models import AbstractUser # 사용자 모델 확장 

# Create your models here.
class User(AbstractUser):
    nickname = models.CharField(max_length=30)
    user_gender = models.CharField(max_length=10)
    user_phone_num = models.CharField(max_length=20)
    user_profile_image = models.ImageField(upload_to="profile_imagees/", blank=True)
    #social_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    #birth = models.DateField(null=True, blank=True)