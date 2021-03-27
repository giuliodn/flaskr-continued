-- Flaskr tutorial ...continued (by giuliodn)
-- Update schema.sql

DROP TABLE IF EXISTS comments;

CREATE TABLE IF NOT EXISTS comments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  post_id INTEGER NOT NULL,
  comment_body TEXT NOT NULL DEFAULT 0,
  comment_created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES user (id),
  FOREIGN KEY (post_id) REFERENCES post (id)
);
