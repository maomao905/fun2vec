import unittest
from corpus import _find_fun_part, _replace_url, _invalid_profile

class TestCorpus(unittest.TestCase):

    def test_find_fun_part(self):
        TEXT1 = '脳内掃除として独り言をつぶやいてる会社員です。  好きなこと：酒、風呂、寝る。最近はブクマとして使ってるような･･･。ここでの発言は私個人の意見であり、所属する組織を代表するものではありません。'
        TEXT2 = 'Lv3娘との日常生活/洋裁/ゲーム Steam&PS4/FX&株…極稀に雑談配信やゲーム配信やってます。最近はPS4版Divisionをプレイしています。'
        TEXT3 = 'FateGOありがとう。拡散性ＭＡは滅ぼしましたので乖離性で傭兵メインでやってます。艦これは、矢矧大鳳初風浦風あきつ丸くれ。あ、あと、絶望した。'
        TEXT4 = 'ビール、箱根駅伝、体操競技、ingress@RES、自転車、ジム、イカ'
        TEXT5 = '根っこはAPH祖国島国。うたプリ（セシル）、刀剣（歌仙、蜂須賀）、文アル、FGO、シノアリス他。宝塚は子供の頃から。リアルで話した事がある人にしか話しかけられないので無言フォローすみません。成人済。リフォロは不要です。検索避の為に通常は鍵かけてます。'
        TEXT6 = '完全無欠のロケンローラー。黒帯。ロック、映画、漫画好き。八十八ヶ所巡礼狂い。漫画や音楽やテレビ、ドラマ、アニメ、映画のことから色々つぶやきます'
        TEXT7 = 'ソーラーカー・西武・台湾・博覧会・TMN・聖飢魔II好き。風の王国PJ。秋田から八王子まで電気自動車で通勤中。'
        TEXT8 = 'FC東京/千葉ロッテマリーンズ/チームスズキエクスター/バイク/自転車/自動車/鉄道/そこらへん界隈で広く浅く生きています。'
        TEXT9 = '自由ソフトウェア, ロックンロール, ラジオ, PUNK'
        TEXT10 = 'Apple / games / Ruby'
        TEXT11 = ' PHP / Ruby / Mobile / Finance / Marketing / K-POP / しまむら /  コマツ / 画像認識 / 機械学習 / 書き出し小説'
        TEXT12 = 'Maker and agnostic. \nLove the Future, Internet, Energyful days.'
        TEXT13 = 'VR/Unity3D/UE4/WebGL/Houdini/C4D'
        TEXT14 = '自己完結型//読書//音楽//映画・海外ドラマ//ダンス//Barca･日ハム・SFジャイアンツ･浅田真央ちゃんファン//成人済//DC:superbat'
        """
        興味を抽出する正規表現テスト
        """
        self.assertCountEqual(_find_fun_part(TEXT14), ['自己完結','読書','音楽','映画','海外ドラマ','ダンス','ファン','成人','済','DC'])
        self.assertCountEqual(_find_fun_part(TEXT1), ['酒', '風呂'])
        # 1文字
        self.assertCountEqual(_find_fun_part(TEXT2), ['洋裁', 'ゲーム', '日常生活'])
        # stop words
        self.assertCountEqual(_find_fun_part(TEXT3), ['絶望'])
        # 英語
        self.assertCountEqual(_find_fun_part(TEXT4), ['ビール', '箱根駅伝', '体操競技', '自転車', 'ジム', 'イカ'])
        self.assertCountEqual(_find_fun_part(TEXT10), ['Apple', 'Ruby'])
        # 記号()
        self.assertCountEqual(_find_fun_part(TEXT5), ['歌仙', 'CECIL', '文', '蜂須賀', 'シノ', 'アル', '刀剣'])
        # # 複数回
        self.assertCountEqual(_find_fun_part(TEXT6), ['ロック', '映画', '漫画', 'テレビ', 'ドラマ', 'アニメ'])
        # 原型と違う場合
        self.assertCountEqual(_find_fun_part(TEXT7), ['ソーラーカー', '西武', '台湾', '博覧会', '聖飢魔II', 'TMN'])
        # max length
        self.assertCountEqual(_find_fun_part(TEXT8), ['千葉ロッテマリーンズ','FC東京','自転車','鉄道','自動車','遍界', 'バイク'])
        # スペースあり
        self.assertCountEqual(_find_fun_part(TEXT9), ['ソフトウェア', 'ロックンロール', 'ラジオ', 'PUNK'])
        self.assertCountEqual(_find_fun_part(TEXT11), ['コマツ', 'Ruby', 'PHP', '書き出し', '認識', '機械学習', 'K-POP', 'しまむら'])
        self.assertCountEqual(_find_fun_part(TEXT12), ['Internet'])

        # 対応できていない例
        # 中に数字
        self.assertCountEqual(_find_fun_part(TEXT13), ['WebGL'])


    def test_relace_url(self):
        """
        urlを<URL>に置き換えする正規表現テスト
        """
        self.assertEqual(_replace_url('アニメ録画が趣味。最近DJはじめました。DJ記録→ https://mixcloud.com/sorshi/'), 'アニメ録画が趣味。最近DJはじめました。DJ記録→ <URL>')
        # ftp
        self.assertEqual(_replace_url('アニメ録画が趣味。最近DJはじめました。DJ記録→ ftp://mixcloud.com/sorshi/'), 'アニメ録画が趣味。最近DJはじめました。DJ記録→ <URL>')
        # 複数
        self.assertEqual(_replace_url('ガールズモード→ https://t.co/e0BHzR194g ミラクルニキ→ https://t.co/EjgsSnMpzc'), 'ガールズモード→ <URL> ミラクルニキ→ <URL>')
        # 記号()
        self.assertEqual(_replace_url('「Peak to Peak」についてはサークルサイト(http://ptp.cru-jp.com)をご覧下さい'), '「Peak to Peak」についてはサークルサイト(<URL>をご覧下さい')
        # 記号
        self.assertEqual(_replace_url('「Peak to Peak」についてはサークルサイト(http://mixi.jp/show_friend.pl?id=6)をご覧下さい'), '「Peak to Peak」についてはサークルサイト(<URL>をご覧下さい')
        # 記号全部
        self.assertEqual(_replace_url("マストドン https://mstdn.jp/<()'\"*hanayuu*-_;#!?*=@>"), 'マストドン <URL>')

    def test_invalid_profile(self):
        """
        公式アカウントなど除外する正規表現テスト
        """
        self.assertTrue(_invalid_profile('毎日新聞東京本社生活報道部が運営する公式ニュースアカウント'))
        self.assertTrue(_invalid_profile('女性向け自動botです（たまに手動）'))
        self.assertTrue(_invalid_profile('女性向け自動BOTです（たまに手動）'))
        self.assertTrue(_invalid_profile('目的は協賛企業などの宣伝を主な理由としています'))
