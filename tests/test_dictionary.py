import os
from word import Word
import pandas as pd
from util import load_config

class TestMorph(object):
    DIR_DICTIONARY = 'data/dictionary'

    def valid_close_word(self, file_path):
        df_close_word = pd.read_csv(file_path)
        w = Word()
        for row in df_close_word.itertuples():
            words = w.preprocess(row.word)
            if len(words) > 0:
                assert words[0] == row.replace_word

    def test_new_word(self):
        FILE_NEW_WORD = os.path.join(self.DIR_DICTIONARY, 'new_word.csv')
        df_new_word = pd.read_csv(FILE_NEW_WORD)

        w = Word()
        for row in df_new_word.itertuples():
            words = w.preprocess(row.surface)
            if len(words) > 0:
                assert words[0] == row.lexeme

    def test_close_word(self):
        FILE_CLOSE_WORD = os.path.join(self.DIR_DICTIONARY, 'close_word.csv')
        self.valid_close_word(FILE_CLOSE_WORD)

    def test_close_word_original(self):
        FILE_CLOSE_WORD_ORIGINAL = os.path.join(self.DIR_DICTIONARY, 'close_word_original.csv')
        self.valid_close_word(FILE_CLOSE_WORD_ORIGINAL)
