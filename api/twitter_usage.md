statuses/sample, 全ツイートからランダムに選ばれたサンプルツイートをストリーミングで取得
=> 一応全部取得しておく。後でfilteringとかするかもしれないし
=> userがネストである場合があるので再帰的に調べる

ref: https://dev.twitter.com/overview/api/users

※ 補足
- filter_levelでfilterできる => 結局使えなかった。
Most likely a combination of shares, views, engagement numbers and so forth.
The “medium” (and eventually “high”) entries will roughly correlate to the “Top Tweets” results for searches on twitter.com
- track paramでフレーズ検索もできる
‘the twitter’ is the AND twitter, and ‘the,twitter’ is the OR twitter

api limit
・検索apiは15分180回
・1回の検索数上限100件
・過去8日分

follower数が多いユーザー取得できたらいいな

wikipediaのタイトルでランダムにsearch
