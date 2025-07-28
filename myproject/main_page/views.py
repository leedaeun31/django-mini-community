from django.shortcuts import render, redirect
from board.models import Room, UserRoom
import re
from django.contrib import messages

def main(request):
    # 로그인 안 된 상태: 그냥 화면만 보여줌
    if not request.user.is_authenticated:
        return render(request, "main/main.html")

    # 로그인 된 상태
    if request.method == "POST":
        link = request.POST.get("link").strip()

        match = re.search(r"[0-9a-fA-F-]{36}", link)
        if match:
            slug = match.group(0)
            try:
                room = Room.objects.get(slug=slug)
                # ✅ UserRoom DB에 사용자와 방 연결 저장 (중복 방지)
                UserRoom.objects.get_or_create(user=request.user, room=room)

                messages.success(request, f"'{room.name}' 방이 등록되었습니다.")
            except Room.DoesNotExist:
                messages.error(request, "해당 방이 존재하지 않습니다.")
        else:
            messages.error(request, "올바른 링크 입력")

        return redirect("main_page:main")  # 메인 페이지로 다시 리다이렉트

    # GET 요청일 때 목록 보여주기 (로그인 사용자만)
    user_rooms = UserRoom.objects.filter(user=request.user).select_related('room')
    rooms = [ur.room for ur in user_rooms]
    return render(request, "main/main.html", {"rooms": rooms})