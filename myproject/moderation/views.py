from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from .models import Report
from .forms import ReportForm

def _get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    return xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR")

@login_required(login_url="/users/login/")
def create_report(request,model_name,object_id):
    from board.models import Post, Comment, Room
    MODEL_MAP={"post":(Post,"pk"),"comment":(Comment,"pk"),"room":(Room, "slug")}
    model,lookup=MODEL_MAP.get(model_name, (None, None))
    if not model:
        messages.error(request,"잘못된 신고 대상입니다.")
        return redirect('/') # 수정 필요 이전 상태로 돌아가기로 

    target=get_object_or_404(model, **{lookup: object_id})
    if request.method == "POST":
        form=ReportForm(request.POST)
        if form.is_valid():
            ct=ContentType.objects.get_for_model(model)
            report,created=Report.objects.get_or_create(
                content_type=ct,object_id=target.pk,reported_by=request.user,
                defaults={
                    'reason':form.cleaned_data['reason'],
                    'detail':form.cleaned_data['detail'],
                    'reporter_ip':_get_client_ip(request),
                    'user_agent':request.META.get("HTTP_USER_AGENT",""),
                }
            )
            if not created:
                messages.info(request,"이미 신고 내역이 있습니다.")
            else:
                messages.success(request,"신고 접수가 완료되었습니다.")
            return redirect(request.GET.get("next")or"/") # 수정 이전 페잊로
        else:
            messages.error(request, "입력값을 확인해 주세요.")
            return render(request, "moderation/report_form.html",
                          {"form": form, "target": target, "model_name": model_name})
        
    form=ReportForm()
    return render(request,"moderation/report_form.html",{"form":form,"target":target,"model_name":model_name})