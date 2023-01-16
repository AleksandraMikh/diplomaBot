from typing import Tuple, Optional
from replit import db
import logging
import base64
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from db_script import GRADE, STATUSES


def get_text_for_diploma(full_name: str, grade: str, gender: str, school: str,
                         city: str, status: str):
  second_name, first_name, _ = full_name.split()
  strings = ("награждается", f"учени{gender} {grade} класса", f"{school}",
             f"({city})", f"{second_name} {first_name}",
             f"за {STATUSES[status]['awarded_for']}",
             f"в {GRADE[grade]['division_rus']} группе олимпиады",
             f"for success in {GRADE[grade]['division_en']} division",
             f"Старший по параллели {grade} класса",
             f"{GRADE[grade]['master_name']}")
  return strings


def find_diploma(
    last_name_or_whole_input: str,
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
               f' {str(STATUSES[db[matches[0]]["status"]]["message"])}.'
               f' Приступаем к формированию документа, это может занять'
               f' несколько минут.')
    #TODO: дописать здесь формирование текста для диплома
    diploma_text = get_text_for_diploma(full_name=matches[0], **db[matches[0]])
    return (message, len(matches), db[matches[0]]["status"], diploma_text)


def get_byte_image(
  status: str,
  diploma_text: Tuple[str],
) -> bytes:
  logging.info("Start get_byte_image function.")
  imgstr = STATUSES[status]["base_picture"]
  image = Image.open(BytesIO(base64.b64decode(imgstr)))
  add_text = ImageDraw.Draw(image)
  font_small = ImageFont.truetype("arial.ttf", 25)
  font_huge = ImageFont.truetype("arial.ttf", 50)
  font_sub = ImageFont.truetype("Bahnschrift.ttf", 14)
  # w, h = add_text.textsize(msg)
  # box=(330, 850, 460, 920)
  #TODO: написать здесь рисование правильного текста
  i = 0
  for text in diploma_text:
    if i < 4:
      add_text.text(
        (354, 460 + 30 * i),
        text,
        anchor='ms',
        fill=('#000000'),
        font=font_small,
      )
    if i == 4:
      add_text.text(
        (354, 590),
        text.title(),
        anchor='ms',
        fill=('#000000'),
        font=font_huge,
      )
    if 4 < i < 8:
      add_text.text(
        (354, 620 + 30 * (i - 5)),
        text,
        anchor='ms',
        fill=('#000000'),
        font=font_small,
      )
    if i == 8:
      add_text.text(
        (68, 868),
        text,
        fill=('#000000'),
        font=font_sub,
      )
    if i == 9:
      add_text.text(
        (491, 868),
        text,
        fill=('#000000'),
        font=font_sub,
      )
    i += 1

  _, grade, _ = diploma_text[1].split()
  imgstr = GRADE[grade]['master_subscribe']
  if grade == '2':
    subscription = Image.open(BytesIO(base64.b64decode(imgstr)))
    subscription.thumbnail(size=(230, 70))
    image.paste(im=subscription, box=(330, 850))
  else:
    add_text.text(
      (300, 868),
      imgstr,
      fill=('#000000'),
      font=font_sub,
    )

  byteIO = BytesIO()
  image.save(byteIO, format='PNG')
  byteArr = byteIO.getvalue()
  return byteArr
