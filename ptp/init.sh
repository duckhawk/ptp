#!/bin/bash

/ptp/.pyenv/versions/ptp/bin/python3 manage.py makemigrations
/ptp/.pyenv/versions/ptp/bin/python3 manage.py migrate
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@ptp.ptp', 'qwerty')" | /ptp/.pyenv/versions/ptp/bin/python3 manage.py shell
/ptp/.pyenv/versions/ptp/bin/uwsgi --ini /ptp/uwsgi/ptp.main
