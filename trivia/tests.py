from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from trivia.models import Game, Round, DoubleRound
from django.contrib.auth.models import User

# Create your tests here.


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='jacob', email='jacob@…', password='top_secret')
        self.client.force_login(self.user)
        self.game = Game.objects.create(game_title='Test Game 1', pub_date=timezone.now())
        self.round = Round.objects.create(category='Test Round 1', game=self.game)
        self.double_round = DoubleRound.objects.create(player=self.user, game=self.game, round=self.round)
        self.game2 = Game.objects.create(game_title='Test Game 2', pub_date=timezone.now())

    def test_create_view(self):
        response = self.client.get(reverse('trivia:double_round', args=(self.game2.id,)))
        self.assertEqual(response.status_code, 200)

    def test_create_post(self):
        response = self.client.post(reverse('trivia:double_round', args=(self.game.id,)))
        self.assertEqual(response.status_code, 200)

    def test_redirect(self):
        response = self.client.get(reverse('trivia:double_round', args=(self.game.id,)))
        round = DoubleRound.objects.get(player=self.user, game=self.game)
        self.assertRedirects(response, reverse('trivia:double_update', args=(round.id,)))

    def test_update_post(self):
        response = self.client.post(reverse('trivia:double_update', args=(self.game.id,)))
        self.assertEqual(response.status_code, 200)
