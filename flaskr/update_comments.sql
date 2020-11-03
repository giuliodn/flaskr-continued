-- Flaskr tutorial ...continued (by giuliodn)
-- Update schema.sql


ALTER TABLE post ADD COLUMN nr_comments INTEGER DEFAULT 0;

CREATE TABLE IF NOT EXISTS comments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  post_id INTEGER NOT NULL,
  comment_body TEXT NOT NULL DEFAULT 0,
  comment_datetime DATETIME DEFAULT,
  FOREIGN KEY (user_id) REFERENCES user (id),
  FOREIGN KEY (post_id) REFERENCES post (id)
);
