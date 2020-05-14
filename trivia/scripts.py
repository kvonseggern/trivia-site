import csv
import os
from django.utils import timezone

from trivia.models import Game, Round, FinalRound, Question

def import_game(file_path, game_name=None):
    if game_name:
        name = game_name
    else:
        name = os.path.basename(file_path)
    new_game = Game(game_title=name, pub_date=timezone.now())
    new_game.save()
    with open(file_path) as f:
        csv_file = csv.reader(f)
        round_dict = {}
        for row in csv_file:
            if row[0].lower() == 'final round':
                fr = FinalRound(category=row[1], game=new_game, question=row[2], answer=row[3])
                fr.save()
            else:
                if row[0] not in round_dict.keys():
                    r = Round(category=row[0], game=new_game)
                    r.save()
                    round_dict[row[0]] = r
                q = Question(round=round_dict[row[0]], question=row[1], answer=row[2])
                q.save()
