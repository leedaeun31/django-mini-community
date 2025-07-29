from django.db import models
from django.contrib.auth.models import AbstractUser # 사용자 모델 확장 
from django.conf import settings
import os
# Create your models here.
def user_profile_image_path(instance, filename):
    # 확장자 추출
    ext = filename.split('.')[-1]
    # 파일명을 username_profile.확장자 형태로 저장
    filename = f"profile.{ext}"
    # 유저별 디렉토리로 저장
    return os.path.join('profile_images', str(instance.id), filename)

class User(AbstractUser):
    nickname = models.CharField(max_length=30)
    user_gender = models.CharField(max_length=10)
    user_phone_num = models.CharField(max_length=20)
    user_profile_image = models.ImageField(upload_to="user_profile_image_path", blank=True, default="profile_images/default_profile.png")
    #social_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    #birth = models.DateField(null=True, blank=True)