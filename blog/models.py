from django.db import models

# Create your models here.

from django.conf import settings
from django.db import models
from django.utils import timezone

CHOICES = (
    ("0", "1,000"),
    ("2", "2,000"),
    ("3", "3,000"),
    ("4", "4,000"),
)


class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    text = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)
    published_date = models.DateTimeField(blank=True, null=True)
    pulldown = models.CharField(max_length=100,verbose_name="no",choices=CHOICES,null="",default="")

    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.title
