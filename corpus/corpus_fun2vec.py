from corpus.corpus_base import BaseCorpus
import re

class Fun2vecCorpus(BaseCorpus):
    __REGEX_FUN_PREV = re.compile(r'(?P<fun>{char}?)((する)?こと)?(に(興味|はまって)|(を|の?が)趣味|を(こよなく)?愛する|が?(?:大?好き|大好物))'.format(char=REGEX_CHAR))
    __REGEX_HOBBY_FOLLOW = re.compile(r'趣味(は|で^す|：|:|→|⇒|\=)\s?(?P<fun>{char})'.format(char=REGEX_CHAR))
    __REGEX_SEP_FUNS = re.compile(r'({char}(?P<sep>とか|やら|、|,\s?|，|\s?/\s?|#|・|\s?／\s?|//|\|)(?:{char}(?P=sep))+{char})' \
        .format(char=REGEX_CHAR), re.IGNORECASE)
    # REGEX_INTEREST_FOLLOW = re.compile(r'興味(は|：|:|→|⇒|\=|が?(有|あ)る(事|こと|も?の)は)\s?(?P<fun>{char})'.format(char=REGEX_CHAR))
    __REGEX_AND_FUN = re.compile(r'((%s(?P<sep>とか?)){3,}%s)' % (REGEX_CHAR, REGEX_CHAR))

    def _extract_funs():
        """
        下記のような区切りがあるを興味・関心とみなし取得する。
        ex) 最近は、三浦半島探検/ヒリゾ/伊豆/箱根/道志/長野上田/ドライブ/秘湯が好きです。
        return: [['三浦半島探検','ヒリゾ', '伊豆'], ['音楽', '落語', '旅']]
        """
        session = create_session()
        logger.info('Running query...')
        users_with_funs = []
        for idx, user in enumerate(session.query(User).filter(User.verified==0, User.funs == None).yield_per(500), 1):
            profile = user.description

            users_with_funs = []
            # url置き換え
            profile = self._replace_url(profile)

            funs.extend(_find_fun_words(profile))
            funs.extend(_find_separated_fun_words(profile))
            funs = self.__word.preprocess(profile)
            # 興味が２つ以上の場合だけ
            if len(funs) >= 2:
                # insert funs
                user.funs = '/'.join(funs)
                users_with_funs.append(user)

            if idx % 1000 == 0:
                _save_funs(session, users_with_funs)
                logger.info('Finished {} profiles'.format(idx))

        return user_funs

    def _find_separated_fun_words(text):
        """
        正規表現で「三浦半島探検/ヒリゾ/伊豆が好きです。」の部分だけを取得
        形態素解析で興味を抽出
        return: ['三浦半島探検','ヒリゾ','伊豆']
        """
        fun_words = []

        ma = REGEX_SEP_FUNS.search(text)
        if ma is None:
            return []

        # funs: ['三浦半島探検', 'ヒリゾ', '伊豆が好きです。']
        funs = ma.group().split(ma.group('sep'))

        for idx, fun in enumerate(funs):
            words = extract_words(fun)
            if len(words) > 0:
                if idx == 0:
                    # 区切られた最初の文はどこから最初かわからないので、一番最後だけ取得
                    first_word = words[-1]
                    fun_words.extend([first_word])
                elif idx+1 == len(funs):
                    # 区切られた最後の文はどこまでかわからないので、一番先頭だけ取得
                    # 「伊豆が好きです。」=> 伊豆, 好き => 伊豆のみ抽出
                    last_word = words[0]
                    fun_words.extend([last_word])
                    try:
                        # 残りのtext
                        next_start_idx = text.index(fun) + fun.index(last_word) + len(last_word)
                        next_text = text[next_start_idx:]
                    except ValueError:
                        # last_wordが原型と異なる場合
                        next_text = text[ma.end():]
                    # 残りの文を再起的に見る
                    fun_words.extend(_find_separated_fun_words(next_text))
                else:
                    fun_words.extend(words)
            else:
                # 区切られた最後の文で何も取得できなかったとき
                if idx+1 == len(funs):
                    next_text = text[ma.end():]
                    fun_words.extend(_find_separated_fun_words(next_text))

        return fun_words

    def _save_funs(session, users):
        session.bulk_save_objects(users)
        session.commit()
