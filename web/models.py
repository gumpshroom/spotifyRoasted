from django.db import models

# Create your models here.
class User(models.Model):
    spotify_id = models.TextField()
    access_token = models.TextField()
    #'wraps' will be stored as JSON, browser will be a 'wrap' object "player"
    wraps = models.JSONField(default=dict)