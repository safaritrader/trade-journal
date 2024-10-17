import os
from django.db import models
from django.contrib.auth.models import User


# Todo : add name for each journal
# Todo : add view permission for other users

class JournalEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    trade_date = models.DateTimeField()
    journal_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    profit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0.00)
    symbol = models.CharField(max_length=10, null=True, blank=True, default='')
    size = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=0.00)

    def __str__(self):
        return f"Journal Entry by {self.user.username} on {self.trade_date}"

    class Meta:
        verbose_name_plural = "Journal Entries"


class JournalEntryImage(models.Model):
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='journal_images/')

    def delete(self, *args, **kwargs):
        # First delete the file from the filesystem
        print(self.image.path)
        if self.image and os.path.isfile(self.image.path):
            os.remove(self.image.path)
        # Then delete the instance from the database
        super(JournalEntryImage, self).delete(*args, **kwargs)

    def __str__(self):
        return f"Image for {self.journal_entry.user.username}'s entry on {self.journal_entry.trade_date}"
