from django.forms import ModelForm

from .models import DoubleRound, FinalResponse, Response


class ResponseForm(ModelForm):
    class Meta:
        model = Response
        fields = ['response']


class FinalResponseForm(ModelForm):
    class Meta:
        model = FinalResponse
        fields = [
            'final_round',
            'player'
        ]
