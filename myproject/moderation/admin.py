# moderation/admin.py
from datetime import timedelta

from django.contrib import admin, messages
from django.utils import timezone
from django.utils.html import format_html

from django.urls import reverse
from .models import Report, UserDiscipline, ensure_discipline, add_warning

# ✅ 프런트(서비스) URL을 만들 때 실제 모델 타입을 구분하려고 가져옵니다.
#    프로젝트의 실제 경로에 맞게 import (앱명이 board인 구조 기준)
from board.models import Room, Post, Comment


def _owner_of_report(r: Report):
    t = getattr(r, "target", None)
    if not t:
        return None
    for attr in ("author", "user", "created_by", "owner", "writer"):
        if hasattr(t, attr):
            return getattr(t, attr)
    return None


def _admin_url_for_report(r: Report):
    try:
        ct = r.content_type
        return reverse(f"admin:{ct.app_label}_{ct.model}_change", args=[r.object_id])
    except Exception:
        return None


# ✅ 프런트(서비스) 상세 페이지 URL 만들기
def _front_url_for_target(t):
    try:
        if isinstance(t, Post):
            return reverse("board:post_detail", args=[t.room.slug, t.id])
        elif isinstance(t, Comment):
            url = reverse("board:post_detail", args=[t.post.room.slug, t.post.id])
            # 댓글로 스크롤 이동(앵커는 템플릿에서 id="comment-{{comment.id}}" 달아주면 좋음)
            return f"{url}#comment-{t.id}"
        elif isinstance(t, Room):
            return reverse("board:room_detail", args=[t.slug])
    except Exception:
        pass
    return None


# ✅ 방(룸)으로 바로 가는 URL (Post/Comment인 경우 방을 역추적)
def _front_room_url_for_target(t):
    try:
        if isinstance(t, Post):
            return reverse("board:room_detail", args=[t.room.slug])
        elif isinstance(t, Comment):
            return reverse("board:room_detail", args=[t.post.room.slug])
        elif isinstance(t, Room):
            return reverse("board:room_detail", args=[t.slug])
    except Exception:
        pass
    return None


def _preview_of_target(r: Report, length: int = 120):
    t = getattr(r, "target", None)
    if not t:
        return ""
    for attr in ("content", "body", "text", "message", "title"):
        if hasattr(t, attr):
            val = getattr(t, attr) or ""
            return (val[:length] + "…") if len(val) > length else val
    return ""


# --------------------- 리포트 액션들(기존 + 부과/해제) ---------------------

@admin.action(description="선택 신고 → 승인(경고 1회)")
def accept_and_warn(modeladmin, request, queryset):
    ok = warned = 0
    for r in queryset:
        r.status = "accepted"
        r.handled_at = timezone.now()
        r.save(update_fields=["status", "handled_at"])
        u = _owner_of_report(r)
        if u:
            add_warning(u, note=f"report#{r.id}")
            warned += 1
        ok += 1
    messages.success(request, f"{ok}건 승인, 경고 {warned}건 부여.")

@admin.action(description="선택 신고 → 기각")
def mark_rejected(modeladmin, request, queryset):
    cnt = queryset.update(status="rejected", handled_at=timezone.now())
    messages.info(request, f"{cnt}건 기각.")

@admin.action(description="대상 콘텐츠 삭제(소프트→없으면 하드)")
def delete_targets(modeladmin, request, queryset):
    n = 0
    for r in queryset:
        t = getattr(r, "target", None)
        if not t:
            continue
        if hasattr(t, "is_deleted"):
            setattr(t, "is_deleted", True)
            t.save(update_fields=["is_deleted"])
        else:
            t.delete()
        n += 1
    messages.warning(request, f"{n}건 콘텐츠 삭제 처리.")

@admin.action(description="작성자 1일 뮤트(작성 금지)")
def mute_owner_1d(modeladmin, request, queryset):
    n = 0
    until = timezone.now() + timedelta(days=1)
    for r in queryset:
        u = _owner_of_report(r)
        if not u: 
            continue
        d = ensure_discipline(u)
        d.muted_until = until
        d.save(update_fields=["muted_until"])
        n += 1
    messages.info(request, f"{n}명 1일 뮤트 적용.")

@admin.action(description="작성자 7일 정지")
def suspend_owner_7d(modeladmin, request, queryset):
    n = 0
    until = timezone.now() + timedelta(days=7)
    for r in queryset:
        u = _owner_of_report(r)
        if not u: 
            continue
        d = ensure_discipline(u)
        d.suspended_until = until
        d.save(update_fields=["suspended_until"])
        n += 1
    messages.info(request, f"{n}명 7일 정지 적용.")

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """
    신고 리스트에서 바로 '대상 보기(사이트)' / '방 열기(사이트)' / '미리보기'를 제공
    + 제재 액션까지 모두 수행 가능
    """
    list_display = (
        "id", "status", "reason",
        "target_link",      # Admin 대상 편집 링크
        "target_preview",   # ✅ 내용 미리보기
        "site_link",        # ✅ 대상 페이지(프런트)로 이동
        "room_link",        # ✅ 방으로 이동
        "owner",
        "created_at",
    )
    list_filter = ("status", "reason", "content_type")
    search_fields = ("detail", "reported_by__email", "reported_by__username")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    actions = [
        accept_and_warn,
        mark_rejected,
        delete_targets,
        mute_owner_1d,        # 작성자 1일 뮤트
        suspend_owner_7d,     # 작성자 7일 정지
    ]

    # --- 컬럼 렌더링 ---

    def target_link(self, obj: Report):
        url = _admin_url_for_report(obj)
        label = f"{obj.content_type.model}#{obj.object_id}"
        return format_html('<a href="{}">{}</a>', url, label) if url else label
    target_link.short_description = "대상(Admin)"

    def target_preview(self, obj: Report):
        return _preview_of_target(obj, length=80)
    target_preview.short_description = "미리보기"

    def site_link(self, obj: Report):
        t = getattr(obj, "target", None)
        url = _front_url_for_target(t)
        if url:
            return format_html('<a href="{}" target="_blank">보기</a>', url)
        return "-"
    site_link.short_description = "대상(사이트)"

    def room_link(self, obj: Report):
        t = getattr(obj, "target", None)
        url = _front_room_url_for_target(t)
        if url:
            return format_html('<a href="{}" target="_blank">방 열기</a>', url)
        return "-"
    room_link.short_description = "방(사이트)"

    def owner(self, obj: Report):
        u = _owner_of_report(obj)
        if not u:
            return "-"
        for attr in ("nickname", "email", "username"):
            if hasattr(u, attr):
                return getattr(u, attr) or str(u)
        return str(u)


# --------------------- UserDiscipline Admin (그대로) ---------------------

@admin.action(description="선택 사용자 뮤트 해제")
def unmute_selected(modeladmin, request, queryset):
    n = 0
    for d in queryset:
        if d.muted_until:
            d.muted_until = None
            d.save(update_fields=["muted_until"])
            n += 1
    messages.success(request, f"{n}명 뮤트 해제.")

@admin.action(description="선택 사용자 정지 해제")
def unsuspend_selected(modeladmin, request, queryset):
    n = 0
    for d in queryset:
        if d.suspended_until:
            d.suspended_until = None
            d.save(update_fields=["suspended_until"])
            n += 1
    messages.success(request, f"{n}명 정지 해제.")

@admin.action(description="선택 사용자 계정 재활성화")
def reactivate_selected(modeladmin, request, queryset):
    n = 0
    for d in queryset:
        if d.banned_at or not d.user.is_active:
            d.banned_at = None
            d.save(update_fields=["banned_at"])
            d.user.is_active = True
            d.user.save(update_fields=["is_active"])
            n += 1
    messages.success(request, f"{n}명 계정 재활성화.")

@admin.action(description="선택 사용자 경고 0으로 초기화")
def reset_warnings(modeladmin, request, queryset):
    n = queryset.update(warnings=0)
    messages.info(request, f"{n}명 경고 초기화.")

@admin.register(UserDiscipline)
class UserDisciplineAdmin(admin.ModelAdmin):
    list_display = ("user", "active_status", "warnings", "muted_until", "suspended_until", "banned_at")
    search_fields = ("user__email", "user__username", "user__nickname")
    actions = [unmute_selected, unsuspend_selected, reactivate_selected, reset_warnings]
    ordering = ("-muted_until", "-suspended_until", "-banned_at")

    def active_status(self, obj: UserDiscipline):
        now = timezone.now()
        if obj.banned_at:
            return "banned"
        if obj.suspended_until and obj.suspended_until > now:
            return "suspended"
        if obj.muted_until and obj.muted_until > now:
            return "muted"
        return "ok"
    active_status.short_description = "상태"
