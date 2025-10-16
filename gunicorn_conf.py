import os

# 🔹 عامل واحد فقط لتقليل استهلاك الذاكرة (مناسب لخطة Render المجانية)
workers = 1

# 🔹 نوع العامل
worker_class = "sync"

# 🔹 مهلة زمنية مناسبة (دقيقتان)
timeout = 120

# 🔹 لتفادي تسرب الذاكرة أو التوقف المفاجئ
max_requests = 200
max_requests_jitter = 20

# 🔹 تسجيل بسيط
accesslog = "-"
errorlog = "-"
loglevel = "info"

# 🔹 حجم الطلبات المسموح بها (50MB كحد أقصى)
limit_request_line = 4094
limit_request_field_size = 8190

# 🔹 إبقاء الاتصال مفتوح قليلاً لتحسين الأداء
keepalive = 5

# 🔹 تشغيل على نفس المنفذ الذي يحدده Render
bind = "0.0.0.0:{}".format(os.environ.get("PORT", "10000"))
