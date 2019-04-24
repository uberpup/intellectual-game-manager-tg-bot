import sqlite3


class DatabaseVariables:
    current_number_of_questions = 0


conn = sqlite3.connect("game_base.db")
DBV = DatabaseVariables()
c = conn.cursor()

c.execute("""CREATE TABLE game_info(
            id integer,
            team_name text,
            points integer
            )
    """)

c.execute("""CREATE TABLE question_base(
            question_number integer,
            question text,
            answer text
            )
    """)


def insert_player(user_id):
    with conn:
        c.execute("INSERT INTO game_info VALUES (?, ?)", (user_id, 0))


def increase_points(user_id):
    with conn:
        c.execute("SELECT points FROM game_table WHERE id = (?)", (user_id, ))
        points = c.fetchone()
        c.execute("""UPDATE game_info SET points = (?) WHERE id = (?)""", (points + 1, user_id))


def set_question(question_text, answer_text):
    with conn:
        c.execute("INSERT INTO question_base VALUES (?, ?)", (DBV.current_number_of_questions, question_text))
        DBV.current_number_of_questions += 1


def set_answer(answer_text, question_id):
    with conn:
        c.execute("UPDATE question_base SET answer = (?) WHERE question_number = (?)", (answer_text, question_id))


def check_answer(answer_text, question_id):
    with conn:
        c.execute("SELECT answer FROM question_base WHERE question_number = (?)", (question_id, ))
        correct_answer = c.fetchone()
    return True if correct_answer == answer_text else False


def get_question(question_id):
    with conn:
        c.execute("SELECT question FROM question_base WHERE question_number = (?)", (question_id, ))
        current_question = c.fetchone()
    return current_question


def get_standings():
    with conn:
        c.execute("SELECT points FROM game_table ORDER BY points, id")
        rating = c.fetchall()
    return rating


conn.commit()
conn.close()
