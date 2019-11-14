import logging
import os
import sys
import telegram.ext
import time
import database


class MainVariables:
    game_started = False  # Will be changed after database added
    start_time = 0.0
    answering_time = 60.0
    current_question_id = 0
# Enabling logging


logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

# Setting game_state, so we could define run function for both local and Heroku setup
game_state = os.getenv("GAMESTATE")
TOKEN = os.getenv("TOKEN")
MVariables = MainVariables()


if game_state == "dev":
    def run(updater):
        updater.start_polling()
elif game_state == "prod":
    def run(updater):
        PORT = int(os.environ.get("PORT", "8443"))
        HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME")
        updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path=TOKEN)
        updater.bot.set_webhook("https://{}.herokuapp.com/{}".format(HEROKU_APP_NAME, TOKEN))
else:
    logger.error("No MODE specified!")
    sys.exit(1)


def start_handler(bot, update):  # Handler-function for /start command
    logger.info("User {} started bot".format(update.effective_user["id"]))
    update.message.reply_text("Hello!\n/startgame, /register your team or seek for /help")


def start_game_handler(bot, update):  # Handler-function for /startgame command
    if not (update.effective_user["id"] in admins):
        logger.info("User {} tried to use inaccessible command {}".format(update.effective_user["id"],
                                                                          start_game_handler))
        update.message.reply_text("Oops, you don't have rights to access this command")
    else:
        game_id = database.start_game(update.effective_user["id"])
        logger.info("User {} started game {}".format(update.effective_user["id"], game_id))
        update.message.reply_text("Game {} started\nYou can /setquestion and /setanswer now".format(game_id))
        MVariables.game_started = True  # !!!


def end_game_handler(bot, update, args):  # /endgame
    if not (update.effective_user["id"] in admins):
        logger.info("User {} tried to use inaccessible command {}".format(update.effective_user["id"],
                                                                          end_game_handler))
        update.message.reply_text("Oops, you don't have rights to access this command")
    else:
        parameter = "".join(args)
        if parameter != "":
            if parameter == "sure":
                game_id = database.get_game_id(False, update.effective_user["id"])
                logger.info("User {} finished game {}".format(update.effective_user["id"], game_id))
                standings_handler(bot, update)  # showing results
                update.message.reply_text("Game {} finished".format(game_id))
                MVariables.game_started = False  # !!!
                database.end_game(game_id)
            else:
                update.message.reply_text("Type 'sure' after /endgame if you are ready to finish the game")
                logger.info("User {} tried to endgame but with wrong args".format(update.effective_user["id"]))
        else:
            update.message.reply_text("Type 'sure' after /end_game if you are ready to finish the game")
            logger.info("User {} tried to endgame but without args".format(update.effective_user["id"]))


def set_answering_time(bot, update, args):  # /setansweringtime; specify the time in seconds
    if len(args) > 0:
        MVariables.answering_time = float(args[0])
        logger.info("User {} changed answering_time to {}".format(update.effective_user["id"], MVariables.answering_time))
        update.message.reply_text("answering_time changed to {}".format(MVariables.answering_time))


def set_question_handler(bot, update, args):  # /setquestion; may specify the number of question (without #)
    current_game = database.get_game_id(False, update.effective_user["id"])
    if MVariables.game_started:
        if update.effective_user["id"] in admins:
            if len(args) > 0:
                question_id = 0
                logger.info("User {} set question {}".format(update.effective_user["id"], question_id))
                question = ("".join(args))
                database.set_question(question, current_game)
            else:
                logger.info("User {} tried to enter empty answer".format(update.effective_user["id"]))
                update.message.reply_text("Try again with valid data: /setquestion needs at least one argument")
        else:
            logger.info("User {} tried to use inaccessible command {}".format(update.effective_user["id"],
                                                                              set_question_handler))
            update.message.reply_text("Oops, you don't have rights to access this command")
    else:
        logger.info("User {} tried to set question before game started".format(update.effective_user["id"]))
        update.message.reply_text("Game hasn't started yet")


def set_answer_handler(bot, update, args):  # /setanswer; need to specify the answer,
    # may specify the answer's question by typing #NUM as last argument, where NUM is the number of needed question
    if MVariables.game_started:  # !!!
        if update.effective_user["id"] in admins:
            current_game = database.get_game_id(True, update.effective_user["id"])
            question_id = 0  # !!!!!!!!!
            logger.info("User {} set answer to question {}".format(update.effective_user["id"], question_id))
            if len(args) > 0:
                if args[len(args) - 1].startswith("#"):  # special marker for question number
                    answer = ("".join(args))
                    database.set_answer(answer,
                                        database.DBVariables.current_number_of_questions, current_game)
                    # need to think about longer answers
                else:
                    answer = ("".join(args[:len(args) - 1]))
                    database.set_answer(answer, args[len(args) - 1], current_game)
            else:
                logger.info("User {} tried to enter empty answer".format(update.effective_user["id"]))
                update.message.reply_text("Try again with valid data: /set_answer needs at least one argument")
        else:
            logger.info("User {} tried to use inaccessible command {}".format(update.effective_user["id"],
                                                                              set_question_handler))
            update.message.reply_text("Oops, you don't have rights to access this command")
    else:
        logger.info("User {} tried to set question before game started".format(update.effective_user["id"]))
        update.message.reply_text("Game hasn't started yet")


def start_question_handler(bot, update, args):  # /startquestion; need to specify its number
    if MVariables.game_started:
        if update.effective_user["id"] in admins:
            current_game = database.get_game_id(True, update.effective_user["id"])
            question_id = database.DBVariables.current_number_of_questions
            logger.info("User {} started question {}".format(update.effective_user["id"], question_id))
            question = database.get_question(args[0], current_game)
            MVariables.current_question_id = args[0]  # !!!
            update.message.reply_text("{}. {}".format(args[0], question))
            # Message every participant  !!!
            MVariables.start_time = time.time()  # !!!
        else:
            logger.info("User {} tried to use inaccessible command {}".format(update.effective_user["id"],
                                                                              set_question_handler))
            update.message.reply_text("Oops, you don't have rights to access this command")
    else:
        logger.info("User {} tried to set question before game started".format(update.effective_user["id"]))
        update.message.reply_text("Game hasn't started yet")


def register_handler(bot, update, args):
    if len(args) > 0:
        team_name = ("".join(args))
        current_game = database.get_game_id(False, update.effective_user["id"])
        database.insert_player(update.effective_user["id"], team_name, current_game)
        logger.info("User {} registered team {}".format(update.effective_user["id"], team_name))
        update.message.reply_text("Team {} registered\nNow wait for questions to start ".format(team_name))
    else:
        logger.info("User {} didn't name his team".format(update.effective_user["id"]))
        update.message.reply_text("Try again entering your team's name after /register")


def answer_handler(bot, update, args):  # /answer; need to specify the answer itself
    current_game = database.get_game_id(False, update.effective_user["id"])
    question_id = MVariables.current_question_id  # !!!
    answer = ""
    if time.time() - MVariables.start_time < MVariables.answering_time:
        answer = ("".join(args)).lower()
        logger.info("User {} answered question {}".format(update.effective_user["id"], question_id))
        update.message.reply_text("Answer for question {} written".format(question_id))
    else:
        logger.info("User {} answered question {} after deadline".format(update.effective_user["id"], question_id))
        update.message.reply_text("Too late")
    # pause : restart if updated answer appeared : somehow need to throw exceptions using
    # global synchronizer of answer calls

    if answer != "" and time.time() - MVariables.start_time >= MVariables.answering_time:  # !!!
        if database.check_answer(answer, question_id, current_game):
            database.increase_points(update.effective_user["id"], current_game)
            logger.info("Team {} answered question {} correctly, points {}".format(
                                        database.get_team_name(update.effective_user["id"], current_game), question_id,
                                        database.get_points(update.effective_user["id"], current_game)))
            update.message.reply_text("Question {} - correct".format(question_id))
        else:
            logger.info("Team {} answered question {} mistakenly, points {}".format(
                database.get_team_name(update.effective_user["id"], current_game), question_id,
                database.get_points(update.effective_user["id"], current_game)))
            update.message.reply_text("Question {} - incorrect".format(question_id))
    if answer == "" and time.time() - MVariables.start_time >= MVariables.answering_time:  # !!!
        logger.info("User {} has no answer on question {}".format(update.effective_user["id"], question_id))
        update.message.reply_text("No answer")


def standings_handler(bot, update):  # /standings
    logger.info("User {} queried standings".format(update.effective_user["id"]))
    rating = database.get_standings(database.get_game_id(False, update.effective_user["id"]))
    for team_info in rating:  # team + points
        update.message.reply_text("{} : {}".format(team_info[0], team_info[1]))


def help_handler(bot, update):
    logger.info("User {} needed help".format(update.effective_user["id"]))
    update.message.reply_text("List of commands available for you:\n/register + team_name\n/answer + answer_text:"
                              " if both the game and a question are running\n/standings\n/help")

    if update.effective_user["id"] in admins:
        update.message.reply_text("As an admin you also can:\n/startgame\n/endgame\n/setansweringtime + answering_time"
                                  "\n/setquestion + question + number(unnecessary)"
                                  "\n/setanswer + answer + #number(default - answer for the last one)"
                                  "\n/startquestion + its historical number")


if __name__ == '__main__':
    logger.info("Starting bot")
    updater = telegram.ext.Updater(token=TOKEN)
    admin_file = open("admin_config.txt", 'r')
    admins = [int(line.strip()) for line in admin_file]  # Enter your admin's id/ids there divided by space

    updater.dispatcher.add_handler(telegram.ext.CommandHandler("start", start_handler))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler("startgame", start_game_handler))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler("endgame", end_game_handler, pass_args=True))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler("setansweringtime", set_answer_handler, pass_args=True))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler("setquestion", set_question_handler, pass_args=True))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler("setanswer", set_answer_handler, pass_args=True))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler("startquestion", start_question_handler, pass_args=True))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler("register", register_handler, pass_args=True))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler("answer", answer_handler, pass_args=True))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler("standings", standings_handler))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler("help", help_handler))

    run(updater)
