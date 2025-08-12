from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

class Report(models.Model):
    # 신고 대상
    content_type=models.ForeignKey(ContentType,on_delete=models.CASCADE)
    object_id=models.CharField(max_length=64) 
    target= GenericForeignKey("content_type", "object_id") 
    
    # 신고자
    reported_by=models.ForeignKey( settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL,related_name="reports")
    reported_id=models.GenericIPAddressField(null=True,blank=True)
    user_agent=models.TextField(blank=True,default="")

    # 내용
    REASONS=[("abuse","욕설/비하"),("spam","스팸/홍보"),("illegal","불법정보"),("etc","기타"),]
    reason=models.CharField(max_length=20,choices=REASONS)
    detail=models.TextField(blank=True)

    # 상태
    STATUS=[("pending","접수"),("accepted","조치완료"),("rejected","기각")]
    status=models.CharField(max_length=20,choices=STATUS,default='pending')

    created_at=models.DateField(auto_now_add=True)
    handled_at=models.DateTimeField(null=True,blank=True)
    reporter_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent  = models.TextField(blank=True, default="")

    class Meta:
        indexes=[
            models.Index(fields=["content_type","object_id"]),
            models.Index(fields=["status","-created_at"]),
        ]
        # 동일 사용자 중복신고 방지
        constraints=[
            models.UniqueConstraint(
                fields=["content_type","object_id","reported_by"],
                name="uniq_report_per_user_target",
                condition=~models.Q(reported_by=None)
            )
        ]
    
    def __str__(self):
        return f"[{self.get_status_display()}] {self.content_type}:{self.object_id}-{self.get_reason_display()}"
    
    def target_owner(self):
        t=self.target
        for attr in ("author","user","created_by","owner"):
            if hasattr(t,attr):
                return getattr(t,attr)
        return None
    
    def target_preview(self,length=120):
        t=self.target
        for attr in ('content','body','text', "message", "title"):
            if hasattr(t,attr):
                val=getattr(t, attr) or ""
                return (val[:length]+"...") if len(val)> length else val
        return ""
    
    def target_admin_url(self):
        try: 
            return reverse(
                f"admin:{self.content_type.app_label}_{self.content_type.model}_change",
                args=[self.object_id],
            )
        except Exception:
            return None

class UserDiscipline(models.Model):
    user=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="discipline")
    warnings=models.PositiveIntegerField(default=0)
    muted_until=models.DateTimeField(null=True,blank=True)
    suspended_until=models.DateTimeField(null=True,blank=True)
    banned_at=models.DateTimeField(null=True,blank=True)

    def active_atatus(self):
        now=timezone.now()
        if self.banned_at:
            return 'banned'
        if self.suspended_until and self.suspended_until > now:
            return 'suspended'
        if self.muted_until and self.muted_until > now:
            return 'muted'
        return 'ok'
    def clear_mute(self):
        self.muted_until=None
        self.save(update_fields=["muted_until"])
    def clear_suspend(self):
        self.suspended_until=None
        self.save(update_fields=['suspended_until'])
    def reactivate_user(self):
        self.banned_at=None
        self.save(update_fields=["banned_at"])
        self.usesr.is_active=True
        self.user.save(update_fields=['is_active'])
def ensure_discipline(user):
    obj,_ =UserDiscipline.objects.get_or_create(user=user)
    return obj

def add_warning(user,note:str=""):
    d=ensure_discipline(user)
    d.warnings +=1
    now=timezone.now()
    action=None

    if d.warnings==3 and (not d.muted_until or d.muted_until < now):
        d.muted_until=now+timedelta(days=1)
        action="muted_1d"
    elif d.warnings==5 and (not d.suspended_until or d.suspended_until <now):
        d.suspended_until=now+timedelta(days=7)
        action="suspended_7d"
    elif d.warnings >= 7 and d.banned_at:
        user.is_active=False
        user.save(update_fields=["is_active"])
        d.banned_at=now
        action="banned"
    d.save()
    return d, action