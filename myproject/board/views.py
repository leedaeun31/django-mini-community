from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Room, UserRoom
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import Post, Comment
User = get_user_model()

# Create your views here.

@login_required  # 게시글 업로드
def upload_post(request, slug):
    room = get_object_or_404(Room, slug=slug)

    if request.method == "POST":
        title = request.POST.get("title")
        text = request.POST.get("text")
        image = request.FILES.get("image")

        if not text and not image:
            messages.error(request, "글 또는 사진을 업로드 해주세요")
            return redirect("board:upload_post", slug=slug)
        Post.objects.create(room=room, author=request.user, title=title, text=text, image=image)
        messages.success(request, "게시글 등록이 완료되었습니다.")
        return redirect("board:room_detail", slug=slug)
    return render(request, "board/posts/upload_post.html", {"room": room})   # ✅ 경로 수정

@login_required  # 게시글 댓글 작성
def post_detail(request, slug, post_id):
    post = get_object_or_404(Post, id=post_id, room__slug=slug)
    comments = post.comments.all().order_by("-created_at")

    if request.method == "POST":
        text = request.POST.get("comment")
        if text:
            Comment.objects.create(post=post, author=request.user, text=text)
            return redirect("board:post_detail", slug=slug, post_id=post.id)
    return render(request, "board/posts/post_detail.html", {"post": post, "comments": comments})   # ✅ 경로 수정


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
        image = request.FILES.get('image')
        if not title:
            messages.error(request, "제목을 입력하세요")
            return redirect("board:edit_post", slug=slug, post_id=post.id)
        post.title = title
        post.text = text

        if image:
            post.image = image

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
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if request.user != comment.author:
        messages.error(request, "댓글 작성자만이 댓글을 수정할 수 있습니다.")
        return redirect('board:post_detail', slug=comment.post.room.slug, post_id=comment.post.id)

    if request.method == "POST":
        text = request.POST.get("text")
        if text:
            comment.text = text
            comment.save()
            messages.success(request, "댓글이 수정되었습니다.")
        return redirect("board:post_detail", slug=comment.post.room.slug, post_id=comment.post.id)
    return render(request, "board/posts/edit_comment.html", {"comment": comment})   # ✅ 경로 수정


@login_required  # 댓글 삭제
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if request.user != comment.author:
        messages.error(request, "댓글 작성자만이 댓글을 삭제할 수 있습니다.")
        return redirect("board:post_detail", slug=comment.post.room.slug, post_id=comment.post.id)

    comment.delete()
    messages.success(request, "댓글이 삭제되었습니다.")
    return redirect("board:post_detail", slug=comment.post.room.slug, post_id=comment.post.id)


@login_required
def setting_room(request, slug):
    room = get_object_or_404(Room, slug=slug)  # UUID로 방 정보 가져오기

    if request.user != room.created_by:
        messages.error(request, "방장만 설정 페이지 접근 가능합니다.")
        return redirect('board:room_detail', slug=slug)

    if request.method == "POST":
        new_name = request.POST.get("name")
        new_password = request.POST.get("password")

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


@login_required
def room_detail(request, slug):
    room = get_object_or_404(Room, slug=slug)

    # 유저 방 인증 체크
    try:
        user_room = UserRoom.objects.get(user=request.user, room=room)
        if not room.require_pin_everytime and user_room.authenticated:
            posts = room.posts.all().order_by("-created_at")  # 게시글 가져오기
            return render(request, "board/room_detail.html", {"room": room, "posts": posts})
    except UserRoom.DoesNotExist:
        user_room = None

    # PIN 입력 처리
    if request.method == "POST":
        pin = request.POST.get("password", "")
        if room.password and room.password != pin:
            messages.error(request, "PIN이 올바르지 않습니다.")
            return redirect("board:room_detail", slug=slug)

        if user_room:
            user_room.authenticated = True
            user_room.save()
        else:
            UserRoom.objects.create(user=request.user, room=room, authenticated=True)

        posts = room.posts.all().order_by("-created_at")
        return render(request, "board/room_detail.html", {"room": room, "posts": posts})

    # GET 요청 시
    posts = room.posts.all().order_by("-created_at")
    return render(request, "board/room_detail.html", {"room": room, "posts": posts})

