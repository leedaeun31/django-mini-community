from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Room, UserRoom, PostImage
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import Post, Comment
from django.views.decorators.http import require_POST
from django.http import JsonResponse
import json

User = get_user_model()


# Create your views here.

@login_required  # 게시글 업로드
def upload_post(request, slug):
    room = get_object_or_404(Room, slug=slug)

    if request.method == "POST":
        title = request.POST.get("title")
        text = request.POST.get("text")
        images = request.FILES.getlist("images") # getlist로 이미지를 리스트 형식으로 여러장 업로드 가능하게

        if len(images)>5:
                messages.error(request,"사진은 최대 5장까지 업로드 가능합니다.")
                return redirect("board:upload_post",slug=slug)
        
        if not text and not images:
            messages.error(request, "글 또는 사진을 업로드 해주세요")
            return redirect("board:upload_post", slug=slug)
        
        post=Post.objects.create(room=room, author=request.user, title=title, text=text)
        
        for img in images:
            PostImage.objects.create(post=post,image=img)
        
        messages.success(request, "게시글 등록이 완료되었습니다.")
        return redirect("board:room_detail", slug=slug)
    return render(request, "board/posts/upload_post.html", {"room": room}) 

@login_required  # 게시글 댓글 작성
def post_detail(request, slug, post_id):
    post = get_object_or_404(Post, id=post_id, room__slug=slug)
    comments = post.comments.all().order_by("-created_at")

    if request.method == "POST":
        text = request.POST.get("comment")
        action=request.POST.get("action")
        comment_id=request.POST.get("comment_id")

        if action == "create":
            text = request.POST.get("comment")
            if text.strip():
                Comment.objects.create(post=post, author=request.user, text=text)
            
        elif action=="edit":
            comment=get_object_or_404(Comment,id=comment_id)

            if request.user==comment.author:
                comment.text=request.POST.get("comment")
                comment.save()
        elif action=="delete":
            comment=get_object_or_404(Comment,id=comment_id)
            if request.user==comment.author:
                comment.delete()

        return redirect("board:post_detail", slug=slug, post_id=post.id)
    return render(request, "board/posts/post_detail.html", {"post": post, "comments": comments}) 


@login_required  # 게시물 수정
def edit_post(request, slug, post_id):
    post = get_object_or_404(Post, id=post_id, room__slug=slug)

    # 작성자만 수정 가능
    if request.user != post.author:
        messages.error(request, "본인만 수정 가능합니다.")
        return redirect("board:post_detail", slug=slug, post_id=post_id)

    if request.method == "POST":
        title = request.POST.get('title')
        text = request.POST.get('text')
        images = request.FILES.getlist('images')
        if not title:
            messages.error(request, "제목을 입력하세요")
            return redirect("board:edit_post", slug=slug, post_id=post.id)
        post.title = title
        post.text = text

        if images:
            post.images.all().delete()
            for img in images:
                PostImage.objects.create(post=post,image=img)

        post.save()
        messages.success(request, "게시글이 수정되었습니다.")
        return redirect("board:post_detail", slug=slug, post_id=post.id)
    return render(request, "board/posts/edit_post.html", {"post": post})

@login_required  # 게시글 삭제
def delete_post(request, slug, post_id):
    post = get_object_or_404(Post, id=post_id, room__slug=slug)

    if request.user != post.author:
        messages.error(request, "게시물을 작성자만 삭제 가능합니다.")
        return redirect("board:post_detail", slug=slug, post_id=post_id)
    post.delete()
    messages.success(request, "게시글 삭제가 완료되었습니댜.")
    return redirect("board:room_detail", slug=slug)

@login_required
def setting_room(request, slug):
    room = get_object_or_404(Room, slug=slug)  # UUID로 방 정보 가져오기

    if request.user != room.created_by:
        messages.error(request, "방장만 설정 페이지 접근 가능합니다.")
        return redirect('board:room_detail', slug=slug)

    if request.method == "POST":
        new_name = request.POST.get("name")
        new_password = request.POST.get("password")
        room.require_pin_everytime = bool(request.POST.get("require_pin_everytime"))
        
        if new_name:
            room.name = new_name
            messages.success(request, "방 이름이 변경되었습니다.")
        if new_password:
            if len(new_password) == 4 and new_password.isdigit():
                room.password = new_password
                messages.success(request, "방 PIN 번호가 변경되었습니다.")
            else:
                messages.error(request, "PIN은 4자리 숫자여야 합니다.")
                return redirect('board:setting_room', slug=slug)
        room.save()

        return redirect('board:setting_room', slug=slug)
    participants = UserRoom.objects.filter(room=room).select_related('user')
    return render(request, 'board/setting_room.html', {'room': room, "participants": participants})   # ✅ 경로 수정


@login_required
def kick(request, slug, user_id):
    room = get_object_or_404(Room, slug=slug)

    if request.user != room.created_by:
        messages.error(request, "방장만 강퇴할 수 있습니다.")
        return redirect('board:room_detail', slug=slug)

    user = get_object_or_404(User, id=user_id)

    UserRoom.objects.filter(user=user, room=room).delete()
    messages.success(request, f"{user.username}님을 강퇴했습니다.")
    return redirect('board:setting_room', slug=slug)


@login_required
def leave_room(request, slug):
    room = get_object_or_404(Room, slug=slug)

    if request.user == room.created_by:
        room.delete()
        messages.success(request, f"'{room.name}' 방을 삭제했습니다.")
    else:
        UserRoom.objects.filter(user=request.user, room=room).delete()
        messages.success(request, f"'{room.name}' 방에서 나갔습니다.")

    return redirect('main_page:main')


@login_required  # 로그인 상태에서만
def create_room(request):
    if request.method == 'POST':
        name = request.POST['name']
        password = request.POST.get('password', '')  # get 사용시 소괄호() 사용 
        room = Room.objects.create(name=name, password=password, created_by=request.user)
        UserRoom.objects.get_or_create(user=request.user, room=room, defaults={'authenticated': True})
        # 생성된 room의 초대링크 보여줌
        return render(request, 'board/create_room.html', {'room': room})

    # GET 요청 시 방 생성 폼 표시
    return render(request, 'board/create_room.html')

from django.views.decorators.http import require_POST

@require_POST
@login_required
def check_pin(request, slug):
    room = get_object_or_404(Room, slug=slug)
    data = json.loads(request.body)
    pin = data.get("pin")

    if pin == room.password:
        # 자동 인증 모드일 때 세션에 저장
        if not room.require_pin_everytime:
            if "authenticated_rooms" not in request.session:
                request.session["authenticated_rooms"] = []
            if str(slug) not in request.session["authenticated_rooms"]:
                request.session["authenticated_rooms"].append(str(slug))
                request.session.modified = True
        return JsonResponse({"success": True})
    return JsonResponse({"success": False})


@login_required
def room_detail(request, slug):
    room = get_object_or_404(Room, slug=slug)
    # 체크박스 해제된 경우는 세션 인증 있으면 바로 입장 가능
    if room.password and not room.require_pin_everytime:
        authenticated_rooms = request.session.get("authenticated_rooms", [])
        if str(slug) not in authenticated_rooms:
            return redirect("main_page:main")  # 세션 인증 없으면 메인으로 보냄

    posts = Post.objects.filter(room=room).order_by("-created_at")
    return render(request, "board/room_detail.html", {"room": room, "posts": posts})

@login_required
def check_session(request, slug):
    authenticated_rooms = request.session.get("authenticated_rooms", [])
    is_authenticated = str(slug) in authenticated_rooms
    return JsonResponse({"authenticated": is_authenticated})

 # [방 클릭] 
#    ↓
# [JS] openPinModal() → 백엔드로 /check_session/ 요청
#    ↓
# [백엔드] 세션에 인증된 slug가 있으면 → True 반환
#    ↓
# [JS]
#  - True: 바로 입장 (window.location.href)
#  - False: PIN 모달 열고 입력 받기
#    ↓
# [PIN 입력 후]
#  → /check_pin/으로 POST 요청
#    ↓
# [백엔드] PIN 일치 + 옵션 확인 → 세션에 slug 저장
