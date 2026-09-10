FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python manage.py collectstatic --noinput && useradd --uid 10001 --create-home appuser
USER appuser
CMD ["gunicorn", "config.wsgi:application", "--config", "config/gunicorn.conf.py"]
