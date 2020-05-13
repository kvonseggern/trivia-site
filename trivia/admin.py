from django.contrib import admin

from .models import DoubleRound, FinalAnswer, Game, Round, Question, QuestionResponse, FinalRound

# Register your models here.

admin.site.register([Game, Round, Question, QuestionResponse, DoubleRound, FinalRound, FinalAnswer])
