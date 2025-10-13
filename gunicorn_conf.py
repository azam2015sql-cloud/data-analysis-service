# gunicorn_conf.py
# Tune Gunicorn for Render: increase timeout and set modest number of workers
workers = 2
threads = 2
timeout = 90
keepalive = 5
bind = "0.0.0.0:%s" % (os.environ.get("PORT", "10000"))
loglevel = "info"
accesslog = "-"
errorlog = "-"
