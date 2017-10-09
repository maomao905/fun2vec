PTN_REPLACE = (
    (r'高校|高等学校', '高校'),
    (r'大学', '大学'),
    (r'新聞', '新聞'),
    (r'JR', 'JR'),
    (r'受験', '受験'),
    (r'姉妹', '姉妹'),
)

PTN_EXCLUDE = (
    (r'[\d]日目?'),
    (r'[\d]年生?'),
    (r'出身$'),
    (r'県$'),
    (r'キロ$'),
    (r'ごめん'),
    (r'決定'),
    (r'注意'),
    (r'スタジアム'),
    (r'[\d]万円?$'),
)