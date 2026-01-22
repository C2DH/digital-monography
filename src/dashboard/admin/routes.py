import flask

admin_bp = flask.Blueprint("admin", __name__)


# @admin_bp.route("/api/admin/hi", methods=["GET"])
# @admin_bp.route("/api/admin/hi/", methods=["GET"])
# def admin_hi() -> flask.Response:
#     slug = flask.request.args.get("slug", "None")


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if flask.request.method == "POST":
        # TODO: add login logic
        if authenticated:
            flask.session["logged_in"] = True
            flask.session["username"] = username
            next_url = flask.request.args.get("next") or "/"
            return flask.redirect(next_url)
        return flask.render_template("login.html", error="Invalid credentials")
    return flask.render_template("login.html")


@admin_bp.route("/logout")
def logout():
    flask.session.clear()
    return flask.redirect(flask.url_for("admin.login"))
