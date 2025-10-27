from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group
from .apps import UsersConfig


@receiver(post_migrate, sender=UsersConfig)
def create_groups(sender, **kwargs):
    """
    Create default user groups after migrations.
    """
    # Создаёт группы арендодателей и арендаторов после миграций
    Group.objects.get_or_create(name='Landlords')
    Group.objects.get_or_create(name='Tenants')