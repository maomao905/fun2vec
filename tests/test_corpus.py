import unittest
from corpus.corpus_base import BaseCorpus
from corpus.corpus_fun2vec import Fun2vecCorpus

class TestCorpus(unittest.TestCase):

    def test_find_separated_fun_words(self):
        """
        興味を抽出する正規表現テスト
        """
        test_cases = (
            (
                '脳内掃除として独り言をつぶやいてる会社員です。  好きなこと：酒、風呂、寝る。最近はブクマとして使ってるような･･･。\
                ここでの発言は私個人の意見であり、所属する組織を代表するものではありません。',
                ['酒', '風呂']
            ),
            (
                # 1文字
                'Lv3娘との日常生活/洋裁/ゲーム Steam&PS4/FX&株…極稀に雑談配信やゲーム配信やってます。最近はPS4版Divisionをプレイしています。',
                ['日常生活', '洋裁', 'ゲーム']
            ),
            (
                # stop words
                'FateGOありがとう。拡散性ＭＡは滅ぼしましたので乖離性で傭兵メインでやってます。艦これは、矢矧大鳳初風浦風あきつ丸くれ。あ、あと、絶望した。',
                ['絶望']
            ),
            (
                # 英語
                'ビール、箱根駅伝、体操競技、ingress@RES、自転車、ジム、イカ',
                ['ビール', '箱根駅伝', '体操競技', 'ingress', 'RES', '自転車', 'ジム', 'イカ']
            ),
            (
                # 記号(
                '根っこはAPH祖国島国。うたプリ（セシル）、刀剣（歌仙、蜂須賀）、文アル、FGO、シノアリス他。宝塚は子供の頃から。\
                リアルで話した事がある人にしか話しかけられないので無言フォローすみません。成人済。リフォロは不要です。検索避の為に通常は鍵かけてます。',
                ['CECIL', '刀剣', '歌仙', '蜂須賀', 'アル', 'FGO', 'シノ']
            ),
            (
                # 複数回
                '完全無欠のロケンローラー。黒帯。ロック、映画、漫画好き。八十八ヶ所巡礼狂い。漫画や音楽やテレビ、ドラマ、アニメ、映画のことから色々つぶやきます',
                ['ロック', '映画', '漫画', 'テレビ', 'ドラマ', 'アニメ', '映画']
            ),
            (
                # 原型と違う場合
                'ソーラーカー・西武・台湾・博覧会・TMN・聖飢魔II好き。風の王国PJ。秋田から八王子まで電気自動車で通勤中。',
                ['ソーラーカー', '埼玉西武ライオンズ', '博覧会', 'TMN', '聖飢魔II']
            ),
            (
                # max length
                'FC東京/千葉ロッテマリーンズ/チームスズキエクスター/バイク/自転車/自動車/鉄道/そこらへん界隈で広く浅く生きています。',
                ['FC東京', '千葉ロッテマリーンズ', 'チームスズキエクスター', 'バイク', '自転車', 'クルマ', '鉄道', '遍界']
            ),
            (
                # スペースあり
                '自由ソフトウェア, ロックンロール, ラジオ, PUNK',
                ['ソフトウェア', 'ロックンロール', 'ラジオ', 'PUNK']
            ),
            (
                'Apple / games / Ruby',
                ['Apple', 'games', 'Ruby']
            ),
            (
                'PHP / Ruby / Mobile / Finance / Marketing / K-POP / しまむら /  コマツ / 画像認識 / 機械学習 / 書き出し小説',
                ['PHP', 'Ruby', 'Mobile', 'Finance', 'Marketing', 'K-POP', 'しまむら', 'コマツ', '認識', '機械学習', '書き出し']
            ),
            (
                'Maker and agnostic. \nLove the Future, Internet, Energyful days.',
                ['Future', 'Internet', 'Energyful']
            ),
            (
                # 対応できていない例
                # 中に数字
                'VR/Unity3D/UE4/WebGL/Houdini/C4D',
                ['VR', 'Unity', '3D', 'UE', 'WebGL', 'Houdini', 'C4']
            ),
            (
                '自己完結型//読書//音楽//映画・海外ドラマ//ダンス//Barca･日ハム・SFジャイアンツ･浅田真央ちゃんファン//成人済//DC:superbat',
                ['自己完結', '読書', '音楽', '映画', '海外ドラマ', 'ダンス', 'Barca', '浅田真央', 'DC']
            ),
            (
                '太鼓の達人/スチールウール/かつぶしまん/低浮上/アイラ/ア/アイラ/アイラ/アイラ/アイラ/アイラ/アイラ/アイラ/アイラ/アイラ/アイラ/アイラ/アイラ',
                ['太鼓の達人', 'スチールウール', 'かつぶしまん', '浮上']
            ),
        )

        fc = Fun2vecCorpus()
        for text, expected_funs in test_cases:
            assert fc._Fun2vecCorpus__find_separated_fun_words(text) == expected_funs

    def test_relace_url(self):
        """
        urlを<URL>に置き換えする正規表現テスト
        """
        test_cases = (
            (
                'アニメ録画が趣味。最近DJはじめました。DJ記録→ https://mixcloud.com/sorshi/',
                'アニメ録画が趣味。最近DJはじめました。DJ記録→ <URL>'
            ),
            (
                'アニメ録画が趣味。最近DJはじめました。DJ記録→ ftp://mixcloud.com/sorshi/',
                'アニメ録画が趣味。最近DJはじめました。DJ記録→ <URL>'
            ),
            (
                # 複数
                'ガールズモード→ https://t.co/e0BHzR194g ミラクルニキ→ https://t.co/EjgsSnMpzc',
                'ガールズモード→ <URL> ミラクルニキ→ <URL>'
            ),
            (
                # ftp
                '「Peak to Peak」についてはサークルサイト(http://ptp.cru-jp.com)をご覧下さい',
                '「Peak to Peak」についてはサークルサイト(<URL>をご覧下さい'
            ),
            (
                '「Peak to Peak」についてはサークルサイト(http://mixi.jp/show_friend.pl?id=6)をご覧下さい',
                '「Peak to Peak」についてはサークルサイト(<URL>をご覧下さい'
            ),
            (
                # 記号()
                "マストドン https://mstdn.jp/<()'\"*hanayuu*-_;#!?*=@>",
                'マストドン <URL>'
            ),
        )

        for case in test_cases:
            text, replace_text = case
            assert BaseCorpus._replace_url(text) == replace_text
