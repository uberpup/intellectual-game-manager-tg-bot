import logging
import os
import sys
import telegram.ext
import time
import database
# Current issues: game_id's and databases; multiword answers; heroku and testing

class MainVariables:
    game_started = False  # Will be changed after database added
    start_time = 0.0


# Enabling logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

# Getting mode, so we could define run function for local and Heroku setup
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
    update.message.reply_text("Hello!\nChoose to /startgame or to /participate")


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


def set_question_handler(bot, update, args):  # /setquestion
    if MV.game_started:
        if update.effective_user["id"] in admins:
            question_id = 0
            logger.info("User {} set question {}".format(update.effective_user["id"], question_id))
            database.set_question(args[0])
        else:
            logger.info("User {} tried to use inaccessible command {}".format(update.effective_user["id"],
                                                                              set_question_handler))
            update.message.reply_text("Oops, you don't have rights to access this command")
    else:
        logger.info("User {} tried to set question before game started".format(update.effective_user["id"]))
        update.message.reply_text("Game hasn't started yet")


def set_answer_handler(bot, update, args):  # /setanswer
    if MV.game_started:
        if update.effective_user["id"] in admins:
            question_id = 0
            logger.info("User {} set answer to question {}".format(update.effective_user["id"], question_id))
            if len(args) == 1:
                database.set_answer(args[0],
                                    database.DBV.current_number_of_questions)  # need to think about longer answers
            else:
                database.set_answer(args[0], args[1])
        else:
            logger.info("User {} tried to use inaccessible command {}".format(update.effective_user["id"],
                                                                              set_question_handler))
            update.message.reply_text("Oops, you don't have rights to access this command")
    else:
        logger.info("User {} tried to set question before game started".format(update.effective_user["id"]))
        update.message.reply_text("Game hasn't started yet")


def start_question_handler(bot, update, args):  # /startquestion
    if MV.game_started:
        if update.effective_user["id"] in admins:
            question_id = database.DBV.current_number_of_questions
            logger.info("User {} started question {}".format(update.effective_user["id"], question_id))
            question = database.get_question(args[0])
            update.message.reply_text("{}. {}".format(args[0], question))
            MV.start_time = time.time()
        else:
            logger.info("User {} tried to use inaccessible command {}".format(update.effective_user["id"],
                                                                              set_question_handler))
            update.message.reply_text("Oops, you don't have rights to access this command")
    else:
        logger.info("User {} tried to set question before game started".format(update.effective_user["id"]))
        update.message.reply_text("Game hasn't started yet")


def answer_handler(bot, update, args):  # /answer
    question_id = 0
    answer = ""
    if time.time() - MV.start_time < 60:
        answer = ("".join(args)).lower()
        logger.info("User {} answered question {}".format(update.effective_user["id"], question_id))
        update.message.reply_text("Answer for question {} written".format(question_id))
    else:
        logger.info("User {} answered question {} after deadline".format(update.effective_user["id"], question_id))
        update.message.reply_text("Too late")
    # pause
    if answer != "" and time.time() - MV.start_time >= 60:
        update.message.reply_text("+" if database.check_answer(answer, question_id) else "-")


def standings_handler(bot, update):  # /standings
    logger.info("User {} queried standings".format(update.effective_user["id"]))
    rating = database.get_standings()
    for team in rating:
        update.message.reply_text("{}".format(team))


if __name__ == '__main__':
    logger.info("Starting bot")
    updater = telegram.ext.Updater(token=TOKEN)
    admins = set()

    updater.dispatcher.add_handler(telegram.ext.CommandHandler("start", start_handler))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler("startgame", start_game_handler))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler("setquestion", set_question_handler, pass_args=True))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler("setanswer", set_answer_handler, pass_args=True))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler("startquestion", start_question_handler, pass_args=True))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler("answer", answer_handler, pass_args=True))
    updater.dispatcher.add_handler(telegram.ext.CommandHandler("standings", standings_handler))

    run(updater)
