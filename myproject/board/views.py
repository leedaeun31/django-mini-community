from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Room

# Create your views here.

@login_required # 로그인 상태에서만
def create_room(request):
    if request.method == 'POST':
        name=request.POST['name'] 
        room=Room.objects.create(name=name, created_by=request.user)

        #생성된 room의 초대링크 보여줌
        return render(request, 'board/create_room.html',{'room':room})
    
    # 만약 요청이 Get일 떄는 방 이름을 입력하는 메인 이동 보여주기 | 방 생성 누르면 기본적으로 get 요청이 들어오는 듯
    return render(request, 'board/create_room.html')
@login_required
def room_detail(request, slug):
    room = get_object_or_404(Room, slug=slug)
    return render(request, 'board/room_detail.html', {'room': room})