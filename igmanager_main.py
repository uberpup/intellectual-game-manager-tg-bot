import logging
import os
import sys
import telegram.ext
import time
import database  # Current issues: game_id's and databases; using sqlite with heroku


class MainVariables:
    game_started = False  # Will be changed after database added
    start_time = 0.0
    answering_time = 60.0
    current_question_id = 0


# Enabling logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

# Getting mode, so we could define run function for both local and Heroku setup
mode = os.getenv("MODE")
TOKEN = os.getenv("TOKEN")
MV = MainVariables()


if mode == "dev":
    def run(updater):
        updater.start_polling()
elif mode == "prod":
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
        game_id = 0  # Will be taken out of database
        logger.info("User {} started game {}".format(update.effective_user["id"], game_id))
        update.message.reply_text("Game {} started\nYou can /setquestion and /setanswer now".format(game_id))
        MV.game_started = True


def end_game_handler(bot, update):  # /endgame
    if not (update.effective_user["id"] in admins):
        logger.info("User {} tried to use inaccessible command {}".format(update.effective_user["id"],
                                                                          end_game_handler))
        update.message.reply_text("Oops, you don't have rights to access this command")
    else:
        game_id = 0  # Will be taken out of database
        logger.info("User {} finished game {}".format(update.effective_user["id"], game_id))
        # some result stats
        update.message.reply_text("Game {} finished".format(game_id))
        MV.game_started = False
        database.finish_db()


def set_answering_time(bot, update, args):  # /setansweringtime; specify the time in seconds
    if len(args) > 0:
        MV.answering_time = float(args[0])
        logger.info("User {} changed answering_time to {}".format(update.effective_user["id"], MV.answering_time))
        update.message.reply_text("answering_time changed to {}".format(MV.answering_time))


def set_question_handler(bot, update, args):  # /setquestion; may specify the number of question (without #)
    if MV.game_started:
        if update.effective_user["id"] in admins:
            if len(args) > 0:
                question_id = 0
                logger.info("User {} set question {}".format(update.effective_user["id"], question_id))
                question = ("".join(args))
                database.set_question(question)
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
    if MV.game_started:
        if update.effective_user["id"] in admins:
            question_id = 0
            logger.info("User {} set answer to question {}".format(update.effective_user["id"], question_id))
            if len(args) > 0:
                if args[len(args) - 1].startswith("#"):  # special marker for question number
                    answer = ("".join(args))
                    database.set_answer(answer,
                                        database.DBV.current_number_of_questions)  # need to think about longer answers
                else:
                    answer = ("".join(args[:len(args) - 1]))
                    database.set_answer(answer, args[len(args) - 1])
            else:
                logger.info("User {} tried to enter empty answer".format(update.effective_user["id"]))
                update.message.reply_text("Try again with valid data: /setanswer needs at least one argument")
        else:
            logger.info("User {} tried to use inaccessible command {}".format(update.effective_user["id"],
                                                                              set_question_handler))
            update.message.reply_text("Oops, you don't have rights to access this command")
    else:
        logger.info("User {} tried to set question before game started".format(update.effective_user["id"]))
        update.message.reply_text("Game hasn't started yet")


def start_question_handler(bot, update, args):  # /startquestion; need to specify its number
    if MV.game_started:
        if update.effective_user["id"] in admins:
            question_id = database.DBV.current_number_of_questions
            logger.info("User {} started question {}".format(update.effective_user["id"], question_id))
            question = database.get_question(args[0])
            MV.current_question_id = args[0]
            update.message.reply_text("{}. {}".format(args[0], question))
            # Message every participant
            MV.start_time = time.time()
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
        database.insert_player(update.effective_user["id"], team_name)
        logger.info("User {} registered team {}".format(update.effective_user["id"], team_name))
        update.message.reply_text("Team {} registered\nNow wait for questions to start ".format(team_name))
    else:
        logger.info("User {} didn't name his team".format(update.effective_user["id"]))
        update.message.reply_text("Try again entering your team's name after /register")


def answer_handler(bot, update, args):  # /answer; need to specify the answer itself
    question_id = MV.current_question_id
    answer = ""
    if time.time() - MV.start_time < MV.answering_time:
        answer = ("".join(args)).lower()
        logger.info("User {} answered question {}".format(update.effective_user["id"], question_id))
        update.message.reply_text("Answer for question {} written".format(question_id))
    else:
        logger.info("User {} answered question {} after deadline".format(update.effective_user["id"], question_id))
        update.message.reply_text("Too late")
    # pause : restart if updated answer appeared : somehow need to throw exceptions using
    # global synchronizer of answer calls
    if answer != "" and time.time() - MV.start_time >= MV.answering_time:
        if database.check_answer(answer, question_id):
            database.increase_points(update.effective_user["id"])
            logger.info("Team {} answered question {} correctly, points {}".format(
                                        database.get_team_name(update.effective_user["id"]), question_id,
                                        database.get_points(update.effective_user["id"])))
            update.message.reply_text("Question {} - correct".format(question_id))
        else:
            logger.info("Team {} answered question {} mistakenly, points {}".format(
                database.get_team_name(update.effective_user["id"]), question_id,
                database.get_points(update.effective_user["id"])))
            update.message.reply_text("Question {} - incorrect".format(question_id))
    if answer == "" and time.time() - MV.start_time >= MV.answering_time:
        logger.info("User {} has no answer on question {}".format(update.effective_user["id"], question_id))
        update.message.reply_text("No answer")


def standings_handler(bot, update):  # /standings
    logger.info("User {} queried standings".format(update.effective_user["id"]))
    rating = database.get_standings()
    for team in rating:  # may change this to format of top3 + ... + user's team
        update.message.reply_text("{}".format(team))


def help_handler(bot, update):
    logger.info("User {} needed help".format(update.effective_user["id"]))
    update.message.reply_text("List of commands available for you:\n/register + team_name\n/answer + answer_text:"
                              " if both the game and a question are running\n/standings\n/help")
    if update.effective_user["id"] in admins:
        update.message.reply_text("As an sdmin you also can:\n/startgame\n/endgame\n/setansweringtime + answering_time"
                                  "\n/setquestion + question + number(unnecessary)"
                                  "\n/setanswer + answer + #number(default - answer for the last one)"
                                  "\n/startquestion + its historical number")


if __name__ == '__main__':
    logger.info("Starting bot")
    updater = telegram.ext.Updater(token=TOKEN)
    admins = [360414453]  # Change to your admin's id

    updater.dispatcher.add_handler(telegram.ext.CommandHandler("start", start_handler))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler("startgame", start_game_handler))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler("endgame", end_game_handler))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler("setansweringtime", set_answer_handler, pass_args=True))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler("setquestion", set_question_handler, pass_args=True))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler("setanswer", set_answer_handler, pass_args=True))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler("startquestion", start_question_handler, pass_args=True))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler("register", register_handler, pass_args=True))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler("answer", answer_handler, pass_args=True))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler("standings", standings_handler))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler("help", help_handler))

    run(updater)

