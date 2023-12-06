web: gunicorn tlfb.wsgi --log-file -
release: python manage.py migrate
worker: REMAP_SIGTERM=SIGQUIT celery worker --app=tlfb.tasks.app -l info
