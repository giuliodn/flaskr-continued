-- Flaskr tutorial ...continued (by giuliodn)
-- Update schema.sql


ALTER TABLE post ADD COLUMN likes INTEGER DEFAULT 0;
ALTER TABLE post ADD COLUMN unlikes INTEGER DEFAULT 0;


CREATE TABLE IF NOT EXISTS likes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  post_id INTEGER NOT NULL,
  likes BOOLEAN,
  FOREIGN KEY (user_id) REFERENCES user (id),
  FOREIGN KEY (post_id) REFERENCES post (id)
);
