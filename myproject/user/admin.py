# user/admin.py
# -----------------------------------------------------------------------------
# Users(사용자) 목록에서 바로 경고/뮤트/정지/해제/재활성화/경고초기화 실행
# -----------------------------------------------------------------------------

from datetime import timedelta

from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone

from moderation.models import ensure_discipline, add_warning

User = get_user_model()


@admin.action(description="경고 1회 부여(누적 규칙 적용)")
def action_give_warning(modeladmin, request, queryset):
    n = 0
    for u in queryset:
        add_warning(u, note="admin_action")
        n += 1
    messages.success(request, f"{n}명 경고 1회 부여.")


@admin.action(description="1일 뮤트")
def action_mute_1d(modeladmin, request, queryset):
    n = 0
    until = timezone.now() + timedelta(days=1)
    for u in queryset:
        d = ensure_discipline(u)
        d.muted_until = until
        d.save(update_fields=["muted_until"])
        n += 1
    messages.info(request, f"{n}명 1일 뮤트 적용.")


@admin.action(description="7일 정지")
def action_suspend_7d(modeladmin, request, queryset):
    n = 0
    until = timezone.now() + timedelta(days=7)
    for u in queryset:
        d = ensure_discipline(u)
        d.suspended_until = until
        d.save(update_fields=["suspended_until"])
        n += 1
    messages.info(request, f"{n}명 7일 정지 적용.")


@admin.action(description="뮤트 해제")
def action_unmute(modeladmin, request, queryset):
    n = 0
    for u in queryset:
        d = ensure_discipline(u)
        if d.muted_until:
            d.muted_until = None
            d.save(update_fields=["muted_until"])
            n += 1
    messages.success(request, f"{n}명 뮤트 해제.")


@admin.action(description="정지 해제")
def action_unsuspend(modeladmin, request, queryset):
    n = 0
    for u in queryset:
        d = ensure_discipline(u)
        if d.suspended_until:
            d.suspended_until = None
            d.save(update_fields=["suspended_until"])
            n += 1
    messages.success(request, f"{n}명 정지 해제.")


@admin.action(description="계정 재활성화(비활성 해제)")
def action_reactivate(modeladmin, request, queryset):
    n = 0
    for u in queryset:
        d = ensure_discipline(u)
        if d.banned_at or not u.is_active:
            d.banned_at = None
            d.save(update_fields=["banned_at"])
            u.is_active = True
            u.save(update_fields=["is_active"])
            n += 1
    messages.success(request, f"{n}명 계정 재활성화.")


@admin.action(description="경고 0으로 초기화")
def action_reset_warnings(modeladmin, request, queryset):
    n = 0
    for u in queryset:
        d = ensure_discipline(u)
        if d.warnings:
            d.warnings = 0
            d.save(update_fields=["warnings"])
            n += 1
    messages.info(request, f"{n}명 경고 초기화.")


class ModerationUserAdmin(BaseUserAdmin):
    """기본 UserAdmin 확장: 제재 현황 컬럼 + 액션 추가"""
    list_display = (
        *BaseUserAdmin.list_display,
        "m_warnings", "m_muted_until", "m_suspended_until", "m_status",
    )
    actions = [
        action_give_warning, action_mute_1d, action_suspend_7d,
        action_unmute, action_unsuspend, action_reactivate, action_reset_warnings,
    ]

    def _disc(self, obj):
        return ensure_discipline(obj)

    def m_warnings(self, obj):
        return self._disc(obj).warnings
    m_warnings.short_description = "경고"

    def m_muted_until(self, obj):
        return self._disc(obj).muted_until
    m_muted_until.short_description = "뮤트_until"

    def m_suspended_until(self, obj):
        return self._disc(obj).suspended_until
    m_suspended_until.short_description = "정지_until"

    def m_status(self, obj):
        d = self._disc(obj)
        now = timezone.now()
        if d.banned_at:
            return "banned"
        if d.suspended_until and d.suspended_until > now:
            return "suspended"
        if d.muted_until and d.muted_until > now:
            return "muted"
        return "ok"
    m_status.short_description = "제재상태"


# 기본 UserAdmin 교체 등록
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, ModerationUserAdmin)
