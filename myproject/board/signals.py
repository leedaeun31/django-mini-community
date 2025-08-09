from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import PostImage

@receiver(post_delete, sender=PostImage)
def delete_file_on_postimage_delete(sender, instance, **kwargs):
    # PostImage가 삭제되면 실제 파일도 스토리지에서 삭제
    if instance.image:
        instance.image.delete(save=False)

@receiver(pre_save, sender=PostImage)
def delete_old_file_on_change(sender, instance, **kwargs):
    # 이미지 교체 시 예전 파일 삭제
    if not instance.pk:
        return
    try:
        old = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return
    if old.image and old.image != instance.image:
        old.image.delete(save=False)
