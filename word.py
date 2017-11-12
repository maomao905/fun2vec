from morpheme import WordParser
import re
from util import load_config
import logging
logging.config.dictConfig(load_config('log'))
logger = logging.getLogger(__name__)

class Word():
    __REGEX_JA = re.compile(r'[ぁ-んァ-ン一-龥]')
    __REGEX_EN = re.compile(r'[a-z]+', re.IGNORECASE)
    __REGEX_STOP_CHAR = re.compile(r'^([ァ-ン]|[ぁ-ん]{1,2})$', re.IGNORECASE)

    __PTN_DIGIT_ALL = r'[一二三四五六七八九十\d]'

    __REGEXES_REPLACE = (
        (re.compile(r'大学$'), '大学'),
        (re.compile(r'新聞$'), '新聞'),
        (re.compile(r'^JR'), 'JR'),
        (re.compile(r'受験$'), '受験'),
        (re.compile(r'姉妹$'), '姉妹'),
        (re.compile(r'^iPhone{}$'.format(__PTN_DIGIT_ALL)), 'iPhone'),
    )

    __REGEXES_EXCLUDE = (
        re.compile(r'^{}+日目?$'.format(__PTN_DIGIT_ALL)),
        re.compile(r'^{}+年(生|生まれ)?$'.format(__PTN_DIGIT_ALL)),
        re.compile(r'^{}+期生$'.format(__PTN_DIGIT_ALL)),
        re.compile(r'^{}+(月|人|歳|才|児)$'.format(__PTN_DIGIT_ALL)),
        re.compile(r'^{}+万?円?$'.format(__PTN_DIGIT_ALL)),
        re.compile(r'^{}+(戦|敗|勝|度)$'.format(__PTN_DIGIT_ALL)),
        re.compile(r'(出身|県)$'),
        re.compile(r'キロ$'),
        re.compile('ごめん'),
        re.compile('決定'),
        re.compile('注意'),
    )

    def __init__(self):
        file_config = load_config('file')
        self.__parser = WordParser(**file_config['mecab'])
        with open(file_config['word']['stop_words']) as f:
            self.__stop_words = frozenset(f.read().rstrip().split('\n'))

    def preprocess(self, text):
        words_processed = []
        morphs = self.__parser(text)
        for morph in morphs:
            morph.lexeme = self.__clean(morph.lexeme)
            if self.__valid(morph):
                words_processed.append(morph.lexeme)
        return words_processed

    def __clean(self, word):
        for regex, rep_word in self.__REGEXES_REPLACE:
            if regex.search(word):
                word = rep_word
                break

        for regex in self.__REGEXES_EXCLUDE:
            if regex.search(word):
                word = None
                break

        return word

    def __valid(self, morph):
        """
        原型をチェック
        英語・カタカナ１文字だけ、ひらがな１文字or２文字は省く
        """
        if morph.lexeme is None or morph.lexeme == '':
            return False

        if not self.__valid_pos(morph.pos):
            return False

        if self.__REGEX_STOP_CHAR.match(morph.lexeme):
            return False

        if morph.lexeme in self.__stop_words:
            return False
        return True

    def __valid_pos(self, pos):
        poses = pos.split('-')
        try:
            if poses[0] == '名詞' and poses[1] in ['一般', '固有名詞', 'サ変接続']:
                if poses[2] == '地域':
                    return False
                return True
            else:
                return False
        except IndexError:
            return True
