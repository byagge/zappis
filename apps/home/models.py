from django.db import models
from wagtail.models import Page
from wagtail.fields import StreamField
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from wagtail.admin.panels import FieldPanel


class HomePage(Page):
    body = StreamField([
        ('heading', blocks.CharBlock(form_classname="title")),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
        ('online_booking', blocks.StructBlock([
            ('title', blocks.CharBlock(required=True)),
            ('description', blocks.RichTextBlock(required=True)),
            ('image', ImageChooserBlock(required=True)),
        ], icon='form')),
    ], use_json_field=True, null=True, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('body'),
    ]
