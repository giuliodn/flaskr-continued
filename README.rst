# Flaskr... continued
=====================

**Flaskr (Flask tutorial) continued...  with homework.**

This repository pick up from where flask tutorial (`the Flaskr blog application`_) left up. You can find the original git repository here_. 

.. _here: https://github.com/pallets/flask/tree/1.1.2/examples/tutorial
.. _`the Flaskr blog application`: https://flask.palletsprojects.com/en/1.1.x/tutorial/

At the end of the tutorial you're left with some "homework": suggestions to extend the blog application and improve your skills. 

In this repository I'll do my best to fullfil those suggestions:

* A detail view to show a single post. Click a post’s title to go to its page.

* Like / unlike a post.

* Comments.

* Tags. Clicking a tag shows all the posts with that tag.

* A search box that filters the index page by name.

* Paged display. Only show 5 posts per page.

* Upload an image to go along with a post.

* Format posts using Markdown.

* An RSS feed of new posts.

This is an accompagnatory repository to a series of Medium_ articles explaining the changes step by step.

.. _Medium: https://medium.com/

You can find articles here:

* `Flaskr tutorial …continued (Part 1)`_: a detail view to show a single post and like / unlike a post.

.. _`Flaskr tutorial …continued (Part 1)`: https://medium.com/@giuliodn/flaskr-tutorial-continued-part-1-23daa764fa72

* `Flaskr tutorial …continued (Part 2)`_: adding comments to a post.

.. _`Flaskr tutorial …continued (Part 2)`: https://medium.com/@giuliodn/flaskr-tutorial-continued-part-2-71052bcb0a9a

For installation the same suggestion of Flask's team applies.

Install *(almost from the original Flask github repository)*
-------

**Be sure to use the same version of the code as the version of the docs
you're reading.** You probably want the latest tagged version, but the
default Git version is the master branch. ::

    # clone the repository
    $ git clone https://github.com/giuliodn/flaskr_continued
    $ cd flaskr-continued
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
    $ export FLASK_DEBUG=1
    $ flask --app flaskr init-db
    $ flask --app flaskr run --debug

Or on Windows cmd::

    > set FLASK_APP=flaskr
    > set FLASK_DEBUG=1
    > flask --app flaskr init-db
    > flask --app flaskr run --debug

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
