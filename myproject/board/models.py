from django.db import models
from django.conf import settings
import uuid # 고유한 랜덤 ID를 생성
# Create your models here.

# db 관리 내역 
class UserRoom(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    room=models.ForeignKey('Room',on_delete=models.CASCADE)
    created_at=models.DateTimeField(auto_now_add=True)
    authenticated=models.BooleanField(default=False) # Pin 인증 여부 확인
    class Meta:
         unique_together = ('user', 'room') 
    def __str__(self):
        return f"{self.user.username}-{self.room.name}"

# 기본 Room 설정     
class Room(models.Model):
    name=models.CharField(max_length=100)
    require_pin_everytime = models.BooleanField(default=True) # 비밀번호 매번 입력 
    slug=models.UUIDField(default=uuid.uuid4,unique=True) #초대링크 생성 / unique=True => 중복방지
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE) # 방 생성자 
    created_at=models.DateTimeField(auto_now_add=True) # 날짜 및 시간 설정 / auto_now_add= => 자동으로 현재 날짜 및 시간 저장
    password=models.CharField(max_length=4,blank=True) # PIN 번호 설정 
    # 관리자 터미널에서 객체 출력시 보여줄 문자열 지정 
    def __str__(self):
        return self.name