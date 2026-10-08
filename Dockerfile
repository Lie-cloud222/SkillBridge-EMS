FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 DJANGO_SETTINGS_MODULE=config.settings.production

RUN apt-get update && apt-get install -y --no-install-recommends curl gnupg unixodbc-dev gcc g++ \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql.list \
    && apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

#RUN DJANGO_SECRET_KEY=build-only python manage.py collectstatic --noinput

CMD python manage.py collectstatic --noinput && python manage.py migrate --noinput && python manage.py setup_roles && daphne -b 0.0.0.0 -p ${PORT:-10000} config.asgi:application