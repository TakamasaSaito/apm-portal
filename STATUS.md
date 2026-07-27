# STATUS.md

最終更新日: 2026-07-27（HTTPS化完了）

## 現状

`https://ea-journey.com` で公開中。
nginx（80/443）→ uvicorn（127.0.0.1:8000）のリバースプロキシ構成。TLS は Let's Encrypt・自動更新有効。

## 完了済み

- ConoHa VPS への本番環境移行（Railway Trial 終了に伴い 2026-07-20 実施）
- GitHub Actions 自動デプロイ設定（SSH key 設定含む）
- ドメイン取得（ea-journey.com）・DNS A レコード設定
- CI リレーション一覧・依存関係一覧へのページネーション追加
- タブタイトルを「SPM ポータル」に修正
- audit.py 循環インポート修正
- ARCHITECTURE.md 作成（管理方針v2.3対応）
- HTTPS化（nginx + certbot / Let's Encrypt）— [#1](https://github.com/TakamasaSaito/apm-portal/issues/1)

## 残タスク

- [#2 seed.py 全面書き直し：日本企業らしいサンプルデータに刷新](https://github.com/TakamasaSaito/apm-portal/issues/2)
- [#3 コスト・予算の可視化：cost_plan テーブルを使った年度別ダッシュボード](https://github.com/TakamasaSaito/apm-portal/issues/3)

## 次の一手

seed.py を日本企業らしいサンプルデータに全面書き直しする（Issue #2）。
