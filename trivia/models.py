from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.urls import reverse

# Create your models here.

class Game(models.Model):
    player = models.ManyToManyField(settings.AUTH_USER_MODEL)
    game_title = models.CharField(max_length=100)
    pub_date = models.DateTimeField('date published')
    completed = models.BooleanField(default=False)

    class Meta:
        ordering = ('-pub_date',)

    def __str__(self):
        return self.game_title

    def round_status_sum(self):
        return sum([int(x.status) for x in self.round_set.all()])
    
    def score_rounds(self):
        # score the rounds (separated out for final wager clarity)
        dict = {}
        for player in self.player.all():
            dict[player] = {}
            for round in self.round_set.all():
                score = round.score_round()
                dict[player].update(score[player])
            dict[player].update({'total': sum(dict[player].values())})
        return dict

    def score_game(self):
        # total game score
        dict = self.score_rounds()
        for player in self.player.all():
            # delete the old total score for each player from score_rounds()
            del dict[player]['total']
            for round in self.finalround_set.all():
                dict[player].update(round.score_finalround()[player])
            dict[player].update({'total': sum(dict[player].values())})
        return dict


class BaseRound(models.Model):
    STATUS_CHOICES = [
        ('0', 'Not Open'),
        ('1', 'Answer Time'),
        ('2', 'Check Answers'),
        ('3', 'Closed'),
    ]
    category = models.CharField(max_length=100)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=0)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)

    def __str__(self):
        return self.category

    def get_absolute_url(self):
        return reverse('trivia:game_detail', kwargs={'pk': self.game_id})

    class Meta:
        abstract = True


class BaseQuestion(models.Model):
    question = models.CharField(max_length=250)
    answer = models.CharField(max_length=150)
    alt_answers = models.CharField(max_length=500, null=True)
    points = models.IntegerField(default=2)

    def __str__(self):
        return self.question

    def answer_set(self):
        if self.alt_answers == None:
            return [self.answer.strip().lower()]
        else:
            alts = [x.strip().lower() for x in self.alt_answers.split(',')]
            return [self.answer.strip().lower()] + alts

    class Meta:
        abstract = True


class BaseResponse(models.Model):
    correct = models.BooleanField(default=False)
    response = models.CharField(max_length=150)
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.response

    class Meta:
        abstract = True


class Round(BaseRound):
    def score_round(self):
        dict = {}
        for player in self.game.player.all():
            score = 0
            for question in self.question_set.filter(round=self):
                for response in question.response_set.filter(player=player):
                    score += response.score_response()
            dict[player] = {self: score}
        return dict

    def check_round(self):
        for question in self.question_set.all():
            for response in question.response_set.all():
                response.check_response()

    def save(self, *args, **kwargs):
        if self.status == '2':
            self.check_round()
        super().save(*args, **kwargs) 


class FinalRound(BaseRound, BaseQuestion):
    STATUS_CHOICES = [
        ('0', 'Not Open'),
        ('1', 'Wager'),
        ('2', 'Answer Time'),
        ('3', 'Check Answers'),
        ('4', 'Closed'),
    ]
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=0)
    points = models.IntegerField(default=0)

    def score_finalround(self):
        dict = {}
        for player in self.game.player.all():
            if self.status != '4':
                dict[player] = {self: 0}
            else:
                try:
                    final_response = FinalResponse.objects.get(player=player, final_round__game=self.game)   
                    if final_response.correct:
                        dict[player] = {self: final_response.wager}
                    else:
                        dict[player] = {self: -final_response.wager}
                except FinalResponse.DoesNotExist:
                    dict[player] = {self: 0}
        return dict

    class Meta:
        constraints = [models.UniqueConstraint(fields=['game'], name='one_final_round')]


class Question(BaseQuestion):
    round = models.ForeignKey(Round, on_delete=models.CASCADE)


class Response(BaseResponse):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    def get_absolute_url(self):
        return reverse('trivia:round_detail', kwargs={'pk': self.question.round_id})

    def check_response(self):
        if self.response.strip() in self.question.answer_set():
            self.correct = True
            self.save()

    def score_response(self):
        if self.correct:
            try:
                double_round = self.question.round.doubleround_set.get(player=self.player)
                multiplier = double_round.multiplier
                score = self.question.points * multiplier
            except DoubleRound.DoesNotExist:
                score = self.question.points
            return score
        else:
            return 0

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['player', 'question'], name='unique_answer')
        ]


class FinalResponse(BaseResponse):
    wager = models.IntegerField(default=None, null=True)
    final_round = models.ForeignKey(FinalRound, on_delete=models.CASCADE)

    def clean(self):
        max_wager = self.final_round.points
        game = self.final_round.game
        score = game.score_rounds()[self.player]['total']
        if max_wager > 0 and self.wager > max_wager:
            raise ValidationError(f'Above max wager. Max wager is {max_wager}.')
        elif max_wager == 0 and self.wager > score:
            raise ValidationError(f'Your max wager is your score. You have {score}.')

    def get_absolute_url(self):
        return reverse('trivia:game_detail', kwargs={'pk': self.final_round.game.id})

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['final_round', 'player'], name='one_final_answer')
        ]


class DoubleRound(models.Model):
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    round = models.ForeignKey(Round, on_delete=models.CASCADE, null=True)
    multiplier = models.IntegerField(default=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['player', 'game'], name='unique_double_round')
        ]

    def __str__(self):
        return self.round

    def get_absolute_url(self):
        return reverse('trivia:game_detail', kwargs={'pk': self.game_id})
