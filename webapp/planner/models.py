from django.db import models

# Create your models here.
class Plate(models.Model):
    pos = models.CharField(max_length=3, primary_key=True)
    sample = models.CharField(max_length=100, blank=True)
    primers = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.pos