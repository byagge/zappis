from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Business
from apps.website.models import Website
 
@receiver(post_save, sender=Business)
def create_website_for_business(sender, instance, created, **kwargs):
    if created:
        Website.objects.get_or_create(business=instance) 