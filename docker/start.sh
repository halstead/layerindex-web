#!/bin/sh

NUM_WORKERS=4
TIMEOUT=500

# Start Gunicorn processes
echo "Starting Gunicorn."
cd /opt/layerindex
exec gunicorn wsgi:application \
    --workers $NUM_WORKERS \
    --timeout $TIMEOUT \
    --bind :5000
    --log-level=debug
    --chdir=/opt/layerindex


echo "Starting rabbitmq."
rabbitmq-server -detached

echo "Starting Celery."
/usr/local/bin/celery -A layerindex.tasks worker --loglevel=info --workdir=/opt/layerindex

