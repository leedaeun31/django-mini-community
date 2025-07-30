from django.urls import path
from . import views

app_name='board'

urlpatterns=[
    path('comments/<int:comment_id>/edit/', views.edit_comment, name='edit_comment'),
    path('comments/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('<uuid:slug>/posts/<int:post_id>/',views.post_detail,name='post_detail'), # 게시글 생성 url
    path('<uuid:slug>/posts/<int:post_id>/edit/',views.edit_post,name='edit_post'), #게시글 수정
    path('<uuid:slug>/posts/<int:post_id>/delete/',views.delete_post,name='delete_post'), #게시글 삭제
    path('<uuid:slug>/posts/upload/',views.upload_post,name='upload_post'), # 게시물 업로드
    path('<uuid:slug>/kick/<int:user_id>',views.kick,name='kick'), #강퇴
    path('<uuid:slug>/setting',views.setting_room,name='setting_room'), # 방 설정
    path('<uuid:slug>/leave/',views.leave_room,name='leave_room'), # 방 나가기 
    path('<uuid:slug>/', views.room_detail, name='room_detail'), # 방 사이트 
    path('create/', views.create_room, name='create_room'), # room생성
]