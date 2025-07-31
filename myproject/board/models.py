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
    
# 게시물 업로드
class Post(models.Model):
    room=models.ForeignKey(Room,on_delete=models.CASCADE, related_name="posts") # 방 삭제시 게시글도 삭제
    author=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE) # 방에서 회원 나가면 게시글도 삭제
    title=models.CharField(max_length=100) #제목
    text=models.TextField(blank=True,null=True) #게시글
    created_at=models.DateTimeField(auto_now_add=True) # 게시글 처음 작성 시간
    updated_at=models.DateTimeField(auto_now=True) # 게시글 수정 시 자동 업데이트

    def __str__(self):
        return f"{self.title} ({self.room.name})"
    
    @property # 댓글의 개수를 속성처럼 사용할 수 있게 해준다.
    def comment_count(self):
        return self.comments.count()  # 게시물 댓글의 개수
# related_name : 역참조 이름(room.posts 또는 post.comments)으로 데이터를 쉽게 가져올 수 있게 함.
# 댓글 

# post 하나에 여러 장의 이미지 연결 
class PostImage(models.Model):
    post=models.ForeignKey(Post,on_delete=models.CASCADE, related_name='images')
    image=models.ImageField(upload_to="posts/images/")

    def __str__(self):
        return f"Image for {self.post.title}"
    
class Comment(models.Model):
    post=models.ForeignKey(Post,on_delete=models.CASCADE, related_name='comments')
    author=models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text=models.TextField() # 댓글 내용
    created_at=models.DateTimeField(auto_now_add=True) # 첫 댓글 시간
    updated_at=models.DateTimeField(auto_now=True) # 수정된 시간 

    def __str__(self):
        return f"Comment by {self.author.username}"
 