# create admin user
loginto container user www-data
source env/bin/activate
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py createsuperuser
python manage.py collectstatic --no-input --clear