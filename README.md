# 実験用ソースコード
## 論文
- https://gitlab.ie.u-ryukyu.ac.jp/dissertation/2024/e215135/-/raw/main/thesis/latex_out/thesis.pdf
## フォルダ説明
- yes_intervention
  - 介入ありの実験のコード
- no_intervention
  - 介入なしの実験のコード
## 実行手順
- `cp .env_example .env`
- `brew install direnv`でdirenvをインストール後、`direnv allow .`を実行してください
- openAIのAPIキーを取得し、.envに貼り付けてください
- 任意のpython環境で`pip install -r requirements.txt`を実行
  - できるなら新しい環境が良い
- 介入ありの実験を行いたい場合
  - `cd yes_intervention`
  - `make run-flask`
  - `http://127.0.0.1:5000`にアクセスしてGUIの指示通りにボタンを押し進める
- 介入なしの実験を行いたい場合
  - `cd no_intervention`
  - `make run-flask`
  - `http://127.0.0.1:5000`にアクセスしてGUIの指示通りにボタンを押し進める
## 前提確認質問の追加プロンプトの作成方法
json_load.ipynbを実行してください。15回分の会話例が作成されるので、
逐一、config.yaml記載のエージェントA, Bのプロンプトの後ろに追加してください。