import aws_lambda_wsgi
import flask


app = flask.Flask(__name__)
app.debug = True
app.secret_key = "FLASK_SECRET_KEY"


@app.route("/")
def index():
    return flask.render_template("index.html")


@app.route("/version")
def index():
    return {"version": "0.0.1"}


@app.route("/done")
def done():
    return flask.render_template("done.html")


def lambda_handler(event, context):
    return aws_lambda_wsgi.response(app, event, context)
