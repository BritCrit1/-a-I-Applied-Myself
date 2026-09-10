import os

bind = "0.0.0.0:" + os.getenv("PORT", "8080")
workers = 2
threads = 4
timeout = 120
accesslog = "-"
errorlog = "-"
