# 001: 本番環境を Railway から ConoHa VPS へ移行

日付: 2026-07-20
状態: 採用

## 決定

本番環境を Railway の PaaS から ConoHa VPS（メモリ 1GB、¥660/月）へ移行した。
アプリは systemd で常時起動し、GitHub Actions（SSH）で自動デプロイする構成に変更した。

## 理由

- Railway の Trial プランが終了し、継続利用には従量課金が発生する見込みだった
- ConoHa VPS は月額固定（¥660）でコストが予測可能になる
- GitHub Actions + SSH によるデプロイは Railway の自動ビルドと同等の利便性を保てる
- 既存の Railway 環境にはデータの引き継ぎ資産がなく、移行コストが低かった

## 影響

- Railway 環境は停止・削除（データ引き継ぎ不要）
- デプロイは `git push origin main` → Actions → SSH → `git pull && systemctl restart` の流れに統一
- VPS への SSH アクセスが運用の前提となる（鍵管理が必要）
- HTTPS 化は別途 nginx + certbot で対応予定（Issue #1）
