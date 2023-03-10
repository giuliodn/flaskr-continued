from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from flask import current_app
from flask import send_from_directory
from flask import Response
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
import os
from math import ceil
from uuid import uuid4
import markdown
from feedgen.feed import FeedGenerator
import socket
#from flaskr import feed

from flaskr.auth import login_required
from flaskr.db import get_db
from flaskr.feed import add_feed

bp = Blueprint("blog", __name__)

# Hardcoding posts per page
POSTS_PER_PAGE = 5

# Image upload
#UPLOAD_FOLDER = 'images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'tiff'}


@bp.route("/")
def index():
    """Show all the posts, most recent first."""

    print(request.base_url)
    # Reset previous searches
    session['search_string'] = ''
    session['user_search'] = ''

    db = get_db()

    # Count all pertinent posts
    total_posts = db.execute("SELECT COUNT(*) FROM POST").fetchone()[0]

    # Count all pages
    pages = ceil(total_posts / POSTS_PER_PAGE)

    # Page requested by user: page=1 if none requested
    page = int(request.args.get('page', default=1))
    
    # Check if page exceedes total pages
    # Should not be the case, but prevents misuse
    if page > pages:
        page = pages

    limit = POSTS_PER_PAGE
    offset = (page-1) * POSTS_PER_PAGE

    posts = db.execute(
        "SELECT p.id, title, image, body, html, created, author_id, username, likes, unlikes, nr_comments"
        " FROM post p JOIN user u ON p.author_id = u.id"
        " ORDER BY created DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    
    return render_template("blog/index.html", posts=posts, tag_id=None, page=page, pages=pages)


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
            "SELECT p.id, title, image, body, html, created, author_id, username, likes, unlikes, nr_comments"
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
        filename = request.args.get("filename")
        error = None

        if not title:
            error = "Title is required."

        # Parse tags
        # NOTE: this is a remainder for a more convenient parsing
        forbidden_chars = set('#[]()`?$%/\<>*')
        forbidden_chars_nicetxt = ' '.join(list(forbidden_chars))
        if any((c in forbidden_chars) for c in tags):
            error = "This characters %s are not allowed in tags, please remove them" % forbidden_chars_nicetxt
        
        if 'file' in request.files:
            image_file = request.files['file']
            print('image_file: %s' % image_file.filename)
            if image_file.filename == '' and not filename:
                filename = ''
            elif allowed_file(image_file.filename):
                filename = str(uuid4())
                image_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            elif not filename:
                error = "File extension not allowed"

        if error is not None:
            flash(error)
        else:
            html = markdown.markdown(body)
            db = get_db()
            # lastrowid gives the id of the newly inserted post 
            # which is needed to associate tags
            post_id= db.execute(
                "INSERT INTO post (title, image, body, html, author_id) VALUES (?, ?, ?, ?, ?)",
                (title, filename, body, html, g.user["id"]),
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

            # At last, update RSS feed

            post_address_final = '{}/show'.format(post_id)

            user = db.execute(
                "SELECT username FROM user WHERE id=?", (g.user['id'], ),
            ).fetchone()

            add_feed(post_address_final, title, user)



            return redirect(url_for("blog.index"))

    return render_template("blog/create.html")


@bp.route("/<int:id>/update_image", endpoint='update_image', methods=("POST", ))
@bp.route("/<int:id>/delete_image", endpoint='delete_image', methods=("POST", ))
@bp.route("/update_image", endpoint='update_image', methods=("POST", ))
@bp.route("/delete_image", endpoint='delete_image', methods=("POST", ))
@bp.route("/<int:id>/to_markdown", endpoint='to_markdown', methods=("POST", ))
@bp.route("/<int:id>/to_html", endpoint='to_html', methods=("POST", ))
@bp.route("/to_markdown", endpoint='to_markdown', methods=("POST", ))
@bp.route("/to_html", endpoint='to_html', methods=("POST", ))
@login_required
def update_while_create_or_update(id=None):
    """Update image while creating/editing post"""

    mode = request.args.get('mode')
    body = request.form['body']
    html = markdown.markdown(body)

    if 'editMode' in request.args:
        editMode = request.args.get('editMode')
    else:
        editMode = 'MD'

    if mode == 'update':
        post = get_post(id)

    if request.method == "POST":
        
        tags = request.form["tags"]
        error = None

        tags_string = tags

        if mode == 'create':
            # there's always a filename variable (thanks Jinja)
            filename = request.args.get('filename')
        elif mode == 'update':
            filename = post['image']


        # Manage endpoint='delete_image' to instantly delete the image
        # and continue editing
        if 'delete_image' in request.endpoint:
            # Create comma separated string of all the tags
            filename = ''

        # Update displayed image upon request
        if 'update_image' in request.endpoint:
            if 'file' in request.files:
                image_file = request.files['file']
                if image_file.filename != '':
                    if allowed_file(image_file.filename):
                        filename = str(uuid4())
                        image_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    else:
                        # There's some file selected but extension is not allowed
                        error = "File extension not allowed"

        # Preview html
        if 'to_html' in request.endpoint:
            editMode = 'html'
        
        # Back to markdown editmode
        if 'to_markdown' in request.endpoint:
            editMode = 'MD'

        if error is not None:
            flash(error)
        else:
            if mode == 'update':
                db = get_db()
                db.execute(
                    "UPDATE post SET image = ? WHERE id = ?", (filename, id)
                )
                db.commit()
                # Refresh post
                post = get_post(id)

        if mode == 'update':
            return render_template("blog/update.html", post=post, tags=tags_string, html=html, editMode=editMode)
        if mode == 'create':
            return render_template("blog/create.html", filename = filename, html=html, editMode=editMode)


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

        filename = post['image']
        if 'file' in request.files:
            image_file = request.files['file']
            if image_file.filename == '' and filename == '':
                filename = ''
            elif allowed_file(image_file.filename):
                filename = str(uuid4())
                image_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            elif image_file.filename != '':
                # There's some file selected but extension is not allowed
                error = "File extension not allowed"

        if error is not None:
            flash(error)
        else:
            html = markdown.markdown(body)
            db = get_db()
            db.execute(
                "UPDATE post SET title = ?, image = ?, body = ?, html = ? WHERE id = ?", (title, filename, body, html, id)
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
    post = get_post(id)
    db = get_db()

    # If any image file, delete it
    if post['image'] != '':
        os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], post['image']))

    # Delete the post
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
def show_tag(tag_id):
    """Show all the posts associated with tag_id.
    """
    db = get_db()
    print('test')

    # Count all pertinent posts
    total_posts = db.execute(
        "SELECT COUNT(*)"
        " FROM post p JOIN user u ON p.author_id = u.id"
        " JOIN tagsofposts t ON t.tag_id = ? AND t.post_id=p.id",
        (tag_id, ),
    ).fetchone()[0]

    # Count all pages
    pages = ceil(total_posts / POSTS_PER_PAGE)

    # Page requested by user: page=1 if none requested
    page = int(request.args.get('page', default=1))
    print(page)

    # Check if page exceedes total pages
    # Should not be the case, but prevents misuse
    if page > pages:
        page = pages

    limit = POSTS_PER_PAGE
    offset = (page-1) * POSTS_PER_PAGE

    posts = db.execute(
        "SELECT p.id, title, body, html, created, author_id, username, likes, unlikes, nr_comments"
        " FROM post p JOIN user u ON p.author_id = u.id"
        " JOIN tagsofposts t ON t.tag_id = ? AND t.post_id=p.id"
        " ORDER BY created DESC LIMIT ? OFFSET ?",
        (tag_id, limit, offset)
    ).fetchall()
    return render_template("blog/index.html", posts=posts, tag_id=tag_id, page=page, pages=pages)

@bp.route("/search", methods=("GET", "POST"))
def search():
    """Show all the posts corresponding to search"""

    if request.method == 'POST':
        search = request.form['searchbox']
        if search == '':
            # User reset search
            return redirect(url_for("blog.index"))
        # Save user input for later display
        session['user_search'] = search
        # Format search string to be used by SQL query
        search = search.replace('*', '%')
        search = search.replace(' ', '%')
        search = '%' + search + '%'
        search = search.replace(r'%%', '%')
        session['search_string'] = search
    else:
        # search = request.args.get('search', default=None)
        search = session['search_string']

    db = get_db()

    # Count all pertinent posts
    total_posts = db.execute(
        "SELECT COUNT(*)"
        " FROM post p JOIN user u ON author_id=u.id"
        " WHERE title LIKE ?", 
        (search, ),
    ).fetchone()[0]

    # Count all pages
    pages = ceil(total_posts / POSTS_PER_PAGE)

    # Page requested by user: page=1 if none requested
    page = int(request.args.get('page', default=1))

    # Check if page exceedes total pages
    # Should not be the case, but prevents misuse
    if page > pages:
        page = pages

    limit = POSTS_PER_PAGE
    offset = (page-1) * POSTS_PER_PAGE

    posts = db.execute(
        "SELECT p.id, title, image, body, html, created, author_id, username, likes, unlikes, nr_comments"
        " FROM post p JOIN user u ON author_id=u.id"
        " WHERE title LIKE ?"
        " ORDER BY created DESC LIMIT ? OFFSET ?",
        (search, limit, offset),
    ).fetchall()

    return render_template("blog/index.html", posts=posts, tag_id=None, page=page, pages=pages)

@bp.route("/uploaded_image/<filename>")
def uploaded_image(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'],
                               filename)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[-1].lower() in ALLOWED_EXTENSIONS


@bp.route("/favicon.ico")
def favicon():
    """ Render favicon if required"""

    return send_from_directory(current_app.static_folder, 'favicon.png')
