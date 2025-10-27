from django.db import models
from django.utils.translation import gettext_lazy as _


class ActiveManager(models.Manager):
    """
    Manager that returns only non-deleted (active) instances.
    """
    # Менеджер, возвращающий только неудалённые (активные) объекты
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class BaseModel(models.Model):
    """
    Abstract base model with soft-delete and timestamps.

    Provides:
    - created_at / updated_at auto timestamps,
    - is_deleted flag for soft deletion,
    - ActiveManager as default (excludes deleted),
    - all_objects manager to access all records.
    """
    # Абстрактная базовая модель с мягким удалением и временными метками

    created_at = models.DateTimeField(
        _('Created at'),  # Дата создания
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('Updated at'),  # Дата обновления
        auto_now=True
    )
    is_deleted = models.BooleanField(
        _('Soft deleted'),  # Мягко удалено
        default=False
    )

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def delete(self, *args, **kwargs):
        """
        Performs soft delete by setting is_deleted=True instead of removing from DB.
        """
        # Выполняет мягкое удаление: устанавливает is_deleted=True вместо физического удаления
        self.is_deleted = True
        self.save(update_fields=['is_deleted'])