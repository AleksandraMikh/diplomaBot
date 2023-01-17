import os
import logging
from telegram.ext import (CommandHandler, Updater, MessageHandler,
                          Filters)  #upm package(python-telegram-bot)
from db_script import fill_the_base
import db_watch
from utils import (find_diploma, get_byte_image, delete_white_background)

token = os.environ['TOKEN']
updater = Updater(token=token)
URL = 'https://api.thecatapi.com/v1/images/search'

logging.basicConfig(
  # filename='example.log',
  # filemode='w',
  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
  level=logging.DEBUG)


def wake_up(update, context):
  logging.info("Start wake_up funtion.")
  name = update.message.chat.first_name
  reply_keyboard = [["/restart"]]
  update.message.reply_text(
    text=(f'Привет, {name}, я бот ТЛ2х2, '
          'я умею раздавать дипломы. Если вы '
          'хотите получить диплом за своего ребёнка, '
          'напишите его ФАМИЛИЮ, ИМЯ и ОТЧЕСТВО (при наличии).'),
    reply_markup=ReplyKeyboardMarkup(
      reply_keyboard,
      # one_time_keyboard=True,
      resize_keyboard=True,
      input_field_placeholder="ФИО ребенка"),
  )


def full_name_and_get_diploma(update, context):
  #TODO: переписать распаковку результата find_diploma
  #с учётом передачи текста для печати
  logging.info("Start full_name_and_get_diploma funtion.")
  chat = update.effective_chat
  text_low = update.message.text.lower()
  words = text_low.split()
  if len(words) < 2:
    logging.info(f"User {chat['username']} entered less than 2 words")
    context.bot.send_message(
      chat.id, (f"Мы не поняли ваше сообщение, вы написали только одно слово."
                f" Введите фамилию, имя и отчество ребёнка через пробел."
                f" Сейчас вы ввели '{text_low}'."))
    return

  (diploma_message, number_of_matches, status,
   diploma_text) = find_diploma(last_name_or_whole_input=' '.join(words))
  logging.info("Information about student is found and unpacked to full_name_and_get_diploma.")

  if status:
    context.bot.send_message(text=diploma_message, chat_id=chat.id)
    byte_im = get_byte_image(status=status, diploma_text=diploma_text)
    update.message.reply_photo(photo=byte_im)
    context.bot.send_message(
      chat.id,
      "Вот и ваш документ, поздравляем! Если вам нужен документ на второго ребёнка, отправьте его ФИО."
    )
    return

  if number_of_matches > 1:
    logging.info(f"User {chat['username']} got more than one match.")
    context.bot.send_message(text=diploma_message, chat_id=chat.id)
    return

  if len(words) > 3:
    context.bot.send_message(
      chat.id, (f"Мы не поняли ваше сообщение."
                f" Введите фамилию, имя и отчество ребёнка через пробел."
                f" Сейчас вы ввели '{text_low}'. \n Если ФИО вашего ребёнка"
                f" состоит из более чем трёх слов, попробуйте ввести их"
                f" в другом порядке."))
    return

  if len(words) == 2:
    logging.info("Start searching with swaped 2 words.")
    (diploma_message, number_of_matches, status,
     diploma_text) = find_diploma(last_name_or_whole_input=words[1],
                                  first_name=words[0])
    logging.info("Information about student is found and unpacked to full_name_and_get_diploma.")

  if len(words) == 3:
    logging.info("Start searching with swaped 3 words.")
    (diploma_message, number_of_matches, status,
     diploma_text) = find_diploma(last_name_or_whole_input=words[2],
                                  first_name=words[0],
                                  middle_name=words[1])
    logging.info("Information about student is found and unpacked to full_name_and_get_diploma.")

  if status:
    context.bot.send_message(text=diploma_message, chat_id=chat.id)
    if len(words) == 2:
      byte_im = get_byte_image(status=status, diploma_text=diploma_text)
    if len(words) == 3:
      byte_im = get_byte_image(status=status, diploma_text=diploma_text)
    update.message.reply_photo(photo=byte_im)
    context.bot.send_message(
      chat.id,
      ("Вот и ваш документ, поздравляем!"
       "Если вам нужен документ на второго ребёнка, отправьте его ФИО."))
    return

  context.bot.send_message(text=diploma_message, chat_id=chat.id)


def error_handler(update, context):
  logging.error(context.error)


def main():

  start_handler = CommandHandler("start", wake_up)
  full_name_handler = MessageHandler(filters=Filters.text,
                                     callback=full_name_and_get_diploma)

  updater.dispatcher.add_handler(start_handler)
  updater.dispatcher.add_handler(full_name_handler)
  updater.dispatcher.add_error_handler(error_handler)

  updater.start_polling()
  updater.idle()


if __name__ == "__main__":
  # fill_the_base()
  # db_watch.watch_the_base()
  main()
  # delete_white_background()
