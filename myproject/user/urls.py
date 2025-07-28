from django.urls import path

from . import views

app_name = 'user'

urlpatterns = [
    path('mypage/',views.mypage, name='mypage'),
    path('logout/',views.logout_view, name='logout'),
    path('login/', views.login_page, name='login_page'),  # HTML 보여주는 뷰
    path('login/naver/', views.naver_login, name='naver_login'),  # 네이버 로그인 리디렉션
    path('naver/callback/', views.naver_login_callback, name='naver_callback'),  # 콜백 처리
]