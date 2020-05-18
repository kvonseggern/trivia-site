from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from trivia.models import Game, Round, DoubleRound, Question
from django.contrib.auth.models import User

# Create your tests here.


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='jacob', email='jacob@…', password='top_secret'
        )
        self.client.login(username='jacob', password='top_secret')
        self.game = Game.objects.create(game_title='Test Game 1', pub_date=timezone.now())
        self.round = Round.objects.create(category='Test Round 1', game=self.game)
        self.question = Question.objects.create(question='Test q?', answer='Ans', round=self.round)
        self.double_round = DoubleRound.objects.create(player=self.user, game=self.game, round=self.round)
        self.game2 = Game.objects.create(game_title='Test Game 2', pub_date=timezone.now())

    def test_index_view(self):
        response = self.client.get(reverse('trivia:index'))
        self.assertEqual(response.status_code, 200)

    def test_game_index(self):
        response = self.client.get(reverse('trivia:games'))
        self.assertEqual(response.status_code, 200)

    def test_game_detail(self):
        response = self.client.get(reverse('trivia:game_detail', args=(self.game2.id,)))
        self.assertEqual(response.status_code, 200)

    def test_round_detail(self):
        response = self.client.get(reverse('trivia:round_detail', args=(self.round.id,)))
        self.assertEqual(response.status_code, 200)

    def test_round_status_update_get(self):
        response = self.client.get(reverse('trivia:round_update', args=(self.round.id,)))
        # regular user should get 403
        self.assertEqual(response.status_code, 403)

    def test_round_status_update_post(self):
        response = self.client.post(reverse('trivia:round_update', args=(self.round.id,)))
        # regular user should get 403
        self.assertEqual(response.status_code, 403)

    def test_create_response(self):
        # this currently fails
        response = self.client.get(reverse('trivia:new_answer', kwargs={
            'game': self.game.id,
            'round': self.round.id,
            'question': self.question.id
        }))
        self.assertEqual(response.status_code, 200)

    def test_response_post(self):
        # this currently fails
        response = self.client.post(reverse('trivia:new_answer', kwargs={
            'game': self.game.id,
            'round': self.round.id,
            'question': self.question.id
        }))
        self.assertRedirects(response, self.round.get_absolute_url(), 200)

    def test_final_wager_get(self):
        response = self.client.post(reverse('trivia:final_wager', kwargs={'game': 1}))
        self.assertRedirects(response, )


    def test_doubleround_create_view(self):
        response = self.client.get(reverse('trivia:double_round', args=(self.game2.id,)))
        self.assertEqual(response.status_code, 200)

    def test_doubleround_create_post(self):
        response = self.client.post(reverse('trivia:double_round', args=(self.game.id,)))
        self.assertEqual(response.status_code, 200)

    def test_doubleround_redirect(self):
        response = self.client.get(reverse('trivia:double_round', args=(self.game.id,)))
        round = DoubleRound.objects.get(player=self.user, game=self.game)
        self.assertRedirects(response, reverse('trivia:double_update', args=(round.id,)))

    def test_doubleround_update_post(self):
        response = self.client.post(reverse('trivia:double_update', args=(self.game.id,)))
        self.assertEqual(response.status_code, 200)
