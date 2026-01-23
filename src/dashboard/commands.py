import click
import flask
import sqlmodel

from src._common.constants import UserRole
from src._common.models import User

try:
    from app import create_app
    from db import db_engine
except (ImportError, ModuleNotFoundError):
    from .app import create_app
    from .db import db_engine


app = create_app()


@click.command(name="create_superuser")
@click.argument("username")
@click.argument("password")
@flask.cli.with_appcontext
def create_superuser(username: str, password: str) -> None:
    user = User(username=username)
    user.set_password(password)
    user.role = UserRole.Admin

    try:
        with sqlmodel.Session(db_engine) as session:
            session.add(user)
            session.commit()
        click.echo(f"Superuser {username} created successfully.")
    except Exception as e:
        click.echo(f"Error creating superuser: {e}", err=True)


app.cli.add_command(create_superuser)
