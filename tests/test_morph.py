from morph import extract_words
class TestMorph(object):
    def test_extract_words(self):
        test_cases = (
            # clean word replace
            ('ラ・サール高校', ['ラ・サール', '高校']),
            ('受験戦争', ['受験戦争']),
            ('iPhone7', ['iPhone']),
            # clean word exclude
            ('58キロ', []),
            ('6勝', []),
            ('１０万円', []),
            # new word
            ('お肉', ['お肉']),
            ('中日', ['中日ドラゴンズ']),
            ('鹿島アントラーズ', ['鹿島アントラーズ']),
            # close word
            ('アントラーズサポーター', ['鹿島アントラーズ']),
            ('E-Girls', ['E-girls']),
            ('マリーンズ', ['千葉ロッテマリーンズ']),
            # close word original
            ('J-ROCK', ['ロック']),
            ('イヌ', ['犬']),
            ('邦楽', ['J-POP']),
            ('#daihyo', ['サッカー日本代表']),
            # stop words
            ('フォロー返し', []),
            ('高', []),
            ('あれこれ', []),
            # valid genkei
            ('あれ', []),
            ('コメ', ['コメ']),
            ('Web', ['Web']),
        )

        for word, exp_words in test_cases:
            assert extract_words(word) == exp_words
