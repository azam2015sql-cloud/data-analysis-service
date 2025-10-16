# -------------------------------
# Gunicorn Configuration for Render
# Optimized for low-memory environments (≤512Mi)
# -------------------------------

import multiprocessing

# عدد العمال (workers)
# 1 كافٍ لتجنب استهلاك الذاكرة الزائد
workers = 1

# لكل عامل، خيطين (threads) لطلبات متزامنة بسيطة
threads = 2

# المدة القصوى لتنفيذ الطلب (بالثواني)
timeout = 180

# نوع العامل
worker_class = "gthread"

# الربط (Render يحدد المنفذ عبر متغير PORT)
bind = "0.0.0.0:" + str(__import__("os").getenv("PORT", 5000))

# سجل الأخطاء (stderr)
errorlog = "-"

# سجل الوصول (stdout)
accesslog = "-"

# مستوى السجلات
loglevel = "info"

# السماح بإعادة التشغيل التلقائي عند تغيير الكود (للمحلي فقط)
reload = False

# تقليل استهلاك الذاكرة عند البناء
preload_app = True

# اسم التطبيق (اختياري)
proc_name = "data-analysis-api"
