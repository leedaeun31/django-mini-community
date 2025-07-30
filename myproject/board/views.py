from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Room, UserRoom
from django.contrib import messages

# Create your views here.

@login_required 
def setting_room(request,slug):
    room = get_object_or_404(Room, slug=slug) #UUID로 방 정보 가져오기
    return render(request, 'board/setting_room.html', {'room': room})
@login_required 
def leave_room(request,slug):
    room=get_object_or_404(Room,slug=slug)

    if request.user == room.created_by:
        room.delete()
        messages.success(request,f"'{room.name}' 방을 삭제했습니다.")
    else:
        UserRoom.objects.filter(user=request.user,room=room).delete()
        messages.success(request,f"'{room.name}' 방에서 나갔습니다.")
    
    return redirect('main_page:main')
    
@login_required # 로그인 상태에서만
def create_room(request):
    if request.method == 'POST':
        name=request.POST['name'] 
        password=request.POST.get('password','') # get 사용시 소괄호() 사용 
        room=Room.objects.create(name=name,password=password, created_by=request.user)
        UserRoom.objects.get_or_create(user=request.user,room=room,defaults={'authenticated':True})
        #생성된 room의 초대링크 보여줌
        return render(request, 'board/create_room.html',{'room':room})
    
    # 만약 요청이 Get일 떄는 방 이름을 입력하는 메인 이동 보여주기 | 방 생성 누르면 기본적으로 get 요청이 들어오는 듯
    return render(request, 'board/create_room.html')
@login_required
def room_detail(request, slug):
    room = get_object_or_404(Room, slug=slug) #UUID로 방 정보 가져오기

    try:
        user_room=UserRoom.objects.get(user=request.user, room=room)
        if not room.require_pin_everytime and user_room.authenticated:
            return render(request,"room_detail.html",{"room:",room})
    except UserRoom.DoesNotExist:
        user_room=None
    
    if request.method =="POST":
        pin=request.POST.get("password","")
        if request.password and room.password !=pin:
            messages.error(request,"PIN이 올바르지 않습니다.")
            return redirect("board:room_detail",slug=slug)
        
        # 인증 성공 : room 생성 및 업데이트
        if user_room:
            user_room.authenticated=True
            user_room.save() 
        else: 
            UserRoom.objects.create(user=request.user,room=room,authenticated=True)
        return render(request, "room_detail.html", {"room":room})
    
    return render(request, 'board/room_detail.html', {'room': room})