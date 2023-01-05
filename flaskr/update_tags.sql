-- Flaskr tutorial ...continued (by giuliodn)
-- Update schema.sql

CREATE TABLE IF NOT EXISTS tags (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tag TEXT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS tagsofposts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tag_id INTEGER NOT NULL,
  post_id INTEGER NOT NULL,
  FOREIGN KEY (tag_id) REFERENCES tags (id),
  FOREIGN KEY (post_id) REFERENCES post (id)
);