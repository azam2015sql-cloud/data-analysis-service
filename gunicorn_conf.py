import multiprocessing

# عدد العمال (workers)
# Render عادةً توفر CPU واحد أو اثنين حسب الخطة
workers = multiprocessing.cpu_count() * 2 + 1

# نوع العامل (sync مناسب لـ Flask البسيط)
worker_class = "sync"

# مهلة زمنية كبيرة لمنع Timeout أثناء تحليل ملفات كبيرة
timeout = 180

# تحديد عدد الطلبات القصوى لكل عامل لتفادي تسرب الذاكرة
max_requests = 500
max_requests_jitter = 50

# تسجيل مفصل
accesslog = "-"
errorlog = "-"
loglevel = "info"

# السماح بطلبات كبيرة (حتى 50MB)
limit_request_line = 4094
limit_request_field_size = 8190

# الاحتفاظ بالاتصالات مفتوحة قليلاً لتحسين الأداء
keepalive = 5

# التأكد من أن Gunicorn يعمل على المنفذ المطلوب من Render
bind = "0.0.0.0:{}".format(os.environ.get("PORT", "10000"))
