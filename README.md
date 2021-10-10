# Flaskr... continued
Flaskr (Flask tutorial) continued...  with homework

This repository pick up from where flask tutorial ([the Flaskr blog application](https://flask.palletsprojects.com/en/1.1.x/tutorial/) ) left up. You can find the original git repository [here](https://github.com/pallets/flask/tree/1.1.2/examples/tutorial)

At the end of the tutorial you're left with some "homework": suggestions to extend the blog application and improve your skills. 

In this repository I'll do my best to fullfil those suggestions and, at the same time, add some more features and change (improve ?) the look and feel of the application.
For the latest I'll use the popular framework **Boostrap (vers. 4)** to change the appearence of the blog.

Here's the list of Flask's team suggestions:

* A detail view to show a single post. Click a post’s title to go to its page.

* Like / unlike a post.

* Comments.

* Tags. Clicking a tag shows all the posts with that tag.

* A search box that filters the index page by name.

* Paged display. Only show 5 posts per page.

* Upload an image to go along with a post.

* Format posts using Markdown.

* An RSS feed of new posts.


And this is the list of my extensions:


* Truncate length of post in main view (for longer posts)

* Add a "discard" button in edit mode

* New appearance using Boostrap framework

* Extend user personal informations

* Add user avatar

* Deploy on serverless structure

For installation the same suggestion of Flask's team applies.

Install *(from the original Flask github repository)*
-------

**Be sure to use the same version of the code as the version of the docs
you're reading.** You probably want the latest tagged version, but the
default Git version is the master branch. ::

    # clone the repository
    $ git clone https://github.com/giuliodn/flaskr_continued
    $ cd flaskr_continued
    # checkout the correct version
    $ git tag  # shows the tagged versions
    $ git checkout latest-tag-found-above
    $ cd examples/tutorial

Create a virtualenv and activate it::

    $ python3 -m venv venv
    $ . venv/bin/activate

Or on Windows cmd::

    $ py -3 -m venv venv
    $ venv\Scripts\activate.bat

Install Flaskr::

    $ pip install -e .

Or if you are using the master branch, install Flask from source before
installing Flaskr::

    $ pip install -e ../..
    $ pip install -e .


Run
---

::

    $ export FLASK_APP=flaskr
    $ export FLASK_ENV=development
    $ flask init-db
    $ flask run

Or on Windows cmd::

    > set FLASK_APP=flaskr
    > set FLASK_ENV=development
    > flask init-db
    > flask run

Open http://127.0.0.1:5000 in a browser.


Test
----

::

    $ pip install '.[test]'
    $ pytest

Run with coverage report::

    $ coverage run -m pytest
    $ coverage report
    $ coverage html  # open htmlcov/index.html in a browser
