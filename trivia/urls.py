from trivia.views import DoubleRoundUpdate, FinalAnswerUpdate, FinalRoundStatusUpdate, FinalRoundWagerUpdate, manage_finalanswers
from django.urls import path

from . import views

app_name = 'trivia'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('games/', views.GameIndexView.as_view(), name='games'),
    path('games/<int:pk>/', views.GameDetailView.as_view(), name='game_detail'),
    path('games/round/<int:pk>/', views.RoundDetailView.as_view(), name='round_detail'),
    path('games/round/<int:pk>/status/', views.RoundStatusUpdate.as_view(), name='round_update'),
    path('games/<int:game>/answer/<int:round>/<int:question>/', views.ResponseCreate.as_view(), name='new_answer'),
    path('games/answer/update/<int:pk>/', views.ResponseUpdate.as_view(), name='update_answer'),
    path('games/<int:game>/wager/', views.finalwager, name='final_wager'),
    path('games/wager/<int:pk>/update/', views.FinalRoundWagerUpdate.as_view(), name='final_wager_update'),
    path('games/<int:game>/final/', views.finalanswer, name='final_answer'),
    path('games/final/<int:pk>/update/', views.FinalAnswerUpdate.as_view(), name='final_answer_update'),
    path('games/<int:game>/final/check/', views.manage_finalanswers, name='check_finalanswer'),
    path('games/<int:game>/check/<int:round>/<int:player>/', views.check_answers, name='check_answers'),
    path('games/finalroundstatus/<int:pk>/', views.FinalRoundStatusUpdate.as_view(), name='finalround_update'),
    path('games/review/<int:pk>/', views.RoundReviewDetail.as_view(), name='round_review'),
    path('games/double/<int:game>/', views.DoubleRoundCreate.as_view(), name='double_round'),
    path('games/double/<int:pk>/update/', views.DoubleRoundUpdate.as_view(), name='double_update'),
    path('manage/', views.ManageView.as_view(), name='manage'),
    path('manage/round/new/', views.RoundCreate.as_view(), name='new_round'),
    path('manage/round/<int:round_pk>/', views.manage_questions, name='manage_questions'),
    path('signup/', views.signup, name='signup'),
]
