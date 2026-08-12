# apm-portal 個別仕様書（SPEC.md）

> 共通標準（dev-standards/STANDARDS.md）との差分のみを記録する。
> 標準どおりの部分は書かない。「なぜ逸脱するか」を必ず書く。

## 基本情報

- 用途: SPM（サービスポートフォリオ管理）ポータル。シナリオナビゲーター・Business Portfolio・監査ログ・CMDB・変更管理
- type: server-app（PWA 機能は未整備 — manifest.json / apple-touch-icon / viewport zoom禁止なし）
- 現行マイルストーン: M1 完了（cost_plan ダッシュボード が残タスク）

## 標準からの逸脱

| 標準ID | 逸脱内容 | 理由 | 昇格候補? |
|--------|----------|------|-----------|
| AUTH-01 | nginx Basic 認証でなく FastAPI JWT 認証（bcrypt + jose）を採用 | admin / user の2ロール分離が必要。nginx Basic では単一パスワードしか扱えない | ×（複数ロール管理が必要なアプリのみ） |
| MOB-01 | viewport zoom 禁止なし（`user-scalable=no` 未設定） | デスクトップ管理画面。スマートフォンからの日常操作を想定していない | × |
| MOB-02 | 横スクロール防止の明示的実装なし | デスクトップ向けサイドバーレイアウト。モバイル最適化は対象外 | × |
| MOB-05 | apple-touch-icon なし | PWA として運用していない（ホーム画面追加を想定しない） | × |
| MOB-06 | manifest.json なし | 同上 | × |
| UI-01 | favicon 未整備（index.html に link rel=icon なし） | 初期構築時に未対応。残課題 | —（対応推奨） |
| UI-02 | OG meta（og:title / og:description / og:image）未整備 | 社内管理ツールのため外部共有を想定しない | × |
| UI-03 | Google Fonts CDN 経由（Noto Sans JP）— オフライン不可 | サーバーアプリのため常時オンラインが前提 | × |
| OPS-06 | deploy/nginx-{app-name}.conf なし | 既存アプリのため未整備。対応推奨 | —（対応推奨） |
| OPS-07 | deploy/apm-portal.service なし | 既存アプリのため未整備。対応推奨 | —（対応推奨） |

## アプリ固有機能

- **JWT 認証**: `backend/routers/auth.py`（bcrypt + python-jose）。SECRET_KEY は環境変数 `JWT_SECRET_KEY` から取得
- **Claude API 連携**: デマンド審査タスクの自動生成（詳細: `backend/routers/demand.py`）
- **多ルーター構成**: `backend/routers/` 配下に 9 個のルーターを分割（applications, audit, auth, capability, ci, cmdb, dashboard, demand, environments, requests）
- **Chart.js**: cdnjs 経由（v4.4.1 固定）
- **er_diagram.mermaid**: データモデルを Mermaid ER 図として管理
- **seed スクリプト群**: `scripts/seed.py` / `seed_demands.py` / `seed_demands_scores.py` / `seed_master.py` — サンプルデータ投入

## 意図的に「やらない」こと

- モバイル対応（デスクトップ専用管理ツール）
- OG / SNS シェア対応（社内ツール）
- PWA 化（ホーム画面追加・オフライン動作）

## 運用上の注意

- JWT の SECRET_KEY は本番環境で環境変数から注入すること（デフォルト値はデバッグ用）
- Chart.js は cdnjs CDN に依存。オフライン環境では動作しない
- `frontend/index.html` が約6,400行の単一ファイル。複雑度が高いため、変更時は影響範囲を慎重に確認する
- `data/apm.db` は `.gitignore` 対象。VPS 上のバックアップは手動管理
