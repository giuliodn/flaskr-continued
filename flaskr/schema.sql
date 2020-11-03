-- Flaskr tutorial ...continued (by giuliodn)
-- Initialize the database.
-- Drop any existing data and create empty tables.

DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS likes;
DROP TABLE IF EXISTS comments;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE post (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  title TEXT NOT NULL DEFAULT 0,
  body TEXT NOT NULL DEFAULT 0,
  likes INTEGER,
  unlikes INTEGER,
  nr_comments INTEGER DEFAULT 0,
  FOREIGN KEY (author_id) REFERENCES user (id)
);

CREATE TABLE likes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  post_id INTEGER NOT NULL,
  likes BOOLEAN,
  FOREIGN KEY (user_id) REFERENCES user (id),
  FOREIGN KEY (post_id) REFERENCES post (id)
);

CREATE TABLE IF NOT EXISTS comments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  post_id INTEGER NOT NULL,
  comment_body TEXT NOT NULL DEFAULT 0,
  comment_datetime DATETIME DEFAULT,
  FOREIGN KEY (user_id) REFERENCES user (id),
  FOREIGN KEY (post_id) REFERENCES post (id)
);
