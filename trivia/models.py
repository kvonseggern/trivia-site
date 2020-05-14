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


class Round(models.Model):
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

    def score_round(self):
        dict = {}
        for player in self.game.player.all():
            correct = QuestionResponse.objects.filter(player=player, question__round=self, correct=True)
            score = correct.aggregate(Sum('question__points'))['question__points__sum'] or 0
            try:
                double_round = DoubleRound.objects.get(round=self, player=player)
                if self == double_round.round:
                    score *= double_round.multiplier
            except DoubleRound.DoesNotExist:
                pass
            dict[player] = {self: score}
        return dict


class FinalRound(models.Model):
    STATUS_CHOICES = [
        ('0', 'Not Open'),
        ('1', 'Wager'),
        ('2', 'Answer Time'),
        ('3', 'Check Answers'),
        ('4', 'Closed'),
    ]
    category = models.CharField(max_length=100)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=0)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    question = models.CharField(max_length=250)
    answer = models.CharField(max_length=250)
    alt_answers = models.CharField(max_length=500, null=True)
    max_wager = models.IntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['game'], name='one_final_round')]

    def __str__(self):
        return self.category

    def get_absolute_url(self):
        return reverse('trivia:game_detail', kwargs={'pk': self.game_id})

    def score_finalround(self):
        dict = {}
        for player in self.game.player.all():
            if self.status != '4':
                dict[player] = {self: 0}
            else:
                try:
                    final_answer = FinalAnswer.objects.get(player=player, finalround__game=self.game)   
                    if final_answer.correct:
                        dict[player] = {self: final_answer.wager}
                    else:
                        dict[player] = {self: -final_answer.wager}
                except FinalAnswer.DoesNotExist:
                    dict[player] = {self: 0}
        return dict


class Question(models.Model):
    question = models.CharField(max_length=250)
    answer = models.CharField(max_length=150)
    alt_answers = models.CharField(max_length=500, null=True)
    points = models.IntegerField(default=2)
    round = models.ForeignKey(Round, on_delete=models.CASCADE)

    def __str__(self):
        return self.question

    def answer_set(self):
        if self.alt_answers == None:
            return [self.answer.strip()]
        else:
            return [self.answer.strip()] + [x.strip() for x in self.alt_answers.split(',')]


class QuestionResponse(models.Model):
    correct = models.BooleanField(default=False)
    response = models.CharField(max_length=150)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['player', 'question'], name='unique_answer')
        ]

    def __str__(self):
        return self.response

    def get_absolute_url(self):
        return reverse('trivia:round_detail', kwargs={'pk': self.question.round_id})


class FinalAnswer(models.Model):
    finalround = models.ForeignKey(FinalRound, on_delete=models.CASCADE)
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    wager = models.IntegerField(default=0)
    answer = models.CharField(max_length=200, null=True)
    correct = models.BooleanField(default=False)

    def get_absolute_url(self):
        return reverse('trivia:game_detail', kwargs={'pk': self.finalround.game.id})

    def clean(self):
        max_wager = self.finalround.max_wager
        game = self.finalround.game
        score = game.score_rounds()[self.player]['total']
        if max_wager > 0 and self.wager > max_wager:
            raise ValidationError(f'Above max wager. Max wager is {max_wager}.')
        elif max_wager == 0 and self.wager > score:
            raise ValidationError(f'Your max wager is your score. You have {score}.')

    def save(self, *args, **kwargs):
        '''
        if self.finalround.status != ('1' or '2'):
            return PermissionDenied("The round status doesn't allow that.")
        else:
        '''
        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['finalround', 'player'], name='one_final_answer')
        ]

class DoubleRound(models.Model):
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    multiplier = models.IntegerField(default=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['player', 'game'], name='unique_double_round')
        ]

    def __str__(self):
        return f'{self.player}: {self.game}, {self.round}'

    def get_absolute_url(self):
        return reverse('trivia:game_detail', kwargs={'pk': self.game_id})
        