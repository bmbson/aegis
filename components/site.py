from flask import Flask, render_template
import os, secrets

APP=""
class Site:
    def __init__(self):
        base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/site/")
        staticf = os.path.join(base, "static")
        templatef = os.path.join(base, "templates")
        self.app = Flask(__name__, static_folder=staticf, template_folder = templatef)
        self.app.secret_key = secrets.token_hex()
        self.runsite()


    def runsite(self):

        @self.app.route("/")
        def index():
            return render_template("index.html")

        @self.app.route("/success.html")
        def success():
            # this is where you would do actual checks to see if the client included your jwt token
            return render_template("success.html")


        # uncomment if using wsgi
        #if __name__ == '__main__':
        # comment if using wsgi
        self.app.run('0.0.0.0', port=18443)

# uncomment if using wsgi
#if __name__ != "main":
#    Site()

