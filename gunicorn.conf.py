# Configuración de Gunicorn para EnerVirgil
import os

# Configuración del servidor
bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"
workers = int(os.environ.get('WEB_CONCURRENCY', 1))
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2

# Configuración de logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Configuración de proceso
preload_app = True
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None

# Configuración SSL (para HTTPS)
keyfile = None
certfile = None