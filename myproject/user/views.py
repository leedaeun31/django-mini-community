import requests
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.conf import settings
from django.core.files.base import ContentFile
from user.models import User
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import os 

client_id = settings.NAVER_CLIENT_ID
client_secret = settings.NAVER_CLIENT_SECRET
callback_url = settings.NAVER_CALLBACK_URL

@login_required
def mypage(request):
    if request.method == "POST":
        username = request.POST.get("username")

        if username:
            # username이 코난이면 기존 이미지 삭제
            if "코난" in username or "탐정" in username:
                if request.user.user_profile_image:
                    request.user.user_profile_image.delete(save=False)
                    request.user.user_profile_image = None

            request.user.username = username
            request.user.save()
            messages.success(request, "이름이 성공적으로 변경되었습니다!")
            return redirect("user:mypage")
        
        profile_image = request.FILES.get("profile_image")

        if profile_image:
            request.user.user_profile_image = profile_image
            request.user.save()
            messages.success(request, "프로필 이미지가 성공적으로 업로드되었습니다.")
            return redirect("user:mypage")

    return render(request, 'mypage.html')


def login_page(request):
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('main_page:main')

def naver_login(request):
    state = "RANDOM_STATE"
    return redirect(
        f"https://nid.naver.com/oauth2.0/authorize?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={callback_url}"
        f"&state={state}"
    )


def naver_login_callback(request):
    code = request.GET.get("code")
    state = request.GET.get("state")

    # Access token 요청
    token_request = requests.post(
        "https://nid.naver.com/oauth2.0/token",
        data={
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": callback_url,
            "code": code,
            "state": state,
        },
    )
    token_json = token_request.json()

    if "error" in token_json:
        return redirect("/")

    access_token = token_json.get("access_token")

    # 사용자 정보 요청
    profile_request = requests.get(
        "https://openapi.naver.com/v1/nid/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    profile_json = profile_request.json()

    if profile_json.get("resultcode") != "00":
        return redirect("/")

    response = profile_json.get("response")
    email = response.get("email")
    name = response.get("name")
    profile_image_url = response.get("profile_image")
    #birth = response.get("birthday")
    #birth_year = response.get("birthyear")
    #phone_number = response.get("mobile")
    gender_map = {"M": "M", "F": "F"}
    user_gender = gender_map.get(response.get("gender"), "U")

    # full_birth = None
    # if birth and birth_year:
    #     full_birth = f"{birth_year}-{birth[:2]}-{birth[3:]}"

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        user = User.objects.create_user(
            email=email,
            #social_id=f"naver_{response.get('id')}",
            username=name,
            nickname=name,
            #birth=full_birth,
            user_gender=user_gender,
            #user_phone_num=phone_number,
        )
        if profile_image_url:
            image_response = requests.get(profile_image_url)
            if image_response.status_code == 200:
                image_name = f"profile_images/{user.email.replace('@','_')}.jpg"
                user.user_profile_image.save(image_name, ContentFile(image_response.content))
        user.save()

    login(request, user)
    return redirect('main_page:main')
