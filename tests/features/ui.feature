Feature: デスクトップUIからのキャプチャ操作
  ユーザーはデスクトップUIを通じてKindle画面をキャプチャし、
  PDFファイルとして保存できる。

  Background:
    Given デスクトップUIが起動している

  Scenario: アプリケーション起動時のKindle検出
    When アプリケーションが起動する
    Then Kindleウィンドウの検出結果が表示される

  Scenario: 自動モードでのキャプチャ開始
    Given Kindleウィンドウが検出されている
    And 自動モードが選択されている
    When ユーザーが開始ボタンをクリックする
    Then カウントダウンが表示される
    And キャプチャが開始される
    And 進捗バーが更新される

  Scenario: ページ数指定モードでのキャプチャ
    Given Kindleウィンドウが検出されている
    And ページ数指定モードで10ページが入力されている
    When ユーザーが開始ボタンをクリックする
    Then 10ページのキャプチャが実行される
    And PDFファイルが生成される
    And 完了メッセージが表示される

  Scenario: キャプチャの中断
    Given キャプチャが実行中である
    When ユーザーが停止ボタンをクリックする
    Then キャプチャが中断される
    And 中断メッセージが表示される

  Scenario: 設定の変更
    When ユーザーが設定ボタンをクリックする
    Then 設定ダイアログが表示される
    When キャプチャ間隔を2.0秒に変更する
    And 保存ボタンをクリックする
    Then 設定が保存される

  Scenario: 出力ファイルの選択
    When ユーザーが参照ボタンをクリックする
    Then ファイル選択ダイアログが表示される
    When ファイルを選択する
    Then ファイルパスが入力欄に反映される

  Scenario: Kindleウィンドウ未検出時のエラー
    Given Kindleウィンドウが検出されていない
    Then 開始ボタンが無効化されている
    And 未検出メッセージが表示される
