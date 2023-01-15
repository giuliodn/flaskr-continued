import socket

from feedgen.feed import FeedGenerator
from flask import Flask, Response, send_from_directory


def get_ip_address():
    """Get current IP address.
    From https://stackoverflow.com/a/166589/379566
    """
    # s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s = socket.gethostbyname(socket.gethostname())
    # s.connect(("8.8.8.8", 80))
    print(s)
    return s

if __name__ == '__main__':
    ip = get_ip_address()
    SERVER_HOME = 'http://{}'.format(get_ip_address())
    print(ip)
    print(SERVER_HOME)