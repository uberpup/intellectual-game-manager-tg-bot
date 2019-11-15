# intellectual-game-manager-tg-bot
Telegram bot for managing intellectual games, that require sending answers directly to judges.
Bot uses Heroku hosting and Heroku database, but my private data is not on this repo :).

Your own data shall be written in console after launching and written in the console or in the config file.
##### Bot allows to:
1. Start your game session.
2. Add users to your session by its id.
3. Set all internal parameters, like time for answering the question, questions and answers on them.
4. Questions, answers ans standings are stored in the database.
5. Every player can see current standings, that are renewed after each question check.
6. Creator can add admins for each session by their telegram id to config file.

Program uses telegram.ext to work with bot and peewee library to work with databases.
