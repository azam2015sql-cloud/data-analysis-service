# gunicorn_conf.py
import os

workers = 1
threads = 1
timeout = 180
worker_class = "gthread"
bind = "0.0.0.0:" + str(os.environ.get("PORT", 10000))
errorlog = "-"
accesslog = "-"
loglevel = "info"
preload_app = True
keepalive = 5
