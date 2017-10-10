import pandas as pd

"""
Create original dictionary
Merge new_word.tsv + close_word.tsv + close_word_original.tsv
Final output: original_dict.csv
"""

def create_original_dictionary():
    res = []
    df = pd.read_csv('data/close_word.tsv', sep='\t')
    for row in df.itertuples():
        morph = replace_morph(row.word, row.replace_word)
        if morph:
            res.append(morph + '\n')

    with open('data/original_dic.csv', 'w') as f:
        f.writelines(res)

def replace_morph(word, replace_word):
    """
    日本語で名詞 or 形容詞を取得
    """
    if word != word or word == replace_word:
        return
    tagger = MeCab.Tagger()
    tagger.parse('')
    try:
        node = tagger.parseToNode(word)
    except TypeError:
        import pdb; pdb.set_trace()
    while node:
        if node.surface:
            features = node.feature.split(',')
            features[6] = replace_word
        node = node.next
    return '{},,,1,'.format(word) + ','.join(features)
