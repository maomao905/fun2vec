from clean_word import clean
class TestCleanWord(object):
    def test_clean(self):
        test_cases_replace = (
            ('ラ・サール高校', '高校'),
            ('ラ・サール高校生', 'ラ・サール高校生'),
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
            '鹿児島出身',
            '鹿児島県',
            '58キロ',
            'ごめんなさい。',
            '決定事項',
            '要注意',
            '1万円',
            '０円',
        )

        for word, rep_word in test_cases_replace:
            assert clean(word) == rep_word

        for word in test_cases_exclude:
            assert clean(word) == None
