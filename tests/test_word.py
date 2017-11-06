from word import Word
from util import load_config

class TestWord(object):
    def test_clean_word(self):
        test_cases_replace = (
            ('慶応大学', '大学'),
            ('朝日新聞', '新聞'),
            ('JR東日本', 'JR'),
            ('高校受験', '受験'),
            ('iPhone7', 'iPhone'),
        )

        test_cases_exclude = (
            '1日目',
            '２日目',
            '三日目',
            '1年生',
            '2013年',
            '1984年生まれ',
            '6月',
            '4人',
            '鹿児島出身',
            '鹿児島県',
            '58キロ',
            'ごめんなさい。',
            '要注意',
            '1万円',
            '０円',
            '2期生',
        )

        w = Word()
        for word, rep_word in test_cases_replace:
            assert w.preprocess(word)[0] == rep_word

        for word in test_cases_exclude:
            assert len(w.preprocess(word)) == 0

    def test_stop_words(self):
        file_config = load_config('file')
        with open(file_config['word']['stop_words']) as f:
            stop_words = frozenset(f.read().rstrip().split('\n'))

        w = Word()
        for word in stop_words:
            assert len(w.preprocess(word)) == 0

    def test_valid(self):
        test_cases = (
            # filter pos
            ('沖縄', []),
            ('走る', []),
            # valid lexeme
            ('あれ', []),
            ('コメ', ['コメ']),
            ('Web', ['Web']),
        )

        w = Word()
        for word, rep_word in test_cases:
            assert w.preprocess(word) == rep_word
