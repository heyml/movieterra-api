import os
from werkzeug.contrib.fixers import ProxyFix

from movieterra import app
from movieterra.routes import *

app.wsgi_app = ProxyFix(app.wsgi_app)
port = int(os.getenv('PORT', 5000))

if __name__ == "__main__":
#    set_scheduler(logger)
    app.run(host = '0.0.0.0',port = port,threaded = True)
