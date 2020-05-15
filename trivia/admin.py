from django.contrib import admin

from .models import DoubleRound, FinalResponse, Game, Round, Question, Response, FinalRound

# Register your models here.

admin.site.register([Game, Round, Question, Response, DoubleRound, FinalRound, FinalResponse])
