# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3) Copia el resto del proyecto:
#    - app/, static/, certs/, config/, logs/, wsgi.py, gunicorn_config.py, README.md...
COPY . .

EXPOSE 8000

CMD ["gunicorn", "-c", "gunicorn_config.py", "wsgi:app"]
