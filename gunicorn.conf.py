import os
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
workers = int(os.environ.get("GUNICORN_WORKERS", "3"))
timeout = 60
accesslog = "-"
errorlog = "-"
