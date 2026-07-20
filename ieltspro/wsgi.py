import os
import sys

# Добавляем пути самым простым способом
sys.path.insert(0, '/home/b/bekovic09g/ulugbekov_uz/public_html')
sys.path.insert(0, '/home/b/bekovic09g/ulugbekov_uz/public_html/venv/lib/python3.8/site-packages')

os.environ['DJANGO_SETTINGS_MODULE'] = 'ieltspro.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()