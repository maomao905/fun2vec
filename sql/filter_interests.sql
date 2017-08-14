SELECT description
FROM users
WHERE verified = 0
    AND description REGEXP '([ぁ-んァ-ヶー一-龠]{1,10}(、|,|/|\s|#|・)){2}'
