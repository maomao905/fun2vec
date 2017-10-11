SELECT
  users.id,
  users.screen_name
FROM users
LEFT JOIN friends
  ON users.id = friends.user_id
WHERE
  friends.user_id IS NULL
AND
  users.verified = 0
AND
  users.friends_count > 0
LIMIT 15
