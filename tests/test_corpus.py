import unittest
from corpus import find_fun_part

SAMPLE_TEXT1 = '脳内掃除として独り言をつぶやいてる会社員です。  好きなこと：酒、風呂、寝る。最近はブクマとして使ってるような･･･。ここでの発言は私個人の意見であり、所属する組織を代表するものではありません。'
SAMPLE_TEXT2 = 'Lv3娘との日常生活/洋裁/ゲーム Steam&PS4/FX&株…極稀に雑談配信やゲーム配信やってます。最近はPS4版Divisionをプレイしています。'
SAMPLE_TEXT3 = 'FateGOありがとう。拡散性ＭＡは滅ぼしましたので乖離性で傭兵メインでやってます。艦これは、矢矧大鳳初風浦風あきつ丸くれ。あ、あと、絶望した。'
SAMPLE_TEXT4 = 'ビール、箱根駅伝、体操競技、ingress@RES、自転車、ジム、イカ'
# SAMPLE_TEXT5 = '根っこはAPH祖国島国。うたプリ（セシル）、刀剣（歌仙、蜂須賀）、文アル、FGO、シノアリス他。宝塚は子供の頃から。リアルで話した事がある人にしか話しかけられないので無言フォローすみません。成人済。リフォロは不要です。検索避の為に通常は鍵かけてます。'
class TestCorpus(unittest.TestCase):

    def test_find_fun_part(self):
        """
        興味を抽出する正規表現テスト
        """
        self.assertEqual(find_fun_part(SAMPLE_TEXT1), ['酒', '風呂', 'ブクマ'])
        self.assertEqual(find_fun_part(SAMPLE_TEXT2), ['娘', '日常生活', '洋裁', 'ゲーム', '株'])
        self.assertEqual(find_fun_part(SAMPLE_TEXT3), ['あと', '絶望'])
        self.assertEqual(find_fun_part(SAMPLE_TEXT4), ['ビール', '箱根駅伝', '体操競技', '自転車', 'ジム', 'イカ'])
        # self.assertEqual(find_fun_part(SAMPLE_TEXT5), ['ビール', '箱根駅伝', '体操競技', '自転車', 'ジム', 'イカ'])
