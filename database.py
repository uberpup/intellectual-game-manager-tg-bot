import os
from peewee import *
from playhouse.postgres_ext import PostgresqlExtDatabase


class DatabaseVariables:
    current_number_of_questions = 0
    current_game_number = 0


NAME = os.getenv("NAME")
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
HOST = os.getenv("HOST")
db = PostgresqlExtDatabase(NAME, user=USER, password=PASSWORD,
                           host=HOST, register_hstore=True)


class BaseExtModel(Model):
    class Meta:
        database = db


class GameInfo(BaseExtModel):
    game_id = BigIntegerField(null=False)
    game_starter = BigIntegerField(null=False)
    id = BigIntegerField(null=False)
    team_name = TextField()
    points = IntegerField(default=0)

    class Meta:
        db_table = "game_info"
        order_by = ("points", )


class QuestionBase(BaseExtModel):
    game_id = BigIntegerField(null=False)
    question_number = IntegerField(default=0)
    question = TextField()
    answer = TextField()

    class Meta:
        db_table = "question_base"
        order_by = ("question_number", )


DBVariables = DatabaseVariables()
db.connect()
db.create_tables([GameInfo, QuestionBase])


def start_game(admin_id):
    row = GameInfo(game_id=DBVariables.current_game_number, game_starter=admin_id)
    DBVariables.current_game_number += 1
    row.save()
    return DBVariables.current_game_number - 1


def get_game_id(mode, id):
    if mode:
        row = GameInfo.get(game_starter=id)
    else:
        row = GameInfo.get(id=id)
    return row.game_id


def insert_player(user_id, team_name, current_game_id):
    row = GameInfo.get(game_id=current_game_id)
    row.id = user_id
    row.team_name = team_name
    row.save()


def increase_points(user_id, current_game_id):
    row = GameInfo.get(game_id = current_game_id, id=user_id)
    row.points = row.points + 1
    row.save()


def set_question(question_text, current_game_id):
    row = QuestionBase.get(game_id = current_game_id)
    row.question = question_text
    row.question_number = DBVariables.current_number_of_questions
    row.save()


def set_answer(answer_text, question_id, current_game_id):
    row = QuestionBase.get(game_id=current_game_id, question_number=question_id)
    row.answer = answer_text
    row.save()


def check_answer(answer_text, question_id, current_game_id):
    row = QuestionBase.get(game_id=current_game_id, question_number=question_id)
    correct_answer = row.answer
    return True if correct_answer == answer_text else False


def get_question(question_id, current_game_id):
    row = QuestionBase.get(game_id=current_game_id, question_number=question_id)
    current_question = row.question
    return current_question


def get_team_name(user_id, current_game_id):
    row = GameInfo.get(game_id=current_game_id, id=user_id)
    current_team_name = row.team_name
    return current_team_name


def get_points(user_id, current_game_id):
    row = GameInfo.get(game_id=current_game_id, id=user_id)
    current_points = row.points
    return current_points


def get_standings(current_game_id):
    rating = GameInfo.select().where(game_id=current_game_id)
    return rating.team_name, rating.points


def end_game(current_game_id):
    game_table_piece = GameInfo(game_id=current_game_id)
    question_base_table_piece = QuestionBase(game_id=current_game_id)
    game_table_piece.delete_instance()
    question_base_table_piece.delete_instance()
    game_table_piece.save()
    question_base_table_piece.save()
