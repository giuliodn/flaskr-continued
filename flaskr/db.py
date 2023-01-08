import sqlite3

import click
from flask import current_app
from flask import g
from flask.cli import with_appcontext

import markdown


def get_db():
    """Connect to the application's configured database. The connection
    is unique for each request and will be reused if this is called
    again.
    """
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    """If this request connected to the database, close the
    connection.
    """
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    """Clear existing data and create new tables."""
    db = get_db()

    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))


def update_db(filename):
    """Update database according to sql commands in filename"""
    db = get_db()

    with current_app.open_resource(filename) as f:
        db.executescript(f.read().decode("utf8"))


def add_markdown_support():
    """Add markdown support.
       Update database schema and markdown field"""
    db = get_db()

    with current_app.open_resource("update_markdown.sql") as f:
       db.executescript(f.read().decode("utf8"))

    posts = db.execute(
        "SELECT id, body FROM post"
    ).fetchall()

    for post in posts:
        html = markdown.markdown(post['body'])
        id = post['id']
        db.execute(
            "UPDATE post SET html = ? WHERE id = ?", (html, id)
        )
        db.commit()


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")


@click.command("update-db")
@click.argument("filename")
@with_appcontext
def update_db_command(filename):
    """Update existing db."""
    update_db(filename)
    click.echo("Database updated.")

@click.command("add-markdown")
@with_appcontext
def add_markdown_command():
    """Add markdown support"""
    add_markdown_support()
    click.echo("Markdown support added. Database updated")
    


def init_app(app):
    """Register database functions with the Flask app. This is called by
    the application factory.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(update_db_command)
    app.cli.add_command(add_markdown_command)
