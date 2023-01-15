from feedgen.feed import FeedGenerator
from flask import Blueprint, request, current_app, Response, url_for


bp = Blueprint("feed", __name__, url_prefix="/feed")


def init_feed():
    """ Initialise feed generator
    """

    fg = FeedGenerator()
    fg.id(request.host_url)
    fg.title('Flaskr tutorial')
    fg.author( {'name':'giuliodn','email':'nope@example.de'} )
    fg.link( href=request.host_url, rel='alternate' )
    fg.image(url=url_for('static', filename='favicon.png'))
    fg.subtitle('Flask tutorial ...continued')
    fg.language('en')

    return fg


def add_feed(final_address, title, author):
    """ Add feed """

    if current_app.feed is None:
        current_app.feed = init_feed()
    
    feed_id = '{}{}'.format(request.host_url, final_address)
    
    fe = current_app.feed.add_entry()
    fe.id(feed_id)
    fe.title(title)
    fe.author({'name': author})
    fe.link(href=feed_id)


@bp.route('/index.xml')
def get_feed():

    # Initialise RSS feed if it doesn't exist
    if current_app.feed is None:
        current_app.feed = init_feed()

    return Response(current_app.feed.rss_str(), mimetype='application/rss+xml')


