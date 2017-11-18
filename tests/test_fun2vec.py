import os, sys
sys.path.append(os.getcwd())
from model import Model
from pygments import highlight
from pygments.formatters import Terminal256Formatter
from util import ljust_ja, CustomLexer, get_color_style
from pprint import pprint

CHECK_WORDS = (
    ('ビリヤード'),
    ('機械学習'),
    ('エンジニア'),
    ('プログラミング'),
    ('お笑い'),
    ('図書館'),
    ('ポケモン'),
    ('機械学習 エンジニア ビリヤード'),
    ('ビリヤード お笑い プログラミング'),
    ('図書館 映画 ポケモン'),
    ('スケート カメラ'),
    ('数学 スマホ 読書'),
    ('パソコン タブレット スマホ'), # 似た単語
    ('パソコン タブレット 読書'), # 似た単語 + 違う単語
    ('スキューバダイビング サーフィン 水泳'), # 似た単語
    ('ビリヤード サーフィン 水泳'), # 似た単語 + 違う単語
)
def main(model_names):
    for name in model_names:
        print(name.center(50, '-'))
        model = load_model(name)
        for words in CHECK_WORDS:
            print('words>', words)
            try:
                for word, sim in model.most_similar(words.split()):
                    word = ljust_ja(word, 20)
                    sim = round(sim, 3)
                    print(highlight('{word} {sim:.3f}'.format(word=word, sim=sim), \
                        lexer=CustomLexer(), formatter=Terminal256Formatter(style=get_color_style(sim))), end='')
                    highlight.__init__()
            except KeyError as e:
                print(e.args[0])
                continue

if __name__ == '__main__':
    model_names = sys.argv[1:]
    if not model_names:
        model_names = ['word2vec', 'fun2vec']
    main(model_names)
