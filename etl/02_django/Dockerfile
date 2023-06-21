# Укажите необходимую версию python
FROM python:3.11

# Выберите папку, в которой будут размещаться файлы проекта внутри контейнера
WORKDIR /usr/src/app

# Заведите необходимые переменные окружения
ENV DJANGO_SETTINGS_MODULE 'config.settings'
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


# Скопируйте в контейнер файлы, которые редко меняются
COPY requirements.txt requirements.txt
COPY uwsgi.ini uwsgi.ini

# Установите зависимости
RUN  pip3 install --no-cache-dir --upgrade pip \
     && pip3 install --no-cache-dir -r requirements.txt

# Скопируйте всё оставшееся. Для ускорения сборки образа эту команду стоит разместить ближе к концу файла.
COPY . .

# Укажите порт, на котором приложение будет доступно внутри Docker-сети
EXPOSE 8000

# Укажите, как запускать ваш сервис

# CMD ["uwsgi", "--strict", "--ini", "uwsgi.ini"]
RUN chmod 777 /usr/src/app/run_migrations.sh

CMD ["bash", "/usr/src/app/run_migrations.sh"]