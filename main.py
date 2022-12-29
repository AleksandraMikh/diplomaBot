import os
import requests
import logging
import base64
import time
from typing import Union, Tuple, Optional
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

LAST_NAME, FIRST_NAME, CONFIRMATION = range(3)


def get_new_image():
  try:
    response = requests.get(URL).json()
  except Exception as error:
    logging.error(f'Ошибка при запросе к основному API: {error}')
    new_url = 'https://api.thedogapi.com/v1/images/search'
    response = requests.get(new_url).json()
  random_cat = response[0].get('url')
  return random_cat


'''
Пожалуйста, давай искать по почте? по имени это слишком мучительно
Люди могут вводить имя несколькими строками, они могут писать неполное имя, у них может быть несколько детей! 
Пусть человек вводит свой 
емэйл, я буду ему присылать всех известных мне детей по этому емэйлу, 
а если в списке кого-то из детей нет, то тогда попробую искать по 
имени. если и тогда не найду, пусть идёт к оргам и выясняет
'''


def last_name(update, context):
  text_caps = update.message.text.upper()
  reply_keyboard = [["/skip"]]
  update.message.reply_text(
    text=
    f"Ваша фамилия {text_caps}. Теперь введите ИМЯ вашего ребенка.Если ты не готов предоставить имя, нажми кнопку /skip",
    reply_markup=ReplyKeyboardMarkup(
      reply_keyboard,
      one_time_keyboard=True,
      resize_keyboard=True,
      input_field_placeholder="полное имя ребенка"),
  )
  context.user_data['last_name'] = update.message.text.lower()
  return FIRST_NAME


def skip_name(update, context):
  user = update.message.from_user
  logging.info("User %s did not send last_name.", user.first_name)
  update.message.reply_text(
    "Если вы не готовы предоставить фамилию или имя ребенка для получения диплома, свяжитесь с организаторами.",
    reply_markup = ReplyKeyboardRemove()
  )

  return ConversationHandler.END


def first_name_and_get_diploma(update, context):
  chat = update.effective_chat
  text_caps = update.message.text.upper()
  context.bot.send_message(
    chat.id,
    f"Ваша фамилия и имя {context.user_data['last_name'].upper()} {text_caps}. Мы ищем фамилию и имя вашего ребенка в базе участников, подождите пару минут и не останавливайте бота ( НЕ отправляйте команду /cancel )"
  )
  context.user_data['first_name'] = update.message.text.lower()
  diploma_message, finish_conversation, status = find_diploma(
    last_name=context.user_data['last_name'],
    first_name=context.user_data['first_name'])
  if not finish_conversation:
    context.user_data['status'] = status
    reply_keyboard = [['/confirm']]
    context.bot.send_message(text=diploma_message,
                             chat_id=chat.id,
                             reply_markup=ReplyKeyboardMarkup(
                               keyboard=reply_keyboard,
                               resize_keyboard=True,
                               one_time_keyboard=True,
                             ))
    return CONFIRMATION
  context.bot.send_message(text=diploma_message,
                             chat_id=chat.id,
                             reply_markup=ReplyKeyboardRemove())
  return ConversationHandler.END


def find_diploma(last_name: str, first_name: str) -> Tuple[str,bool,Optional[str]]:
  '''Funcion searches for information about student in database. 
  It returns tuple with message, flag and status of student. 
  Flag is True if conversation to be ended. 
  Status is str from db['statuses']. 
  If student does't exist in db or is not unique status is None.
  '''
  matches = db.prefix(
    f"{last_name.lower()} {first_name.lower()}")
  if len(matches) == 0: 
    message = (f'Участник с именем {last_name.capitalize()} {first_name.capitalize()} не найден.'
            f'Если вы ошиблись, запустите бота заново командой /start'
            f' (наберите это собщением и отправьте боту). Если вы не'
            f' ошиблись при печати имени, свяжитесь с организатором.')
    return (message, True, None)
  if len(matches) > 1:
    message = f'Я нашёл {len(matches)} участников c именем {last_name.capitalize()} {first_name.capitalize()}. Не знаю, что делать, но я что-нибудь придумаю. А пока наш разговор окончен.'
    return (message, True, None)
  if len(matches) == 1:
    message = (f'Участник с именем {last_name.capitalize()} {first_name.capitalize()} получил'
            f' {str(db["statuses"][db[matches[0]]["status"]]["message"])}. Если информация верна,'
            f' нажмите кнопку /confirm. Если в информации ошибка,'
            f' свяжитесь с организаторами.')
    return (message, False, db[matches[0]]["status"])

def wake_up(update, context):
  t1 = time.time()
  chat = update.effective_chat
  name = update.message.chat.first_name
  # button = ReplyKeyboardMarkup([['/newcat'],['/start']], resize_keyboard=True)
  # button = ReplyKeyboardMarkup([['/get_diploma']], resize_keyboard=True)
  reply_keyboard = [["/skip"]]
  update.message.reply_text(
    text=
    f'Привет, {name}, я бот ТЛ2х2, я умею раздавать дипломы. Если ты хочешь получить свой диплом, напиши ФАМИЛИЮ своего ребёнка. Если ты не готов предоставить фамилию, нажми кнопку /skip',
    reply_markup=ReplyKeyboardMarkup(
      reply_keyboard,
      one_time_keyboard=True,
      resize_keyboard=True,
      input_field_placeholder="фамилия ребенка"),
  )
  return LAST_NAME


def get_byte_image(last_name: str, 
                  first_name: str, 
                  status: str) -> bytes:
  imgstr = db["statuses"][status]["base_picture"]
  image = Image.open(BytesIO(base64.b64decode(imgstr)))
  add_text = ImageDraw.Draw(image)
  font = ImageFont.truetype("arial.ttf", 30)
  add_text.text(
    (100, 100),
    f"It's me {last_name.capitalize()} {first_name.capitalize()}!",
    fill=('#000000'),
    font=font,
  )
  byteIO = BytesIO()
  image.save(byteIO, format='PNG')
  byteArr = byteIO.getvalue()
  return byteArr


def cancel(update, context):
  """Cancels and ends the conversation."""
  user = update.message.from_user
  logging.info("User %s canceled the conversation.", user.first_name)
  update.message.reply_text("Bye! I hope we can talk again some day.",
                            reply_markup=ReplyKeyboardRemove())

  return ConversationHandler.END


def confirm(update, context):
  """Asks user to check data from database"""
  user = update.message.from_user
  logging.info("User %s confirmed information about diploma.", user.first_name)
  reply_keyboard = [["/too_long"]]
  update.message.reply_text(
    "Вы подтвердили информацию о дипломе или сертификате участника, готовим для вас диплом (сертификат). Это может занять несколько минут.",
    reply_markup=ReplyKeyboardMarkup(
      reply_keyboard,
      one_time_keyboard=True,
      resize_keyboard=True,
      input_field_placeholder="фамилия ребенка"),
  )
  update.message.reply_text(
    'Функция get_byte_image ещё не реализована, но пока что я могу отправить вам это'
  )
  byte_im = get_byte_image(last_name = context.user_data['last_name'], 
                          first_name = context.user_data['first_name'],
                          status = context.user_data['status'])
  update.message.reply_photo(photo = byte_im)
  return ConversationHandler.END


def main():

  conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", wake_up)],
    states={
      LAST_NAME: [
        MessageHandler(Filters.regex(r"^\w+$"), last_name),
        CommandHandler("skip", skip_name),
      ],
      FIRST_NAME: [
        MessageHandler(Filters.regex(r"^\w+$"), first_name_and_get_diploma),
        CommandHandler("skip", skip_name),
      ],
      CONFIRMATION: [
        CommandHandler("confirm", confirm),
      ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
  )

  updater.dispatcher.add_handler(conv_handler)

  updater.start_polling()
  updater.idle()


if __name__ == "__main__":
  # fill_the_base()
  # db_watch.watch_the_base()
  main()
