from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint("blog", __name__)


@bp.route("/")
def index():
    """Show all the posts, most recent first."""
    db = get_db()
    posts = db.execute(
        "SELECT p.id, title, body, created, author_id, username, likes, unlikes, nr_comments"
        " FROM post p JOIN user u ON p.author_id = u.id"
        " ORDER BY created DESC"
    ).fetchall()
    
    return render_template("blog/index.html", posts=posts)


def get_post(id, check_author=True):
    """Get a post and its author by id.

    Checks that the id exists and optionally that the current user is
    the author.

    :param id: id of post to get
    :param check_author: require the current user to be the author
    :return: the post with author information
    :raise 404: if a post with the given id doesn't exist
    :raise 403: if the current user isn't the author
    """
    post = (
        get_db()
        .execute(
            "SELECT p.id, title, body, created, author_id, username, likes, unlikes, nr_comments"
            " FROM post p JOIN user u ON p.author_id = u.id"
            " WHERE p.id = ?",
            (id,),
        )
        .fetchone()
    )

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post["author_id"] != g.user["id"]:
        abort(403)

    return post


def get_comments(post_id, comment_id=None):
    """Get comments to a post.

    :param id: id of post to get comments for
    :comment id: id of a single comment to return
    :return: the comments with author and date information
    :return: one comment with author and date information if comment_id is not None
    :return: None if there're no comments
    """
    if comment_id == None:
        # comment_id not specified: fetch all of them
        comments = (
            get_db()
            .execute(
                "SELECT c.id, comment_body, comment_created, u.username, c.user_id"
                " FROM comments c JOIN user u ON c.user_id = u.id"
                " WHERE post_id = ?",
                (post_id,),
            )
            .fetchall()
        )
    else:
        # Return just one comment
        comments = (
            get_db()
            .execute(
                "SELECT c.id, comment_body, comment_created, u.username, c.user_id"
                " FROM comments c JOIN user u ON c.user_id = u.id"
                " WHERE post_id = ? AND c.id = ?",
                (post_id, comment_id),
            )
            .fetchone()
        )

    return comments

def get_tags(post_id):
    """Get tags of a post.

    :param post_id: id of post to get tags for
    :return: the tags of post_id
    :return: None if there're no tags
    """
    tags = (
        get_db()
        .execute(
            "SELECT tags.id, tags.tag"
            " FROM tags JOIN tagsofposts ON tags.id = tagsofposts.tag_id"
            " WHERE post_id = ?",
            (post_id, ),
        )
        .fetchall()
    )

    return tags


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    """Create a new post for the current user."""
    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        tags = request.form["tags"]
        error = None

        if not title:
            error = "Title is required."

        # Parse tags
        # NOTE: this is a remainder for a more convenient parsing
        forbidden_chars = set('#[]()`?$%/\<>*')
        forbidden_chars_nicetxt = ' '.join(list(forbidden_chars))
        if any((c in forbidden_chars) for c in tags):
            error = "This characters %s are not allowed in tags, please remove them" % forbidden_chars_nicetxt

        if error is not None:
            flash(error)
        else:
            db = get_db()
            # lastrowid gives the id of the newly inserted post 
            # which is needed to associate tags
            post_id= db.execute(
                "INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)",
                (title, body, g.user["id"]),
            ).lastrowid
            db.commit()

            # turn tags to list and strip whitespaces
            tags = tags.split(',')
            tags = [x.strip() for x in tags]
            print(tags)

            for tag in tags:
                # Check if tag is in database
                tag_row = db.execute(
                    "SELECT id FROM tags WHERE tag=?", (tag,),
                ).fetchone()
                if tag_row is None:
                    # Tag not in the database, we need to insert it
                    tag_id=db.execute(
                        "INSERT INTO tags (tag) VALUES (?)",
                        (tag,),
                    ).lastrowid
                    db.commit()
                else:
                    # If tag_row is not None then 'id' is inside it
                    tag_id = tag_row['id']
                # Now we can associate tag to post
                db.execute(
                    "INSERT INTO tagsofposts (tag_id, post_id) VALUES (?,?)",
                    (tag_id, post_id),
                )
                db.commit()

            return redirect(url_for("blog.index"))

    return render_template("blog/create.html")


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    """Update a post if the current user is the author."""
    post = get_post(id)
    tags_of_post = get_tags(id)

    # Create a list of the tags of the post
    tag_list = []
    for tag in tags_of_post:
        tag_list.append(tag['tag'])

    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        tags = request.form["tags"]
        error = None

        if not title:
            error = "Title is required."

        # Parse tags
        # NOTE: this is a remainder for a more convenient parsing
        forbidden_chars = set('#[]()`?$%/\<>*')
        forbidden_chars_nicetxt = ' '.join(list(forbidden_chars))
        if any((c in forbidden_chars) for c in tags):
            error = "This characters %s are not allowed in tags, please remove them" % forbidden_chars_nicetxt

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE post SET title = ?, body = ? WHERE id = ?", (title, body, id)
            )
            db.commit()

            # turn tags to list and strip whitespaces
            tags = tags.split(',')
            tags = [x.strip() for x in tags]

            for tag in tags:
                # Check if tag is in database
                tag_row = db.execute(
                    "SELECT id FROM tags WHERE tag=?", (tag,),
                ).fetchone()
                if tag_row is None:
                    # Tag not in the database, we need to insert it
                    tag_id=db.execute(
                        "INSERT INTO tags (tag) VALUES (?)",
                        (tag,),
                    ).lastrowid
                    db.commit()
                else:
                    # If tag_row is not None then 'id' is inside it
                    tag_id = tag_row['id']

                # We must check if tag is already associated with post.
                if tag not in tag_list:
                    # tag not previously associated
                    db.execute(
                        "INSERT INTO tagsofposts (tag_id, post_id) VALUES (?,?)",
                        (tag_id, id),
                    )
                    db.commit()
                else:
                    # remove tag from tag_list to check if user
                    # deleted some tag 
                    tag_list.remove(tag)

            if len(tag_list) != 0:
                # user removed some tags: break connection to post
                for tag in tag_list:
                    # first we need tag_id
                    tag_id = db.execute("SELECT id FROM tags WHERE tag = ?", (tag, )).fetchone()
                    tag_id = tag_id['id']
                    db.commit()
                    # then we break association
                    db.execute("DELETE FROM tagsofposts WHERE post_id = ? AND tag_id = ?", (id, tag_id),)
                    db.commit()

            return redirect(url_for("blog.index"))

    # Create comma separated string of all the tags
    tags_string = ', '.join(tag_list)

    return render_template("blog/update.html", post=post, tags=tags_string)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    """Delete a post.

    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    get_post(id)
    db = get_db()
    db.execute("DELETE FROM post WHERE id = ?", (id,))
    db.execute("DELETE FROM tagsofposts WHERE post_id = ?", (id, ))
    db.commit()
    return redirect(url_for("blog.index"))


@bp.route("/<int:id>/show", methods=["GET", "POST"])
def show(id):
    """Show a post no matter who the author is"""
    post = get_post(id, check_author=False)
    comments = get_comments(id)
    tags = get_tags(id)

    if request.method == "POST":
        # The form has a comment to save
        comment_body = request.form["body"]
        error = None

        if not comment_body:
            error = "No comment to send."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO comments (comment_body, post_id, user_id) VALUES (?, ?, ?)",
                (comment_body, id, g.user["id"]),
            )
            # Update the number of comments to the post
            db.execute("UPDATE post SET nr_comments=nr_comments+1 WHERE id=?", (id,))
            db.commit()

        return redirect(url_for("blog.show", id=id))

    # The method is "GET": just show the page
    return render_template("blog/show.html", post=post, comments=comments, tags=tags)


@bp.route("/<int:id>/show_like", endpoint='show_like')
@bp.route("/<int:id>/like")
@login_required
def like(id):
    """ Like a post """
    post = get_post(id, check_author=False)
    user_id = session.get("user_id")
    db=get_db()

    # Check if user already likes this post
    likes = (
        get_db()
        .execute(
            "SELECT likes FROM likes WHERE user_id=? AND post_id=?", (user_id, id),
        )
        .fetchone()
    )

    if likes is not None and likes['likes'] != 0:
        # User already likes this post; just tell him and do nothing
        flash("You already like this post!")
    elif likes is not None and likes['likes'] == 0:
        # User didn't like this post before. Remove his preference from
        # likes table and decrement unlike from post
        db.execute("DELETE FROM likes"
                   " WHERE user_id=? AND post_id=?", (user_id, id))
        db.execute("UPDATE post SET unlikes=unlikes-1 WHERE id=?", (id,))
        db.commit()
        flash("You did not like this post before. Now you're neutral on this post")
    else:
        # Add preference of user for this post (likes=1), and add a like to the post
        db.execute("INSERT INTO likes (user_id, post_id, likes)"
                   " VALUES (?, ?, ?)", (user_id, id, 1))
        db.execute("UPDATE post SET likes=likes+1 WHERE id=?", (id,))
        db.commit()

    print(request.endpoint)

    if 'show_like' in request.endpoint:
        return redirect(url_for("blog.get_show", id=id))
    else:
        return redirect(url_for("blog.index"))

@bp.route("/<int:id>/show_unlike", endpoint='show_unlike')
@bp.route("/<int:id>/unlike")
@login_required
def unlike(id):
    """ Unlike a post """
    post = get_post(id, check_author=False)
    user_id = session.get("user_id")
    db=get_db()

    # Check if user already likes this post
    likes = (
        get_db()
        .execute(
            "SELECT likes FROM likes WHERE user_id=? AND post_id=?", (user_id, id),
        )
        .fetchone()
    )

    if likes is not None and likes['likes'] == 0:
        # User already doesn't like this post; just tell him and do nothing
        flash("You already don't like this post!")
    elif likes is not None and likes['likes'] != 0:
        # User did like this post before. Remove his preference from
        # likes table and decrement like from post
        db.execute("DELETE FROM likes"
                   " WHERE user_id=? AND post_id=?", (user_id, id))
        db.execute("UPDATE post SET likes=likes-1 WHERE id=?", (id,))
        db.commit()
        flash("You did like this post before. Now you're neutral on this post")
    else:
        # Add preference of user for this post (likes=1), and add a like to the post
        db.execute("INSERT INTO likes (user_id, post_id, likes)"
                   " VALUES (?, ?, ?)", (user_id, id, 0))
        db.execute("UPDATE post SET unlikes=unlikes+1 WHERE id=?", (id,))
        db.commit()

    if 'show_unlike' in request.endpoint:
        return redirect(url_for("blog.get_show", id=id))
    else:
        return redirect(url_for("blog.index"))

@bp.route("/<int:id>/comment_update", methods=("GET", "POST"))
@login_required
def comment_update(id):
    """Update a comment"""
    post = get_post(id, check_author=False)
    comment_id = request.args.get('comment_id')
    comment = get_comments(id, comment_id)

    # Prevent comment changes from others than author
    if comment["user_id"] != g.user["id"]:
        abort(403)

    if request.method == "GET":
        return render_template("blog/update_comment.html", post=post, comments=comment)

    if request.method == "POST":
        comment_body = request.form["body"]
        error = None

        if not comment_body:
            error = "Comment is empty, consider deleting your comment"

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE comments SET comment_body=? WHERE id=?",
                (comment_body, comment_id),
            )
            db.commit()

        # if user is updating comment he can only come from blog/show
        return redirect(url_for("blog.show", id=id))


@bp.route("/<int:id>/comment_delete", methods=("GET",))
@login_required
def comment_delete(id):
    """Delete a comment.

    Ensures that the comment exists and that the logged in user is the
    author of the comment.
    """
    comment_id = request.args.get('comment_id')
    # The following is required to check the comment author and logged in user are the same
    comment = get_comments(id, comment_id)

    # Prevent user to delete if he's not the author
    if comment["user_id"] != g.user["id"]:
        abort(403)

    #get_post(id)
    db = get_db()
    db.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
    db.execute("UPDATE post SET nr_comments=nr_comments-1 WHERE id=?", (id,))
    db.commit()

    return redirect(url_for("blog.show", id=id))


@bp.route("/<int:tag_id>/show_tag", methods=("GET",))
@login_required
def show_tag(tag_id):
    """Show all the posts associated with tag_id.
    """
    db = get_db()
    posts = db.execute(
        "SELECT p.id, title, body, created, author_id, username, likes, unlikes, nr_comments"
        " FROM post p JOIN user u ON p.author_id = u.id"
        " JOIN tagsofposts t ON t.tag_id = ? AND t.post_id=p.id"
        " ORDER BY created DESC",
        (tag_id, )
    ).fetchall()
    return render_template("blog/index.html", posts=posts)

@bp.route("/search", methods=("POST",))
def search():
    """Show all the posts corresponding to search"""

    search = request.form['searchbox']
    search = search.replace('*', '%')
    search = search.replace(' ', '%')
    search = '%' + search + '%'
    search = search.replace(r'%%', '%')

    db = get_db()
    posts = db.execute(
        "SELECT p.id, title, body, created, author_id, username, likes, unlikes, nr_comments"
        " FROM post p JOIN user u ON author_id=u.id"
        " WHERE title LIKE ?"
        " ORDER BY created DESC",
        (search, ),
    ).fetchall()
    
    return render_template("blog/index.html", posts=posts)

