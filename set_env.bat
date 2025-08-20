@echo off
REM 環境変数を設定するバッチファイル
REM このファイルを実行する前に、実際のAPIキーを設定してください

set OPENAI_API_KEY=your_actual_openai_api_key_here
set SERP_API_KEY=your_actual_serpapi_key_here

echo 環境変数が設定されました
echo OPENAI_API_KEY: %OPENAI_API_KEY%
echo SERP_API_KEY: %SERP_API_KEY%

REM アプリケーションを起動
python app.py

