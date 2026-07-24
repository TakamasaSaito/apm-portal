# STATUS.md

最終更新日: 2026-07-25

## 現状

ConoHa VPS（160.251.252.203）へ移行完了、systemd で常時起動中。
GitHub Actions による自動デプロイが稼働しており、main push で本番反映される。

## 完了済み

- ConoHa VPS への本番環境移行（Railway Trial 終了に伴い 2026-07-20 実施）
- GitHub Actions 自動デプロイ設定（SSH key 設定含む）
- ドメイン取得（ea-journey.com）・DNS A レコード設定
- CI リレーション一覧・依存関係一覧へのページネーション追加
- タブタイトルを「SPM ポータル」に修正
- audit.py 循環インポート修正

## 残タスク

- [#1 HTTPS化（Let's Encrypt）：nginx + certbot でリバースプロキシ構成](https://github.com/TakamasaSaito/apm-portal/issues/1)
- [#2 seed.py 全面書き直し：日本企業らしいサンプルデータに刷新](https://github.com/TakamasaSaito/apm-portal/issues/2)
- [#3 コスト・予算の可視化：cost_plan テーブルを使った年度別ダッシュボード](https://github.com/TakamasaSaito/apm-portal/issues/3)

## 次の一手

DNS 反映を確認後、nginx + certbot でHTTPS化を実施する（Issue #1）。
