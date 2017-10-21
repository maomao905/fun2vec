import re

PTN_DIGIT_ALL = r'[一二三四五六七八九十\d]'

REGEX_REPLACE = (
    (re.compile(r'(高校|高等学校)$'), '高校'),
    (re.compile(r'(中学|中学校)$'), '中学'),
    (re.compile(r'大学$'), '大学'),
    (re.compile(r'新聞$'), '新聞'),
    (re.compile(r'^JR'), 'JR'),
    (re.compile(r'受験$'), '受験'),
    (re.compile(r'姉妹$'), '姉妹'),
    (re.compile(r'^iPhone{}$'.format(PTN_DIGIT_ALL)), 'iPhone'),
)

REGEX_EXCLUDE = (
    re.compile(r'^{}日目?$'.format(PTN_DIGIT_ALL)),
    re.compile(r'^{}年生?$'.format(PTN_DIGIT_ALL)),
    re.compile(r'出身$'),
    re.compile(r'県$'),
    re.compile(r'キロ$'),
    re.compile('ごめん'),
    re.compile('決定'),
    re.compile('注意'),
    re.compile(r'^{}+万?円?$'.format(PTN_DIGIT_ALL)),
    re.compile(r'^{}+(戦|敗|勝|度)$'.format(PTN_DIGIT_ALL)),
)

def clean_word(word):
    for regex, rep_word in REGEX_REPLACE:
        if regex.search(word):
            word = rep_word
            break

    for regex in REGEX_EXCLUDE:
        if regex.search(word):
            if word == '中日':
                print(regex)
            word = None
            break

    return word
