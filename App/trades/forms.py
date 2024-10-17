from django import forms
from django.forms.models import inlineformset_factory
from .models import JournalEntry, JournalEntryImage


class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = ['trade_date', 'journal_text', 'profit', 'symbol', 'size']


# Create a formset for handling multiple images
JournalEntryImageFormSet = inlineformset_factory(
    JournalEntry,
    JournalEntryImage,
    fields=('image',),
    extra=3,  # Number of extra image fields to display
    can_delete=True
)
