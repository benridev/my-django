# create admin user
loginto container user www-data
source env/bin/activate
python manage.py createsuperuser