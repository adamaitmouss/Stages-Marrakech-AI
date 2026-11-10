import os

bind = f"0.0.0.0:{int(os.environ.get('PORT', '8000'))}"
workers = int(os.environ.get('WEB_CONCURRENCY', '2'))
threads = int(os.environ.get('AUTH_THREADS', '4'))
timeout = 60
accesslog = '-'
errorlog = '-'
capture_output = True
preload_app = False
