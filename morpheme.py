from MeCab import Tagger
from util import load_config
import logging
logging.config.dictConfig(load_config('log'))
logger = logging.getLogger(__name__)

class WordParser():
    # http://taku910.github.io/mecab/format.html
    __DEFAULT_NODE = {
        'keys':         ('surface', 'lexeme',  'pos'),
        'node-format':  ('%H',      '%f[6]',    '%F-[0,1,2,3]'),
        'unk-format':   ('%m',      '%m',       '%F-[0,1,2,3]'),
    }
    __EOS_FORMAT  = ''

    def __init__(self, dicdir=None, userdics=None, node=None, *args, **kwargs):
        self.node = node or self.__DEFAULT_NODE

        option = {
            'node-format': r'\t'.join(self.node['node-format']) + r'\n',
            'unk-format': r'\t'.join(self.node['unk-format']) + r'\n',
            'eos-format': self.__EOS_FORMAT,
        }
        # http://taku910.github.io/mecab/mecab.html
        if dicdir:
            option['dicdir'] = dicdir
        if userdics:
            option['userdic'] = ','.join(userdics)
        self.__option = ' '.join('--{}={}'.format(*c) for c in option.items())
        self.__tagger = Tagger(self.__option)

    def __repr__(self):
        return f'{self.__class__.__qualname__}({self.__option!r})'

    def __call__(self, text):
        res = self.__tagger.parse(text).rstrip().split('\n')
        return [Morpheme(**self.__parse_node(node)) for node in self.__tagger.parse(text).rstrip().split('\n') if node]

    def __parse_node(self, node):
        return dict(zip(self.node['keys'], node.split('\t')))

class Morpheme:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return f'{self.__class__.__qualname__}<{self.__dict__}>'
