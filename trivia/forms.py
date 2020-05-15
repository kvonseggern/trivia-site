from django.forms import ModelForm

from .models import FinalResponse


class FinalResponseForm(ModelForm):
    class Meta:
        model = FinalResponse
        fields = [
            'final_round',
            'player'
        ]
