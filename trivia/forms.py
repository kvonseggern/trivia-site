from django.forms import ModelForm

from .models import FinalAnswer


class FinalAnswerForm(ModelForm):
    class Meta:
        model = FinalAnswer
        fields = [
            'finalround',
            'player'
        ]
