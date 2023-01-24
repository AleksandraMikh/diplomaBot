from replit import db
import diploma_bases
import subscriptions

GRADE = {
  '1': {
    'master_name': '/А.В.Кашкарова/',
    'master_subscribe': subscriptions.first_grade,
    'division_rus': 'младшей',
    'division_en': 'junior'
  },
  '2': {
    'master_name': '/А.А.Мищенко/',
    'master_subscribe': subscriptions.second_grade,
    'division_rus': 'младшей',
    'division_en': 'junior'
  },
  '3': {
    'master_name': '/К.И.Александров/',
    'master_subscribe': subscriptions.third_grade,
    'division_rus': 'средней',
    'division_en': 'middle'
  },
  '4': {
    'master_name': '/Н.С.Борисов/',
    'master_subscribe': subscriptions.forth_grade,
    'division_rus': 'старшей',
    'division_en': 'older'
  }
}

diploma1 = {
  'title': 'диплом I степени',
  'base_picture': diploma_bases.base_1,
  'message': 'диплом I степени',
  'awarded_for': 'победу',
}
diploma2 = {
  'title': 'диплом II степени',
  'base_picture': diploma_bases.base_2,
  'message': 'диплом II степени',
  'awarded_for': 'успешное выступление',
}
diploma3 = {
  'title': 'диплом III степени',
  'base_picture': diploma_bases.base_3,
  'message': 'диплом III степени',
  'awarded_for': 'успешное выступление',
}
certificate_of_honor1 = {
  'title': 'похвальный отзыв I степени',
  'base_picture': diploma_bases.cert_of_honor1_base,
  'message': 'похвальный отзыв I степени',
  'awarded_for': 'успешное выступление',
}
certificate_of_honor2 = {
  'title': 'похвальный отзыв II степени',
  'base_picture': diploma_bases.cert_of_honor2_base,
  'message': 'похвальный отзыв II степени',
  'awarded_for': 'успешное выступление',
}

STATUSES = {
  '1': diploma1,
  '2': diploma2,
  '3': diploma3,
  'ПГ1': certificate_of_honor1,
  'ПГ2': certificate_of_honor2,
}


def fill_the_base():

  last_name_first_name = [['Иванов', 'Иван', 'Иванович'],
                          ['Петров', 'Пётр', 'Петрович'],
                          ['Петров', 'Петр', 'Иванович'],
                          ['Сидоров', 'Сидор', 'Сидорович'],
                          ['Иванова', 'Анна', 'Ивановна']]
  student = {}
  i = 0
  for status in STATUSES:
    student['status'] = status
    student['grade'] = str(i % 4 + 1)
    # student['last_name'] = last_name_first_name[i][0]
    # student['first_name'] = last_name_first_name[i][1]
    # student['middle_name'] = last_name_first_name[i][2]
    full_name = ' '.join(last_name_first_name[i])
    if 'Анна' in full_name:
      student['gender'] = 'ца'
    else:
      student['gender'] = 'к'
    if i != 0:
      student['school'] = 'короткое название школы'
    else:
      student['school'] = 'очень длинное название школы-с-дефисами'
    if i != 1:
      student['city'] = 'Саратов'
    else:
      student['city'] = 'Белград, Сербия'

    db[full_name.lower()] = student
    print('name = ', full_name, 'status = ', status)
    i += 1

  strange_last_name_first_name = [
    'бюльбюль оглы полад', 'петров-водкин сергей',
    'иванов-петров марк-антоний олегович',
    'королева андаллов первых людей дейнерис бурерождённая',
    'Мијатовић Ђорђе'.lower()
  ]
  i = 0
  for status in STATUSES:
    student['status'] = status
    student['grade'] = str((i + 1) % 4 + 1)
    if 'королева' in strange_last_name_first_name[i]:
      student['gender'] = 'ца'
    else:
      student['gender'] = 'к'
    if i != 0:
      student['school'] = 'короткое название школы'
    else:
      student['school'] = 'очень длинное название школы-с-дефисами'
    if i != 4:
      student['city'] = 'Саратов'
    else:
      student['city'] = 'Белград, Сербия'
    db[strange_last_name_first_name[i]] = student
    i += 1
