from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from .models import Report
from .forms import ReportForm
from django.core.mail import EmailMessage

def _get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    return xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR")

@login_required(login_url="/users/login/")
def create_report(request,model_name,object_id):
    from board.models import Post, Comment, Room
    MODEL_MAP={"post":(Post,"pk"),"comment":(Comment,"pk"),"room":(Room, "slug")}
    alarm=0
    model,lookup=MODEL_MAP.get(model_name, (None, None))
    if not model:
        messages.error(request,"잘못된 신고 대상입니다.")
        return redirect('/') # 수정 필요 이전 상태로 돌아가기로 

    target=get_object_or_404(model, **{lookup: object_id})
    if request.method == "POST":
        form=ReportForm(request.POST)
        if form.is_valid():
            ct=ContentType.objects.get_for_model(model)
             # 1. 먼저 중복 신고가 있는지 확인합니다.
            if Report.objects.filter(content_type=ct, object_id=target.pk, reported_by=request.user).exists():
                messages.info(request, "이미 신고 내역이 있습니다.")
                return redirect(request.GET.get("next") or "/")

            # 2. 중복이 없으면, form 데이터로 Report 객체를 생성합니다. (detail 필드 포함)
            print(">>> Cleaned Data:", form.cleaned_data)
            report = form.save(commit=False)
            print(">>> Report Object Detail:", report.detail)

            # 3. 나머지 서버측 데이터를 채워줍니다.
            report.content_type = ct
            report.object_id = target.pk
            report.reported_by = request.user
            report.reporter_ip = _get_client_ip(request)
            report.user_agent = request.META.get("HTTP_USER_AGENT", "")
            
            # 4. 모든 데이터가 채워진 report 객체를 데이터베이스에 저장합니다.
            report.save()

            messages.success(request, "신고 접수가 완료되었습니다.")
            
            # 5. 이메일을 발송합니다.
            subject = "신고가 들어왔습니다."
            to = [settings.EMAIL_HOST_USER]
            from_email = settings.EMAIL_HOST_USER
            
            # 이제 report.detail에 상세 내용이 정상적으로 들어 있습니다.
            email_body = (
                f"[신고 대상] {model.__name__} (id={target.pk})\n"
                f"[사유] {report.get_reason_display()}\n" 
                f"[상세] {report.detail}\n"
                f"[신고자] {request.user} (id={request.user.id})\n"
            )
            EmailMessage(subject=subject, body=email_body, to=to, from_email=from_email).send(fail_silently=False)
            
            return redirect(request.GET.get("next") or "/")
        
        else:
            # 폼 유효성 검사 실패 시
            print("!!! FORM ERRORS:", form.errors) # 디버깅용
            messages.error(request, "입력값을 확인해 주세요.")
            return render(request, "moderation/report_form.html",{"form": form, "target": target, "model_name": model_name})
    
    # GET 요청 처리
    form = ReportForm()
    return render(request, "moderation/report_form.html", {"form": form, "target": target, "model_name": model_name})
# email 전송 

# def send_emil(reqest):
#     if alarm==1:
#         subject ="신고가 들어 왔습니다."
#         to = ["idy1618@naver.com"]
#         from_email="idy1618@naver.com"
#         messages=
