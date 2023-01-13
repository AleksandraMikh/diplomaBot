import os
import requests
import logging
import base64
import time
from typing import Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from telegram.ext import (CommandHandler, Updater, MessageHandler,
                          Filters)  #upm package(python-telegram-bot)
from telegram import (ReplyKeyboardMarkup,
                      TelegramError)  # upm package(python-telegram-bot)
from replit import db
from db_script import fill_the_base
import db_watch

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

  (diploma_message, number_of_matches,
   status,diploma_text) = find_diploma(last_name_or_whole_input=' '.join(words))

  if status:
    context.bot.send_message(text=diploma_message, chat_id=chat.id)
    byte_im = get_byte_image(last_name_or_whole_input=' '.join(words),
                             status=status,
                            diploma_text = diploma_text)
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
      chat.id, (f"Мы не поняли ваше сообщение, вы написали больше 3 слов."
                f" Введите фамилию, имя и отчество ребёнка через пробел."
                f" Сейчас вы ввели '{text_low}'. \n Если ФИО вашего ребёнка"
                f" состоит из более чем трёх слов, попробуйте ввести их"
                f" в другом порядке."))
    return

  if len(words) == 2:
    logging.info("Start searching with swaped 2 words.")
    (diploma_message, number_of_matches,
     status,diploma_text) = find_diploma(last_name_or_whole_input=words[1],
                            first_name=words[0])

  if len(words) == 3:
    logging.info("Start searching with swaped 3 words.")
    (diploma_message, number_of_matches,
     status,diploma_text) = find_diploma(last_name_or_whole_input=words[2],
                            first_name=words[0],
                            middle_name=words[1])

  if status:
    context.bot.send_message(text=diploma_message, chat_id=chat.id)
    if len(words) == 2:
      byte_im = get_byte_image(last_name_or_whole_input=words[1],
                               first_name=words[0],
                               status=status,
                              diploma_text = diploma_text)
    if len(words) == 3:
      byte_im = get_byte_image(last_name_or_whole_input=words[2],
                               first_name=words[0],
                               middle_name=words[1],
                               status=status,
                              diploma_text = diploma_text)
    update.message.reply_photo(photo=byte_im)
    context.bot.send_message(
      chat.id,
      ("Вот и ваш документ, поздравляем!"
       "Если вам нужен документ на второго ребёнка, отправьте его ФИО."))
    return

  context.bot.send_message(text=diploma_message, chat_id=chat.id)


def get_text_for_diploma(full_name: str, 
                        grade: str,
                        gender: str,
                        school:str,
                        city: str,
                        status: str):
  return (full_name,
         grade,
         gender,
         school,
         city,
         status)


def find_diploma(last_name_or_whole_input: str,
                 first_name: str = '',
                 middle_name: str = '') -> Tuple[str, int, Optional[str], Optional[str]]:
  '''Funcion searches for information about student in database.
    Middle name considered to be empty string if not provided.
    It returns tuple with message, number of matches and status of student if it's unique. 
    Status is str from db['statuses']. 
    If student does't exist in db or is not unique status is None.
    '''
  #TODO1: дописать формирование текста для диплома если найдено ровно
  #одно совпадение, использовать отдельную функцию (?)
  #возвращать текст в кортеже
  #TODO2: возвращать не кортеж, а словарь

  search_string = (f"{last_name_or_whole_input.lower()} "
                   f"{first_name.lower()} {middle_name.lower()}")
                   
  logging.info(
    f"Start find_diploma function: search_string = {search_string.strip()}")
  matches = db.prefix(search_string.strip())
  logging.info(f"find_diploma function: {len(matches)} matches found")
  if len(matches) == 0:
    if 'ё' in search_string:
      new_search_string = search_string.replace('ё', 'е')
      res = find_diploma(last_name_or_whole_input=new_search_string)
      if res[1] == 0:
        new_message = res[
          0] + '\n \n А ещё я заметил, что в имени вашего ребёнка есть буква Ë. Я проверил, нет ли совпадений при замене всех Ë на Е, их не нашлось 😔'
        res = (new_message, res[1], res[2], None)
      return res
    message = (f'Участник с именем {last_name_or_whole_input.title()}'
               f' {first_name.capitalize()} {middle_name.capitalize()}'
               f' не найден. Если вы ошиблись, отправьте ФИО ещё раз.'
               f' Если вы не ошиблись при печати имени,'
               f' свяжитесь с организатором по почте ?????@??.??')
    return (message, len(matches), None, None)
  if len(matches) > 1:
    message = (f'Я нашёл {len(matches)} участников c именем'
               f' {last_name_or_whole_input.title()}'
               f' {first_name.capitalize()} {middle_name.capitalize()}.'
               f' Не знаю, что делать, но я что-нибудь придумаю.'
               f' А пока попробуйте ввести ФИО иначе - вдруг'
               f' получится найти именно вашего ребёнка.')
    return (message, len(matches), None, None)
  if len(matches) == 1:
    message = (f'Участник с именем {last_name_or_whole_input.title()}'
               f' {first_name.capitalize()}'
               f' {middle_name.capitalize()} получил'
               f' {str(db["statuses"][db[matches[0]]["status"]]["message"])}.'
               f' Приступаем к формированию документа, это может занять'
               f' несколько минут.')
    #TODO: дописать здесь формирование текста для диплома
    diploma_text = get_text_for_diploma(full_name = matches[0], 
                                        **db[matches[0]]
                                       )
    return (message, len(matches), db[matches[0]]["status"], diploma_text)


def get_byte_image(last_name_or_whole_input: str,
                   status: str,
                   diploma_text: Tuple[str],
                   first_name: str = '',
                   middle_name: str = '') -> bytes:
  logging.info("Start get_byte_image function.")
  imgstr = db["statuses"][status]["base_picture"]
  image = Image.open(BytesIO(base64.b64decode(imgstr)))
  add_text = ImageDraw.Draw(image)
  font = ImageFont.truetype("arial.ttf", 30)
  msg = (f"It's me {last_name_or_whole_input.title()}"
         f" {first_name.capitalize()} {middle_name.capitalize()}!")
  # w, h = add_text.textsize(msg)
  # box = (100, 100, 500, 150)
  #TODO: написать здесь рисование правильного текста
  add_text.text(
    (100, 100),
    msg,
    fill=('#000000'),
    font=font,
  )
  i = 0
  for text in diploma_text:
    add_text.text(
      (100, 120 + 20*i),
      text,
      fill=('#000000'),
      font=font,
    )
    i+=1
  byteIO = BytesIO()
  image.save(byteIO, format='PNG')
  byteArr = byteIO.getvalue()
  return byteArr


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
