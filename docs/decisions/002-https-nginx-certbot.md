# 002: HTTPS化 — nginx リバースプロキシ + Let's Encrypt (certbot)

日付: 2026-07-27
状態: 採用

## 決定

本番を `https://ea-journey.com` に移行した。
nginx（80/443）をリバースプロキシとして前段に置き、uvicorn（127.0.0.1:8000）へ転送する構成とした。
TLS証明書は certbot（--nginx）で Let's Encrypt から取得し、自動更新を有効化した。

## 理由

ドメイン取得後、名前解決が通らない問題が発生した。
原因は ea-journey.com のネームサーバーが「カスタム（ns-a1〜a3.conoha.io）」に設定されており、
Aレコードを設定した ConoHa 標準 DNS ゾーン（a.conoha-dns.com / b.conoha-dns.org）と
向き先が食い違っていたことによる。NS を ConoHa 標準に変更して解決した。
HTTPS 化の方式は nginx + certbot が ConoHa VPS 環境での実績が多く、自動更新も確実なため採用した。

## 影響

- 本番URLが `http://160.251.252.203:8000` → `https://ea-journey.com` に変更
- ファイアウォール（ufw / ConoHaセキュリティグループ）に 80/443 を追加済み
- 同様のネームサーバー問題は他ドメイン追加時にも起こりうる。NS 設定を最初に確認すること
