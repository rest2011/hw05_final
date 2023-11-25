# Соцсеть Yatube
Социальная сеть блогеров. Повзоляет написание постов и публикации их в отдельных группах, подписки на посты, добавление и удаление записей и их комментирование. Подписки на любимых блогеров.
## Технологии
Python, Django, SQLite, Bootstrap, HTML, CSS
## Установка и запуск
Инструкции по установке
- Клонируйте репозиторий:
```
git clone git@github.com:rest2011/hw05_final.git
```
- Установите и активируйте виртуальное окружение:

для MacOS
```
python3 -m venv venv
```
для Windows
```
python -m venv venv
source venv/bin/activate
source venv/Scripts/activate
```
- Установите зависимости из файла requirements.txt:
```
pip install -r requirements.txt
```
- Примените миграции:
```
python manage.py migrate
```
- В папке с файлом manage.py выполните команду:
```
python manage.py runserver
```
## Автор
Ринат Хаматьяров (https://github.com/rest2011)


