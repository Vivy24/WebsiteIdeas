gunicorn --bind=0.0.0.0 --timeout 600 "minimaldb:create_app()"
