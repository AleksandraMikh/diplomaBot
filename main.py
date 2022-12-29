import os
import requests
import logging
import base64
import time
from typing import Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from telegram.ext import (CommandHandler, Updater, ConversationHandler,
                          MessageHandler,
                          Filters)  #upm package(python-telegram-bot)
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove  #upm package(python-telegram-bot)
from replit import db
from db_script import fill_the_base
import db_watch

token = os.environ['TOKEN']
updater = Updater(token=token)
URL = 'https://api.thecatapi.com/v1/images/search'

logging.basicConfig(
  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
  level=logging.DEBUG)


def full_name_and_get_diploma(update, context):
  chat = update.effective_chat
  text_low = update.message.text.lower()
  words = text_low.split()
  if len(words) < 2 or len(words) > 3:
    context.bot.send_message(
    chat.id,
    f"Мы не поняли ваше сообщение. Введите фамилию, имя и отчество ребёнка через пробел."
    f" Сейчас вы ввели '{text_low}'.")
    return
  (diploma_message, 
   no_match_or_many_matches, 
   status) = find_diploma(
              last_name=words[0],
              first_name=words[1],
              middle_name = words[2])
  
  if not no_match_or_many_matches:
    context.bot.send_message(text=diploma_message,
                             chat_id=chat.id)
    byte_im = get_byte_image(last_name=words[0],
                            first_name=words[1],
                            middle_name = words[2],
                            status = status)
    update.message.reply_photo(photo = byte_im)
    context.bot.send_message(
    chat.id,
    "Вот и ваш документ, поздравляем! Если вам нужен документ на второго ребёнка, отправьте его ФИО.")
    return

  (diploma_message, 
   no_match_or_many_matches, 
   status) = find_diploma(
              last_name=words[2],
              first_name=words[0],
              middle_name = words[1])
  if not no_match_or_many_matches:
    context.bot.send_message(text=diploma_message,
                             chat_id=chat.id)
    byte_im = get_byte_image(last_name=words[2],
                            first_name=words[0],
                            middle_name = words[1],
                            status = status)
    update.message.reply_photo(photo = byte_im)
    context.bot.send_message(
    chat.id,
    "Вот и ваш документ, поздравляем! Если вам нужен документ на второго ребёнка, отправьте его ФИО.")
    return
  context.bot.send_message(text=diploma_message,
                             chat_id=chat.id)


def find_diploma(last_name: str, 
                 first_name: str, 
                 middle_name: str = '') -> Tuple[str,bool,Optional[str]]:
  '''Funcion searches for information about student in database.
  Middle name considered to be empty string if not provided.
  It returns tuple with message, flag and status of student. 
  Flag is True if more or less then 1 match was found. 
  Status is str from db['statuses']. 
  If student does't exist in db or is not unique status is None.
  '''
  matches = db.prefix(
    f"{last_name.lower()} {first_name.lower()} {middle_name.lower()}")
  if len(matches) == 0: 
    message = (f'Участник с именем {last_name.capitalize()}'
            f' {first_name.capitalize()} {middle_name.capitalize()} не найден.'
            f'Если вы ошиблись, отправьте ФИО ещё раз.'
            f' Если вы не ошиблись при печати имени,'
            f' свяжитесь с организатором по почте ?????@??.??')
    return (message, True, None)
  if len(matches) > 1:
    message = f'Я нашёл {len(matches)} участников c именем {last_name.capitalize()} {first_name.capitalize()} {middle_name.capitalize()}. Не знаю, что делать, но я что-нибудь придумаю. А пока попробуйте ввести ФИО иначе - вдруг получится найти именно вашего ребёнка.'
    return (message, True, None)
  if len(matches) == 1:
    message = (f'Участник с именем {last_name.capitalize()} {first_name.capitalize()}'
            f' {middle_name.capitalize()} получил'
            f' {str(db["statuses"][db[matches[0]]["status"]]["message"])}.'
            f' Приступаем к формированию документа, это может занять несколько минут.')
    return (message, False, db[matches[0]]["status"])

def wake_up(update, context):
  name = update.message.chat.first_name
  reply_keyboard = [["/restart"]]
  update.message.reply_text(
    text=
    f'Привет, {name}, я бот ТЛ2х2, я умею раздавать дипломы. Если вы хотите получить диплом за своего ребёнка, напишите его ФАМИЛИЮ, ИМЯ и ОТЧЕСТВО (при наличии).',
    reply_markup=ReplyKeyboardMarkup(
      reply_keyboard,
      # one_time_keyboard=True,
      resize_keyboard=True,
      input_field_placeholder="ФИО ребенка"),
  )


def get_byte_image(last_name: str, 
                  first_name: str,
                  status: str,
                  middle_name: str = '') -> bytes:
  imgstr = db["statuses"][status]["base_picture"]
  image = Image.open(BytesIO(base64.b64decode(imgstr)))
  add_text = ImageDraw.Draw(image)
  font = ImageFont.truetype("arial.ttf", 30)
  add_text.text(
    (100, 100),
    f"It's me {last_name.capitalize()} {first_name.capitalize()} {middle_name.capitalize()}!",
    fill=('#000000'),
    font=font,
  )
  byteIO = BytesIO()
  image.save(byteIO, format='PNG')
  byteArr = byteIO.getvalue()
  return byteArr


def main():

  start_handler = CommandHandler("start", wake_up)
  full_name_handler = MessageHandler(filters = Filters.text, 
                                     callback = full_name_and_get_diploma)

  updater.dispatcher.add_handler(start_handler)
  updater.dispatcher.add_handler(full_name_handler)

  updater.start_polling()
  updater.idle()


if __name__ == "__main__":
  # fill_the_base()
  # db_watch.watch_the_base()
  main()
