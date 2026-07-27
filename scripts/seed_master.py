"""マスターデータ投入スクリプト。全テーブルをリセットして基本マスタを投入する。
単独実行: python scripts/seed_master.py
"""
import sqlite3
import json
import os
from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _hash(pw: str) -> str:
    return _pwd_context.hash(pw)


DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "apm.db")


def seed_master():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # --- 全テーブルを DROP + 完全スキーマで CREATE ---
    cur.executescript("""
PRAGMA foreign_keys = OFF;

DROP TABLE IF EXISTS audit_log;
DROP TABLE IF EXISTS cmdb_rel_ci;
DROP TABLE IF EXISTS demand_task;
DROP TABLE IF EXISTS demand_application;
DROP TABLE IF EXISTS cost_plan;
DROP TABLE IF EXISTS project;
DROP TABLE IF EXISTS demand;
DROP TABLE IF EXISTS apm_request;
DROP TABLE IF EXISTS application_dependency;
DROP TABLE IF EXISTS configuration_item;
DROP TABLE IF EXISTS environment;
DROP TABLE IF EXISTS application;
DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS department;
DROP TABLE IF EXISTS business_capability;
DROP TABLE IF EXISTS relation_type;

CREATE TABLE relation_type (
    relation_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_name        TEXT NOT NULL UNIQUE,
    parent_label     TEXT,
    child_label      TEXT
);

CREATE TABLE business_capability (
    capability_id    TEXT PRIMARY KEY,
    capability_name  TEXT NOT NULL,
    parent_id        TEXT REFERENCES business_capability(capability_id),
    level            INTEGER NOT NULL,
    scope            TEXT,
    sort_order       INTEGER
);

CREATE TABLE department (
    department_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    department_name TEXT NOT NULL UNIQUE
);

CREATE TABLE user (
    user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name     TEXT NOT NULL,
    department_id INTEGER REFERENCES department(department_id),
    role          TEXT NOT NULL DEFAULT 'applicant',
    login_id      TEXT,
    password_hash TEXT
);

CREATE TABLE application (
    application_id       TEXT PRIMARY KEY,
    application_name     TEXT NOT NULL,
    owner_department_id  INTEGER REFERENCES department(department_id),
    status               TEXT NOT NULL DEFAULT 'plan',
    vendor               TEXT,
    business_owner       TEXT,
    system_owner         TEXT,
    ops_manager          TEXT,
    dev_manager          TEXT,
    start_plan           TEXT,
    start_actual         TEXT,
    end_plan             TEXT,
    end_actual           TEXT,
    app_category         TEXT,
    portfolio_area       INTEGER,
    migration_target_id  TEXT REFERENCES application(application_id),
    annual_cost_million  INTEGER,
    is_infrastructure    INTEGER DEFAULT 0
);

CREATE TABLE application_dependency (
    dependency_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    app_id             TEXT REFERENCES application(application_id),
    depends_on_app_id  TEXT REFERENCES application(application_id),
    dependency_type    TEXT,
    note               TEXT,
    migration_status   TEXT DEFAULT 'not_planned',
    migration_due_date DATE,
    migration_note     TEXT
);

CREATE TABLE environment (
    environment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    env_type       TEXT NOT NULL,
    location       TEXT, ip TEXT, host TEXT, os TEXT,
    middleware     TEXT, cpu_mem TEXT, storage TEXT
);

CREATE TABLE configuration_item (
    ci_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ci_name      TEXT NOT NULL, ci_type TEXT,
    hostname     TEXT, ip_address TEXT, bmc_ip TEXT,
    os TEXT, os_version TEXT, cpu TEXT, memory TEXT, storage TEXT,
    vendor TEXT, model TEXT,
    status       TEXT DEFAULT 'active', note TEXT
);

CREATE TABLE apm_request (
    request_id        TEXT PRIMARY KEY,
    type              TEXT NOT NULL,
    application_id    TEXT REFERENCES application(application_id),
    applicant_user_id INTEGER REFERENCES user(user_id),
    applied_at        TEXT NOT NULL,
    status            TEXT NOT NULL DEFAULT 'pending',
    approver_user_id  INTEGER REFERENCES user(user_id),
    approved_at       TEXT,
    reason            TEXT,
    changes           TEXT,
    app_name          TEXT,
    dept              TEXT,
    biz_owner         TEXT,
    new_status        TEXT,
    start_plan        TEXT,
    end_plan          TEXT,
    app_category      TEXT
);

CREATE TABLE cmdb_rel_ci (
    rel_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_table     TEXT NOT NULL,
    parent_id        TEXT NOT NULL,
    child_table      TEXT NOT NULL,
    child_id         TEXT NOT NULL,
    relation_type_id INTEGER REFERENCES relation_type(relation_type_id),
    note             TEXT,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE demand (
    demand_id        TEXT PRIMARY KEY,
    title            TEXT NOT NULL,
    it_class         TEXT, category TEXT, domain TEXT, type TEXT,
    start_date       DATE, due_date DATE,
    submitter_user_id    INTEGER REFERENCES user(user_id),
    department_id        INTEGER REFERENCES department(department_id),
    manager_user_id      INTEGER REFERENCES user(user_id),
    system_owner_user_id INTEGER REFERENCES user(user_id),
    pm_user_id           INTEGER REFERENCES user(user_id),
    description      TEXT, portfolio TEXT, program TEXT,
    change_type      TEXT, purpose TEXT, feasibility TEXT,
    priority         TEXT, region TEXT, company TEXT,
    business_unit    TEXT, business_case TEXT, expected_benefit TEXT,
    target_date      DATE,
    estimated_cost   INTEGER, requested_budget INTEGER,
    cost_note        TEXT, notes TEXT,
    stage            TEXT DEFAULT 'draft',
    reject_reason    TEXT, review_comment TEXT, approval_comment TEXT,
    score            INTEGER, investment_class TEXT,
    capital_expense  INTEGER, operating_expense INTEGER,
    financial_benefit INTEGER, roi_percent REAL, npv INTEGER,
    irr REAL, capital_budget INTEGER, operating_budget INTEGER,
    discount_rate REAL, demand_actual_cost INTEGER,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE demand_application (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    demand_id      TEXT REFERENCES demand(demand_id),
    application_id TEXT REFERENCES application(application_id),
    relation_note  TEXT
);

CREATE TABLE cost_plan (
    cost_plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    demand_id    TEXT REFERENCES demand(demand_id),
    fiscal_year  INTEGER, fiscal_period TEXT, cost_type TEXT,
    unit_cost    INTEGER, quantity INTEGER DEFAULT 1,
    planned_cost INTEGER, actual_cost INTEGER DEFAULT 0, note TEXT,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE demand_task (
    task_id          TEXT PRIMARY KEY,
    demand_id        TEXT REFERENCES demand(demand_id),
    name             TEXT NOT NULL,
    due_date         DATE,
    assignee_user_id INTEGER REFERENCES user(user_id),
    priority         TEXT,
    state            TEXT DEFAULT 'open',
    comment          TEXT, ai_generated INTEGER DEFAULT 0, rationale TEXT,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE project (
    project_id      TEXT PRIMARY KEY,
    demand_id       TEXT REFERENCES demand(demand_id),
    title           TEXT NOT NULL,
    status          TEXT DEFAULT 'active',
    manager_user_id INTEGER REFERENCES user(user_id),
    portfolio       TEXT,
    description     TEXT,
    created_date    DATE,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_log (
    audit_log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER REFERENCES user(user_id),
    action       TEXT NOT NULL,
    target_table TEXT, target_id TEXT,
    before_value TEXT, after_value TEXT, ip_address TEXT,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
);
    """)

    # ---------- relation_type マスター ----------
    for row in (
        ("has_environment", "環境を持つ",    "環境である"),
        ("has_ci",          "構成情報を持つ", "構成情報である"),
        ("realizes",        "ケイパビリティ", "実現システム"),
    ):
        cur.execute(
            "INSERT OR IGNORE INTO relation_type (type_name, parent_label, child_label) VALUES (?,?,?)",
            list(row),
        )

    has_env_id = cur.execute("SELECT relation_type_id FROM relation_type WHERE type_name='has_environment'").fetchone()[0]
    has_ci_id  = cur.execute("SELECT relation_type_id FROM relation_type WHERE type_name='has_ci'").fetchone()[0]
    realizes_id = cur.execute("SELECT relation_type_id FROM relation_type WHERE type_name='realizes'").fetchone()[0]

    # ---------- 部署（20件） ----------
    departments = [
        "人事部", "営業本部", "購買部", "経理部", "総務部",
        "情報システム部", "開発部", "品質管理部", "法務部", "マーケティング部",
        "海外事業部", "製造部", "物流部", "カスタマーサポート部", "広報部",
        "財務部", "経営企画部", "内部監査部", "調達部", "研修部",
    ]
    dept_ids: dict = {}
    for d in departments:
        cur.execute("INSERT INTO department (department_name) VALUES (?)", [d])
        dept_ids[d] = cur.lastrowid

    # ---------- ユーザー（20件） ----------
    users = [
        ("申請者ユーザー", "情報システム部",       "applicant", "user",  _hash("user")),
        ("事務局ユーザー", "情報システム部",       "admin",     "admin", _hash("admin")),
        ("田中 花子",      "人事部",               "applicant", None, None),
        ("山田 太郎",      "情報システム部",       "applicant", None, None),
        ("鈴木 一郎",      "経理部",               "applicant", None, None),
        ("高橋 二郎",      "営業本部",             "applicant", None, None),
        ("佐藤 事務局",    "情報システム部",       "admin",     None, None),
        ("伊藤 三郎",      "購買部",               "applicant", None, None),
        ("渡辺 四郎",      "総務部",               "applicant", None, None),
        ("中村 五郎",      "開発部",               "applicant", None, None),
        ("小林 六子",      "品質管理部",           "applicant", None, None),
        ("加藤 七子",      "法務部",               "admin",     None, None),
        ("吉田 八郎",      "マーケティング部",     "applicant", None, None),
        ("山本 九子",      "海外事業部",           "applicant", None, None),
        ("松本 十郎",      "製造部",               "applicant", None, None),
        ("井上 勇",        "物流部",               "applicant", None, None),
        ("木村 梅子",      "カスタマーサポート部", "applicant", None, None),
        ("林 竹子",        "広報部",               "applicant", None, None),
        ("清水 松子",      "財務部",               "admin",     None, None),
        ("藤田 健",        "経営企画部",           "applicant", None, None),
    ]
    user_ids: dict = {}
    for name, dept, role, login_id, password_hash in users:
        cur.execute(
            "INSERT INTO user (user_name, department_id, role, login_id, password_hash) VALUES (?, ?, ?, ?, ?)",
            [name, dept_ids[dept], role, login_id, password_hash],
        )
        user_ids[name] = cur.lastrowid

    # ---------- アプリケーション（22件） ----------
    apps = [
        ("G-CLOUD", "グローバルクラウド基盤(AWS)",    "情報システム部", "running",
         "Amazon Web Services",
         "事務局ユーザー", "山田 太郎", "山田 太郎", "山田 太郎",
         "2022-04-01", "2022-04-01", None, None,
         "Cloud Platform（クラウド基盤）", 4, None, 6200, 1),
        ("G-SSO",   "グローバル認証基盤(SSO)",        "情報システム部", "running",
         "Microsoft Azure AD",
         "事務局ユーザー", "山田 太郎", "山田 太郎", "山田 太郎",
         "2023-01-01", "2023-01-01", None, None,
         "Security（セキュリティ管理）", 4, None, 3800, 1),
        ("G-HRM",   "グローバルHRM",                  "人事部",         "dev",
         "Workday",
         "田中 花子", "田中 花子", "田中 花子", "中村 五郎",
         "2026-10-01", None, None, None,
         "HRM（人事・労務・給与）", 4, None, 4800, 0),
        ("G-ERP",   "グローバルERP",                  "経理部",         "running",
         "SAP",
         "鈴木 一郎", "鈴木 一郎", "鈴木 一郎", "中村 五郎",
         "2023-07-01", "2023-07-01", None, None,
         "ERP（基幹業務）", 4, None, 5500, 0),
        ("INF-DC1",  "国内データセンター基盤",         "情報システム部", "running",
         "NTTデータ",
         "事務局ユーザー", "山田 太郎", "山田 太郎", "山田 太郎",
         "2015-04-01", "2015-04-01", "2027-03-31", None,
         "Infrastructure（インフラ・サーバー・クラウド）", 2, "G-CLOUD", 1200, 1),
        ("INF-AUTH", "国内認証基盤",                   "情報システム部", "running",
         "株式会社ID管理",
         "事務局ユーザー", "山田 太郎", "山田 太郎", "山田 太郎",
         "2016-06-01", "2016-06-01", "2026-09-30", None,
         "Security（セキュリティ管理）", 2, "G-SSO", 900, 1),
        ("APM-001", "人事管理システム",                "人事部",         "running",
         "株式会社HR-Tech",
         "田中 花子", "田中 花子", "山田 太郎", "中村 五郎",
         "2021-04-01", "2021-04-01", "2028-03-31", None,
         "HRM（人事・労務・給与）", 2, None, 850, 0),
        ("APM-002", "営業支援システム（SFA）",         "営業本部",       "running",
         "Salesforce Japan",
         "高橋 二郎", "高橋 二郎", "山田 太郎", "中村 五郎",
         "2020-10-01", "2020-10-15", "2027-09-30", None,
         "CRM（顧客管理・営業支援）", 2, None, 620, 0),
        ("APM-003", "在庫管理システム",                "購買部",         "running",
         "株式会社SCM-Pro",
         "伊藤 三郎", "伊藤 三郎", "山田 太郎", "中村 五郎",
         "2019-07-01", "2019-07-01", "2027-06-30", None,
         "SCM（サプライチェーン・購買・在庫）", 2, None, 480, 0),
        ("APM-004", "経費精算システム",                "経理部",         "running",
         "株式会社FinTech",
         "鈴木 一郎", "鈴木 一郎", "山田 太郎", "中村 五郎",
         "2022-01-01", "2022-02-01", "2029-03-31", None,
         "Finance（経理・財務・予算）", 2, None, 520, 0),
        ("APM-005", "顧客管理システム（CRM）",         "営業本部",       "dev",
         "Salesforce Japan",
         "高橋 二郎", "高橋 二郎", "山田 太郎", "中村 五郎",
         "2025-10-01", None, None, None,
         "CRM（顧客管理・営業支援）", 3, None, 720, 0),
        ("APM-006", "文書管理システム",                "総務部",         "plan",
         "未定",
         "渡辺 四郎", "渡辺 四郎", "未定", "未定",
         "2026-10-01", None, None, None,
         "Document Management（文書・コンテンツ管理）", 3, None, 380, 0),
        ("APM-007", "旧給与計算システム",              "人事部",         "retire",
         "株式会社レガシーSI",
         "田中 花子", "田中 花子", "退任", "退任",
         "2010-04-01", "2010-04-01", "2026-03-31", "2026-03-31",
         "HRM（人事・労務・給与）", 1, "G-HRM", 450, 0),
        ("APM-008", "法務契約管理システム",            "法務部",         "running",
         "DocuSign Japan",
         "加藤 七子", "加藤 七子", "山田 太郎", "中村 五郎",
         "2020-07-01", "2020-07-15", "2028-06-30", None,
         "Legal / Compliance（法務・コンプライアンス）", 3, None, 250, 0),
        ("APM-009", "マーケティング自動化ツール",      "マーケティング部", "running",
         "HubSpot Japan",
         "吉田 八郎", "吉田 八郎", "山田 太郎", "中村 五郎",
         "2021-10-01", "2021-11-01", "2028-09-30", None,
         "Marketing（マーケティング）", 3, None, 350, 0),
        ("APM-010", "設備管理システム",                "製造部",         "running",
         "株式会社FACILITY",
         "松本 十郎", "松本 十郎", "山田 太郎", "中村 五郎",
         "2019-04-01", "2019-04-01", "2027-03-31", None,
         "ITSM / ITOM（ITサービス・運用管理）", 2, None, 280, 0),
        ("APM-011", "品質管理システム",                "品質管理部",     "running",
         "株式会社QA-Pro",
         "小林 六子", "小林 六子", "山田 太郎", "中村 五郎",
         "2020-01-01", "2020-01-15", "2028-12-31", None,
         "Other（その他）", 2, None, 310, 0),
        ("APM-012", "カスタマーサポートチケット管理",  "カスタマーサポート部", "running",
         "Zendesk Japan",
         "木村 梅子", "木村 梅子", "山田 太郎", "中村 五郎",
         "2021-07-01", "2021-07-01", None, None,
         "ITSM / ITOM（ITサービス・運用管理）", 3, None, 240, 0),
        ("APM-013", "勤怠管理システム",                "人事部",         "running",
         "株式会社TIME-Pro",
         "田中 花子", "田中 花子", "山田 太郎", "中村 五郎",
         "2022-07-01", "2022-07-01", None, None,
         "HRM（人事・労務・給与）", 2, None, 190, 0),
        ("APM-014", "社内ポータル",                    "総務部",         "running",
         "Microsoft",
         "渡辺 四郎", "渡辺 四郎", "山田 太郎", "中村 五郎",
         "2018-04-01", "2018-04-01", None, None,
         "Collaboration（グループウェア・社内コミュニケーション）", 2, None, 180, 0),
        ("APM-015", "旧勤怠管理システム",              "人事部",         "retire",
         "株式会社レガシーHR",
         "田中 花子", "退任", "退任", "退任",
         "2008-04-01", "2008-04-01", "2025-03-31", "2025-03-31",
         "HRM（人事・労務・給与）", 1, "APM-013", 280, 0),
        ("APM-016", "レガシー帳票出力システム",         "情報システム部", "running",
         "株式会社帳票SI",
         "山田 太郎", "山田 太郎", "山田 太郎", "退任",
         "2007-10-01", "2007-10-01", "2026-03-31", None,
         "Document Management（文書・コンテンツ管理）", 1, None, 120, 0),
        ("APM-017", "旧会議室予約システム",             "総務部",         "running",
         "株式会社オフィスSI",
         "渡辺 四郎", "渡辺 四郎", "渡辺 四郎", "退任",
         "2011-04-01", "2011-04-01", "2026-06-30", None,
         "Collaboration（グループウェア・社内コミュニケーション）", 1, None, 80, 0),
        ("APM-018", "旧社内チャットツール",             "総務部",         "retire",
         "旧ベンダー（サービス終了）",
         "渡辺 四郎", "退任", "退任", "退任",
         "2013-07-01", "2013-07-01", "2025-09-30", "2025-09-30",
         "Communication Platform（社内コミュニケーション）", 1, "APM-014", 150, 0),
        ("APM-019", "旧文書管理システム",               "総務部",         "running",
         "株式会社文書SI",
         "渡辺 四郎", "渡辺 四郎", "山田 太郎", "退任",
         "2010-04-01", "2010-04-01", "2026-09-30", None,
         "Document Management（文書・コンテンツ管理）", 1, "APM-006", 320, 0),
        ("APM-020", "旧経費精算ワークフロー",           "経理部",         "running",
         "株式会社レガシーFinance",
         "鈴木 一郎", "鈴木 一郎", "山田 太郎", "退任",
         "2009-10-01", "2009-10-01", "2026-03-31", None,
         "Finance（経理・財務・予算）", 1, "G-ERP", 480, 0),
        ("APM-021", "旧勤怠連携バッチシステム",         "情報システム部", "running",
         "内製",
         "山田 太郎", "山田 太郎", "山田 太郎", "山田 太郎",
         "2012-04-01", "2012-04-01", "2026-06-30", None,
         "ITSM / ITOM（ITサービス・運用管理）", 1, "APM-013", 60, 1),
        ("APM-022", "旧グループウェア",                 "総務部",         "running",
         "旧ベンダー",
         "渡辺 四郎", "渡辺 四郎", "山田 太郎", "退任",
         "2006-04-01", "2006-04-01", "2026-12-31", None,
         "Collaboration（グループウェア・社内コミュニケーション）", 1, "APM-014", 550, 0),
    ]
    for (app_id, name, dept, status, vendor,
         biz, sys_o, ops, dev,
         start_p, start_a, end_p, end_a, app_cat,
         portfolio_area, migration_target_id, annual_cost, is_infra) in apps:
        cur.execute(
            """INSERT INTO application
                   (application_id, application_name, owner_department_id, status, vendor,
                    business_owner, system_owner, ops_manager, dev_manager,
                    start_plan, start_actual, end_plan, end_actual, app_category,
                    portfolio_area, migration_target_id, annual_cost_million, is_infrastructure)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [app_id, name, dept_ids[dept], status, vendor,
             biz, sys_o, ops, dev,
             start_p, start_a, end_p, end_a, app_cat,
             portfolio_area, migration_target_id, annual_cost, is_infra],
        )

    # ---------- アプリ依存関係 ----------
    def _dep(a, b, t, n, m_st="not_planned", m_due=None, m_note=None):
        return (a, b, t, n, m_st, m_due, m_note)

    deps = [
        _dep("APM-001", "INF-DC1",  "infra", "東京DCオンプレサーバー上で稼働"),
        _dep("APM-001", "INF-AUTH", "auth",  "社内認証基盤でSSO連携"),
        _dep("APM-003", "INF-DC1",  "infra", "大阪DCオンプレサーバー上で稼働"),
        _dep("APM-003", "INF-AUTH", "auth",  "社内認証基盤でSSO連携"),
        _dep("APM-007", "INF-DC1",  "infra", "東京DCオンプレサーバー上で稼働（廃止済）", "completed"),
        _dep("APM-007", "G-HRM",    "data",  "G-HRMへ人事データ移行完了",               "completed"),
        _dep("APM-010", "INF-DC1",  "infra", "東京DCオンプレサーバー上で稼働"),
        _dep("APM-011", "INF-DC1",  "infra", "大阪DCオンプレサーバー上で稼働"),
        _dep("APM-002", "G-CLOUD",  "infra", "AWS上でホスティング"),
        _dep("APM-002", "G-SSO",    "auth",  "グローバルSSO連携"),
        _dep("APM-004", "G-CLOUD",  "infra", "AWS上でホスティング"),
        _dep("APM-004", "G-SSO",    "auth",  "グローバルSSO連携"),
        _dep("APM-005", "G-CLOUD",  "infra", "AWS上で開発中"),
        _dep("APM-005", "G-SSO",    "auth",  "グローバルSSO連携"),
        _dep("APM-006", "G-CLOUD",  "infra", "AWS上で構築予定"),
        _dep("APM-008", "G-CLOUD",  "infra", "AWS上でホスティング"),
        _dep("APM-008", "G-SSO",    "auth",  "グローバルSSO連携"),
        _dep("APM-009", "G-SSO",    "auth",  "グローバルSSO連携"),
        _dep("APM-012", "G-CLOUD",  "infra", "AWS上でホスティング"),
        _dep("APM-013", "G-CLOUD",  "infra", "SaaS連携（KING OF TIME）"),
        _dep("APM-013", "G-SSO",    "auth",  "グローバルSSO連携"),
        _dep("APM-014", "G-CLOUD",  "infra", "SharePoint Online（M365 / AWS連携）"),
        _dep("APM-014", "G-SSO",    "auth",  "グローバルSSO連携"),
        _dep("INF-DC1", "G-CLOUD",  "infra", "AWSへ段階移行中"),
        _dep("INF-AUTH","G-SSO",    "auth",  "G-SSO移行進行中"),
        _dep("G-ERP",   "G-CLOUD",  "infra", "AWS上で稼働"),
        _dep("G-ERP",   "G-SSO",    "auth",  "グローバルSSO連携"),
        _dep("G-HRM",   "G-CLOUD",  "infra", "AWS上で開発中"),
        _dep("APM-015", "INF-DC1",  "infra", "東京DCオンプレサーバー上で稼働（廃止済）",   "completed"),
        _dep("APM-016", "INF-DC1",  "infra", "東京DCオンプレ帳票サーバー上で稼働"),
        _dep("APM-020", "INF-DC1",  "infra", "東京DCオンプレサーバー上で稼働（廃止予定）"),
        _dep("APM-021", "INF-DC1",  "infra", "東京DCオンプレバッチサーバー上で稼働",       "in_progress", "2026-12-31", "AWS移行プロジェクト進行中"),
        _dep("APM-022", "INF-AUTH", "auth",  "旧社内認証基盤でSSO連携（廃止予定）",        "planned",     "2026-09-30", "G-SSOへの切替を計画中"),
        _dep("APM-021", "INF-AUTH", "auth",  "認証基盤依存",                              "planned", "2026-08-31", "グローバル認証基盤への切替を計画中"),
        _dep("APM-013", "INF-AUTH", "auth",  "勤怠管理がINF-AUTHに依存（未対応）"),
        _dep("APM-012", "INF-AUTH", "auth",  "CSがINF-AUTHに依存（未対応）"),
        _dep("APM-014", "INF-DC1",  "infra", "ポータルのオンプレ系処理がINF-DC1に依存（未対応）"),
    ]
    for app_id, dep_id, dep_type, note, m_st, m_due, m_note in deps:
        cur.execute(
            """INSERT INTO application_dependency
                   (app_id, depends_on_app_id, dependency_type, note,
                    migration_status, migration_due_date, migration_note)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [app_id, dep_id, dep_type, note, m_st, m_due, m_note],
        )

    # ---------- 環境（30件） ----------
    envs = [
        ("G-CLOUD", "本番環境",        "AWS ap-northeast-1",    "VPC 10.10.0.0/16",  "aws-prod.corp.local",        "Amazon Linux 2023", "Kubernetes 1.30",        "多数 EC2 インスタンス", "S3/EBS/RDS"),
        ("G-CLOUD", "DR環境",           "AWS ap-northeast-3",    "VPC 10.20.0.0/16",  "aws-dr.corp.local",           "Amazon Linux 2023", "Kubernetes 1.30",        "多数 EC2 インスタンス", "S3/EBS"),
        ("G-SSO",   "本番環境",         "Azure Japan East",      "40.79.192.0/24",    "sso-prod.corp.local",         "Azure AD",          "Microsoft Entra ID",     "マネージドサービス",    "Azure ストレージ"),
        ("G-ERP",   "本番環境",         "AWS ap-northeast-1",    "VPC 10.30.0.0/16",  "erp-prod.corp.local",         "SUSE Linux 15",     "SAP S/4HANA 2023",       "16vCPU/128GB",          "10TB SSD"),
        ("G-HRM",   "開発環境",         "Workday Sandbox",       "SaaS",              "hrm-dev.corp.local",          "SaaS (Workday)",     "Workday Sandbox",        "マネージドサービス",    "SaaS ストレージ"),
        ("INF-DC1", "本番環境",         "東京DC（大手町）",       "10.0.0.0/16",       "dc1-tokyo.corp.local",        "VMware ESXi 7.0",   "VMware vCenter 7.0",     "160vCPU/1024GB（計）",  "NetApp AFF A400 100TB"),
        ("INF-DC1", "DR環境",           "大阪DC（本社内）",       "10.1.0.0/16",       "dc1-osaka.corp.local",        "VMware ESXi 7.0",   "VMware vCenter 7.0",     "80vCPU/512GB（計）",    "NetApp AFF A250 50TB"),
        ("INF-AUTH","本番環境",         "東京DC（大手町）",       "10.0.1.0/24",       "auth-prod.corp.local",        "Windows Server 2019","Active Directory DS",    "4vCPU/16GB",            "500GB SSD RAID1"),
        ("APM-001", "本番環境",         "東京DC（大手町）",       "10.0.2.10",         "hr-prod.corp.local",          "RHEL 8.6",          "Tomcat 10 / Java 17",    "8vCPU/32GB",            "1TB SSD"),
        ("APM-001", "ステージング環境",  "東京DC（大手町）",       "10.0.2.20",         "hr-stg.corp.local",           "RHEL 8.6",          "Tomcat 10 / Java 17",    "4vCPU/16GB",            "500GB SSD"),
        ("APM-001", "開発環境",         "AWS ap-northeast-1",    "172.31.1.10",       "hr-dev.corp.local",           "Amazon Linux 2",    "Tomcat 10 / Java 17",    "2vCPU/8GB",             "200GB SSD"),
        ("APM-002", "本番環境",         "AWS ap-northeast-1",    "52.2.10.10",        "sfa-prod.corp.local",         "Amazon Linux 2",    "Node.js 18 / PM2",       "4vCPU/16GB",            "500GB SSD"),
        ("APM-002", "テスト環境",        "AWS ap-northeast-1",    "52.2.11.10",        "sfa-test.corp.local",         "Amazon Linux 2",    "Node.js 18 / PM2",       "2vCPU/8GB",             "200GB SSD"),
        ("APM-003", "本番環境",         "大阪DC（本社内）",       "10.1.3.10",         "inv-prod.corp.local",         "CentOS 7.9",        "Apache / PHP 8.1",       "8vCPU/32GB",            "2TB HDD RAID5"),
        ("APM-003", "ステージング環境",  "大阪DC（本社内）",       "10.1.3.20",         "inv-stg.corp.local",          "CentOS 7.9",        "Apache / PHP 8.1",       "4vCPU/16GB",            "1TB HDD"),
        ("APM-004", "本番環境",         "AWS ap-northeast-1",    "52.3.10.10",        "expense-prod.corp.local",     "Amazon Linux 2",    "Python 3.11 / FastAPI",  "4vCPU/8GB",             "200GB SSD"),
        ("APM-004", "開発環境",         "AWS ap-northeast-1",    "172.31.3.10",       "expense-dev.corp.local",      "Amazon Linux 2",    "Python 3.11 / FastAPI",  "2vCPU/4GB",             "100GB SSD"),
        ("APM-005", "開発環境",         "AWS ap-northeast-1",    "172.31.5.10",       "crm-dev.corp.local",          "Amazon Linux 2",    "React / FastAPI",         "2vCPU/4GB",             "100GB SSD"),
        ("APM-007", "本番環境",         "東京DC（大手町）",       "10.0.7.10",         "payroll-old.corp.local",      "Windows Server 2012","COBOL / WebSphere 8",   "4vCPU/16GB",            "500GB HDD"),
        ("APM-008", "本番環境",         "AWS ap-northeast-1",    "52.8.10.10",        "legal-prod.corp.local",       "Amazon Linux 2",    "Java 11 / Spring Boot",  "4vCPU/8GB",             "200GB SSD"),
        ("APM-008", "STG環境",          "AWS ap-northeast-1",    "52.8.11.10",        "legal-stg.corp.local",        "Amazon Linux 2",    "Java 11 / Spring Boot",  "2vCPU/4GB",             "100GB SSD"),
        ("APM-009", "本番環境",         "SaaS (HubSpot)",        "SaaS",              "mktg.corp.local",             "SaaS",              "HubSpot Marketing Hub",  "マネージドサービス",    "SaaS ストレージ"),
        ("APM-010", "本番環境",         "東京DC（大手町）",       "10.0.10.10",        "fac-prod.corp.local",         "CentOS 7.9",        "Tomcat 9 / Java 11",     "4vCPU/16GB",            "1TB HDD"),
        ("APM-010", "テスト環境",        "東京DC（大手町）",       "10.0.10.20",        "fac-test.corp.local",         "CentOS 7.9",        "Tomcat 9 / Java 11",     "2vCPU/8GB",             "500GB HDD"),
        ("APM-011", "本番環境",         "大阪DC（本社内）",       "10.1.11.10",        "qa-prod.corp.local",          "RHEL 7.9",          "Python 3.9 / Django",    "4vCPU/16GB",            "1TB SSD"),
        ("APM-012", "本番環境",         "AWS ap-northeast-1",    "52.12.10.10",       "cs-prod.corp.local",          "Amazon Linux 2",    "Node.js 18 / PM2",       "4vCPU/8GB",             "200GB SSD"),
        ("APM-012", "STG環境",          "AWS ap-northeast-1",    "52.12.11.10",       "cs-stg.corp.local",           "Amazon Linux 2",    "Node.js 18 / PM2",       "2vCPU/4GB",             "100GB SSD"),
        ("APM-013", "本番環境",         "SaaS (KING OF TIME)",   "SaaS",              "attendance.corp.local",       "SaaS",              "KING OF TIME",           "マネージドサービス",    "SaaS ストレージ"),
        ("APM-014", "本番環境",         "SaaS (Microsoft 365)",  "SaaS",              "portal.corp.local",           "SaaS",              "SharePoint Online",      "マネージドサービス",    "SharePoint ストレージ"),
    ]
    env_ids: dict = {}
    for row in envs:
        app_id, env_type = row[0], row[1]
        cur.execute(
            "INSERT INTO environment (env_type, location, ip, host, os, middleware, cpu_mem, storage) VALUES (?,?,?,?,?,?,?,?)",
            list(row[1:]),
        )
        env_id = cur.lastrowid
        env_ids[(app_id, env_type)] = env_id
        cur.execute(
            "INSERT INTO cmdb_rel_ci (parent_table, parent_id, child_table, child_id, relation_type_id) VALUES ('application',?,  'environment',?,?)",
            [app_id, str(env_id), has_env_id],
        )

    # ---------- 構成情報（CI） ----------
    def eid(app_id, env_type):
        return env_ids.get((app_id, env_type))

    ci_data = [
        (eid("G-CLOUD","本番環境"),  "aws-mgmt-prod",     "Other",   "aws-mgmt-prod.corp.local",    "VPC内",       None, None,None,None,None,None,"AWS","Management Console","active","AWS Organizations 管理アカウント"),
        (eid("G-CLOUD","DR環境"),    "aws-mgmt-dr",       "Other",   "aws-mgmt-dr.corp.local",      "VPC内",       None, None,None,None,None,None,"AWS","Management Console","active","DR リージョン管理コンソール"),
        (eid("G-SSO","本番環境"),    "azure-ad-tenant",   "Other",   "tenant.corp.onmicrosoft.com", "Azure",       None, None,None,None,None,None,"Microsoft","Entra ID P2","active","全社 SSO テナント / MFA 有効"),
        (eid("G-ERP","本番環境"),    "erp-ap-prod-01",    "Server",  "erp-ap-prod-01.corp.local",   "10.30.1.10",  "10.30.1.200","SUSE Linux 15","15 SP4","Intel Xeon Platinum 8380 2.3GHz 40C","256GB DDR4 ECC","2TB SSD RAID10","Fujitsu","PRIMERGY RX4770 M6","active","SAP アプリケーションサーバー"),
        (eid("G-ERP","本番環境"),    "erp-db-prod-01",    "DB",      "erp-db-prod-01.corp.local",   "10.30.1.11",  "10.30.1.201","SUSE Linux 15","15 SP4","Intel Xeon Platinum 8380 2.3GHz 40C","512GB DDR4 ECC","10TB SSD RAID10","Fujitsu","PRIMERGY RX4770 M6","active","SAP HANA DB (本番)"),
        (eid("G-HRM","開発環境"),    "hrm-sandbox-01",    "Other",   "hrm-sandbox.workday.com",     "SaaS",        None, None,None,None,None,None,"Workday","Workday HCM Sandbox","active","導入検証用 Sandbox テナント"),
        (eid("INF-DC1","本番環境"),  "dc1-vcenter-01",    "Server",  "dc1-vcenter-01.corp.local",   "10.0.0.10",   "10.0.0.200","Windows Server 2019","1809","Intel Xeon Gold 6254 3.1GHz 18C","64GB DDR4 ECC","500GB SSD","Dell","PowerEdge R740","active","vCenter Server 7.0 管理"),
        (eid("INF-DC1","本番環境"),  "dc1-core-sw-01",    "Network", "dc1-core-sw-01.corp.local",   "10.0.0.1",    "10.0.0.201",None,None,None,None,None,"Cisco","Catalyst 9500-48Y4C","active","コアスイッチ L3 / VLAN管理"),
        (eid("INF-DC1","DR環境"),    "dc1-vcenter-dr-01", "Server",  "dc1-vcenter-dr-01.corp.local","10.1.0.10",   "10.1.0.200","Windows Server 2019","1809","Intel Xeon Silver 4214R 2.4GHz 12C","32GB DDR4","300GB SSD","Dell","PowerEdge R640","active","DR vCenter Server 7.0"),
        (eid("INF-AUTH","本番環境"), "auth-dc01",         "Server",  "auth-dc01.corp.local",        "10.0.1.11",   "10.0.1.200","Windows Server 2019","1809","Intel Xeon Silver 4110 2.1GHz 8C","16GB DDR4 ECC","500GB SSD RAID1","HP","ProLiant DL380 Gen10","active","Active Directory DC1（FSMO保持）"),
        (eid("INF-AUTH","本番環境"), "auth-dc02",         "Server",  "auth-dc02.corp.local",        "10.0.1.12",   "10.0.1.201","Windows Server 2019","1809","Intel Xeon Silver 4110 2.1GHz 8C","16GB DDR4 ECC","500GB SSD RAID1","HP","ProLiant DL380 Gen10","active","Active Directory DC2（冗長）"),
        (eid("APM-001","本番環境"),  "hr-web-prod-01",    "Server",  "hr-web-prod-01.corp.local",   "10.0.2.11",   "10.0.2.200","RHEL 8.6","8.6.0","Intel Xeon Gold 6248R 3.0GHz 20C","32GB DDR4 ECC","500GB SSD","Dell","PowerEdge R650","active","APサーバー（Tomcat/Java）"),
        (eid("APM-001","本番環境"),  "hr-db-prod-01",     "DB",      "hr-db-prod-01.corp.local",    "10.0.2.12",   "10.0.2.201","RHEL 8.6","8.6.0","Intel Xeon Gold 6248R 3.0GHz 20C","64GB DDR4 ECC","2TB SSD RAID1","Dell","PowerEdge R650","active","PostgreSQL 15 マスター"),
        (eid("APM-001","本番環境"),  "hr-lb-prod-01",     "Network", "hr-lb-prod-01.corp.local",    "10.0.2.10",   "10.0.2.202",None,None,None,None,None,"F5","BIG-IP i2600","active","ロードバランサー VIP 10.0.2.10"),
        (eid("APM-001","ステージング環境"),"hr-web-stg-01","Server",  "hr-web-stg-01.corp.local",    "10.0.2.21",   "10.0.2.210","RHEL 8.6","8.6.0","Intel Xeon Silver 4214R 2.4GHz 12C","16GB DDR4","300GB SSD","Dell","PowerEdge R550","active","STG APサーバー"),
        (eid("APM-001","ステージング環境"),"hr-db-stg-01", "DB",      "hr-db-stg-01.corp.local",     "10.0.2.22",   "10.0.2.211","RHEL 8.6","8.6.0","Intel Xeon Silver 4214R 2.4GHz 12C","32GB DDR4","1TB SSD","Dell","PowerEdge R550","active","PostgreSQL 15 STG"),
        (eid("APM-001","開発環境"),  "hr-dev-ap-01",      "Server",  "hr-dev-ap-01.corp.local",     "172.31.1.11", None,"Amazon Linux 2","2","2vCPU (t3.medium)","4GB","100GB SSD","AWS","EC2 t3.medium","active","開発用 APサーバー"),
        (eid("APM-002","本番環境"),  "sfa-ap-prod-01",    "Server",  "sfa-ap-prod-01.corp.local",   "52.2.10.11",  None,"Amazon Linux 2","2","4vCPU (c6i.xlarge)","8GB","200GB SSD","AWS","EC2 c6i.xlarge","active","Node.js 18 / PM2 本番"),
        (eid("APM-002","本番環境"),  "sfa-db-prod-01",    "DB",      "sfa-db-prod-01.corp.local",   "52.2.10.12",  None,"Amazon Linux 2","2","2vCPU (db.r6g.large)","16GB","500GB SSD","AWS","RDS PostgreSQL 15 マルチAZ","active","RDS マルチAZ"),
        (eid("APM-002","テスト環境"),"sfa-ap-test-01",    "Server",  "sfa-ap-test-01.corp.local",   "52.2.11.11",  None,"Amazon Linux 2","2","2vCPU (t3.medium)","4GB","100GB SSD","AWS","EC2 t3.medium","active","テスト環境 APサーバー"),
        (eid("APM-003","本番環境"),  "inv-web-prod-01",   "Server",  "inv-web-prod-01.corp.local",  "10.1.3.11",   "10.1.3.200","CentOS 7.9","7.9.2009","Intel Xeon E5-2680v4 2.4GHz 14C","16GB DDR4","1TB HDD","Fujitsu","PRIMERGY RX2530 M4","active","Apache/PHP Webサーバー"),
        (eid("APM-003","本番環境"),  "inv-db-prod-01",    "DB",      "inv-db-prod-01.corp.local",   "10.1.3.12",   "10.1.3.201","CentOS 7.9","7.9.2009","Intel Xeon E5-2680v4 2.4GHz 14C","32GB DDR4","2TB HDD RAID5","Fujitsu","PRIMERGY RX2540 M4","active","MySQL 8.0 本番"),
        (eid("APM-003","ステージング環境"),"inv-web-stg-01","Server", "inv-web-stg-01.corp.local",   "10.1.3.21",   "10.1.3.210","CentOS 7.9","7.9.2009","Intel Xeon E5-2620v4 2.1GHz 8C","8GB DDR4","500GB HDD","Fujitsu","PRIMERGY RX2510 M2","active","STG Webサーバー"),
        (eid("APM-004","本番環境"),  "expense-ap-prod-01","Server",  "expense-ap-prod-01.corp.local","52.3.10.11",  None,"Amazon Linux 2","2","2vCPU (t3.large)","8GB","100GB SSD","AWS","EC2 t3.large","active","FastAPI 本番サーバー"),
        (eid("APM-004","本番環境"),  "expense-db-prod-01","DB",      "expense-db-prod-01.corp.local","52.3.10.12",  None,"Amazon Linux 2","2","2vCPU (db.t3.medium)","4GB","100GB SSD","AWS","RDS MySQL 8.0","active","RDS マルチAZ"),
        (eid("APM-004","開発環境"),  "expense-dev-ap-01", "Server",  "expense-dev-ap-01.corp.local","172.31.3.11", None,"Amazon Linux 2","2","1vCPU (t3.small)","2GB","50GB SSD","AWS","EC2 t3.small","active","開発用サーバー"),
        (eid("APM-005","開発環境"),  "crm-dev-ap-01",     "Server",  "crm-dev-ap-01.corp.local",    "172.31.5.11", None,"Amazon Linux 2","2","2vCPU (t3.medium)","4GB","50GB SSD","AWS","EC2 t3.medium","active","CRM 開発 APIサーバー"),
        (eid("APM-007","本番環境"),  "payroll-ap-old-01", "Server",  "payroll-ap-old-01.corp.local","10.0.7.11",   "10.0.7.200","Windows Server 2012","R2","Intel Xeon E5-2650v2 2.6GHz 8C","16GB DDR3","300GB HDD","NEC","Express5800/R120g-1E","decommission","旧給与AP（廃止済）"),
        (eid("APM-007","本番環境"),  "payroll-db-old-01", "DB",      "payroll-db-old-01.corp.local","10.0.7.12",   "10.0.7.201","Windows Server 2012","R2","Intel Xeon E5-2650v2 2.6GHz 8C","32GB DDR3","1TB HDD RAID5","NEC","Express5800/R120g-2E","decommission","旧給与DB Oracle 11g（廃止済）"),
        (eid("APM-008","本番環境"),  "legal-ap-prod-01",  "Server",  "legal-ap-prod-01.corp.local", "52.8.10.11",  None,"Amazon Linux 2","2","2vCPU (t3.large)","8GB","200GB SSD","AWS","EC2 t3.large","active","Spring Boot 本番 APサーバー"),
        (eid("APM-008","本番環境"),  "legal-db-prod-01",  "DB",      "legal-db-prod-01.corp.local", "52.8.10.12",  None,"Amazon Linux 2","2","2vCPU (db.t3.large)","8GB","500GB SSD","AWS","RDS PostgreSQL 15","active","RDS マルチAZ"),
        (eid("APM-008","STG環境"),   "legal-ap-stg-01",   "Server",  "legal-ap-stg-01.corp.local",  "52.8.11.11",  None,"Amazon Linux 2","2","1vCPU (t3.medium)","4GB","100GB SSD","AWS","EC2 t3.medium","active","STG APサーバー"),
        (eid("APM-009","本番環境"),  "hubspot-tenant",    "Other",   "corp.hubspot.com",            "SaaS",        None,None,None,None,None,None,"HubSpot","Marketing Hub Professional","active","全社 HubSpot テナント"),
        (eid("APM-010","本番環境"),  "fac-ap-prod-01",    "Server",  "fac-ap-prod-01.corp.local",   "10.0.10.11",  "10.0.10.200","CentOS 7.9","7.9.2009","Intel Xeon E5-2620v4 2.1GHz 8C","16GB DDR4","500GB HDD","NEC","Express5800/R110j-1","active","設備管理 APサーバー"),
        (eid("APM-010","本番環境"),  "fac-db-prod-01",    "DB",      "fac-db-prod-01.corp.local",   "10.0.10.12",  "10.0.10.201","CentOS 7.9","7.9.2009","Intel Xeon E5-2620v4 2.1GHz 8C","16GB DDR4","1TB HDD RAID1","NEC","Express5800/R120g-1E","active","MySQL 8.0 本番"),
        (eid("APM-011","本番環境"),  "qa-ap-prod-01",     "Server",  "qa-ap-prod-01.corp.local",    "10.1.11.11",  "10.1.11.200","RHEL 7.9","7.9","Intel Xeon E5-2680v4 2.4GHz 14C","16GB DDR4","500GB SSD","Fujitsu","PRIMERGY RX2530 M4","active","品質管理 APサーバー"),
        (eid("APM-011","本番環境"),  "qa-db-prod-01",     "DB",      "qa-db-prod-01.corp.local",    "10.1.11.12",  "10.1.11.201","RHEL 7.9","7.9","Intel Xeon E5-2680v4 2.4GHz 14C","32GB DDR4","1TB SSD RAID1","Fujitsu","PRIMERGY RX2540 M4","active","PostgreSQL 14 本番"),
        (eid("APM-012","本番環境"),  "cs-ap-prod-01",     "Server",  "cs-ap-prod-01.corp.local",    "52.12.10.11", None,"Amazon Linux 2","2","2vCPU (t3.large)","8GB","200GB SSD","AWS","EC2 t3.large","active","Zendesk API連携サーバー"),
        (eid("APM-012","本番環境"),  "cs-db-prod-01",     "DB",      "cs-db-prod-01.corp.local",    "52.12.10.12", None,"Amazon Linux 2","2","2vCPU (db.t3.medium)","4GB","100GB SSD","AWS","RDS MySQL 8.0","active","チケット分析用 DB"),
        (eid("APM-012","STG環境"),   "cs-ap-stg-01",      "Server",  "cs-ap-stg-01.corp.local",     "52.12.11.11", None,"Amazon Linux 2","2","1vCPU (t3.small)","2GB","50GB SSD","AWS","EC2 t3.small","active","STG APサーバー"),
        (eid("APM-013","本番環境"),  "kot-tenant",        "Other",   "corp.kingofTime.jp",          "SaaS",        None,None,None,None,None,None,"株式会社ヒューマンテクノロジーズ","KING OF TIME","active","全社勤怠管理テナント"),
        (eid("APM-014","本番環境"),  "sharepoint-tenant", "Other",   "corp.sharepoint.com",         "SaaS",        None,None,None,None,None,None,"Microsoft","SharePoint Online (M365 E3)","active","全社ポータル / Teams連携"),
    ]
    for (env_id, ci_name, ci_type, hostname, ip_address, bmc_ip,
         os_, os_version, cpu, memory, storage, vendor, model, status, note) in ci_data:
        if env_id is None:
            continue
        cur.execute(
            """INSERT INTO configuration_item
                   (ci_name, ci_type, hostname, ip_address, bmc_ip,
                    os, os_version, cpu, memory, storage, vendor, model, status, note)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [ci_name, ci_type, hostname, ip_address, bmc_ip,
             os_, os_version, cpu, memory, storage, vendor, model, status, note],
        )
        ci_id = cur.lastrowid
        cur.execute(
            "INSERT INTO cmdb_rel_ci (parent_table, parent_id, child_table, child_id, relation_type_id) VALUES ('environment',?,'configuration_item',?,?)",
            [str(env_id), str(ci_id), has_ci_id],
        )

    # ---------- 申請（20件） ----------
    def _chg(*items):
        return json.dumps([{"label": l, "field": f, "before": b, "after": a}
                           for l, f, b, a in items], ensure_ascii=False)

    u = user_ids
    requests = [
        {"request_id": "REQ-001", "type": "register", "application_id": "APM-008",
         "applicant_user_id": u["加藤 七子"], "applied_at": "2024-06-01 10:00", "status": "approved",
         "approver_user_id": u["佐藤 事務局"], "approved_at": "2024-06-05 14:00",
         "reason": "法務部の契約書管理をデジタル化するため DocuSign を導入する",
         "changes": None, "app_name": "法務契約管理システム", "dept": "法務部",
         "biz_owner": "加藤 七子", "new_status": "running", "start_plan": "2020-07-01", "end_plan": None},
        {"request_id": "REQ-002", "type": "register", "application_id": "APM-009",
         "applicant_user_id": u["吉田 八郎"], "applied_at": "2024-07-15 11:30", "status": "approved",
         "approver_user_id": u["佐藤 事務局"], "approved_at": "2024-07-20 09:00",
         "reason": "リードナーチャリング自動化のため HubSpot を導入する",
         "changes": None, "app_name": "マーケティング自動化ツール", "dept": "マーケティング部",
         "biz_owner": "吉田 八郎", "new_status": "running", "start_plan": "2021-10-01", "end_plan": None},
        {"request_id": "REQ-003", "type": "register", "application_id": "APM-010",
         "applicant_user_id": u["松本 十郎"], "applied_at": "2024-04-01 09:00", "status": "approved",
         "approver_user_id": u["佐藤 事務局"], "approved_at": "2024-04-10 11:00",
         "reason": "製造設備の予防保全強化のため設備管理システムを導入する",
         "changes": None, "app_name": "設備管理システム", "dept": "製造部",
         "biz_owner": "松本 十郎", "new_status": "running", "start_plan": "2019-04-01", "end_plan": None},
        {"request_id": "REQ-004", "type": "register", "application_id": "APM-011",
         "applicant_user_id": u["小林 六子"], "applied_at": "2024-09-01 10:00", "status": "approved",
         "approver_user_id": u["佐藤 事務局"], "approved_at": "2024-09-08 15:00",
         "reason": "品質データのリアルタイム可視化により不良品追跡を迅速化する",
         "changes": None, "app_name": "品質管理システム", "dept": "品質管理部",
         "biz_owner": "小林 六子", "new_status": "running", "start_plan": "2020-01-01", "end_plan": None},
        {"request_id": "REQ-005", "type": "register", "application_id": "APM-012",
         "applicant_user_id": u["木村 梅子"], "applied_at": "2025-01-10 13:00", "status": "approved",
         "approver_user_id": u["加藤 七子"], "approved_at": "2025-01-15 10:00",
         "reason": "問い合わせ対応の一元管理によりSLA遵守率を向上させる",
         "changes": None, "app_name": "カスタマーサポートチケット管理", "dept": "カスタマーサポート部",
         "biz_owner": "木村 梅子", "new_status": "running", "start_plan": "2021-07-01", "end_plan": None},
        {"request_id": "REQ-006", "type": "register", "application_id": None,
         "applicant_user_id": u["渡辺 四郎"], "applied_at": "2026-03-01 10:00", "status": "pending",
         "approver_user_id": None, "approved_at": None,
         "reason": "全社の会議室予約を一元管理し二重予約をゼロにする",
         "changes": None, "app_name": "会議室予約システム", "dept": "総務部",
         "biz_owner": "渡辺 四郎", "new_status": "plan", "start_plan": "2026-10-01", "end_plan": None},
        {"request_id": "REQ-007", "type": "register", "application_id": None,
         "applicant_user_id": u["田中 花子"], "applied_at": "2026-04-05 14:00", "status": "pending",
         "approver_user_id": None, "approved_at": None,
         "reason": "eラーニングと研修管理を統合し必須研修受講率を100%にする",
         "changes": None, "app_name": "研修管理システム", "dept": "研修部",
         "biz_owner": "田中 花子", "new_status": "plan", "start_plan": "2027-04-01", "end_plan": None},
        {"request_id": "REQ-008", "type": "update", "application_id": "APM-001",
         "applicant_user_id": u["田中 花子"], "applied_at": "2025-04-10 09:00", "status": "approved",
         "approver_user_id": u["佐藤 事務局"], "approved_at": "2025-04-12 11:00",
         "reason": "人事部長交代に伴うビジネスオーナー変更",
         "changes": _chg(("ビジネスオーナー", "business_owner", "山田 部長", "田中 花子")),
         "app_name": None, "dept": None, "biz_owner": None, "new_status": None, "start_plan": None, "end_plan": None},
        {"request_id": "REQ-009", "type": "update", "application_id": "APM-002",
         "applicant_user_id": u["高橋 二郎"], "applied_at": "2025-05-01 10:30", "status": "approved",
         "approver_user_id": u["佐藤 事務局"], "approved_at": "2025-05-07 09:00",
         "reason": "Salesforce ライセンス更新交渉によりサポート期限を2年延長",
         "changes": _chg(("廃止予定日", "end_plan", "2027-09-30", "2029-09-30")),
         "app_name": None, "dept": None, "biz_owner": None, "new_status": None, "start_plan": None, "end_plan": None},
        {"request_id": "REQ-010", "type": "update", "application_id": "APM-003",
         "applicant_user_id": u["伊藤 三郎"], "applied_at": "2026-01-20 11:00", "status": "pending",
         "approver_user_id": None, "approved_at": None,
         "reason": "購買部長交代に伴うビジネスオーナー変更申請",
         "changes": _chg(("ビジネスオーナー", "business_owner", "伊藤 旧部長", "伊藤 三郎")),
         "app_name": None, "dept": None, "biz_owner": None, "new_status": None, "start_plan": None, "end_plan": None},
        {"request_id": "REQ-011", "type": "update", "application_id": "APM-004",
         "applicant_user_id": u["鈴木 一郎"], "applied_at": "2025-03-10 14:00", "status": "rejected",
         "approver_user_id": u["清水 松子"], "approved_at": "2025-03-12 10:00",
         "reason": "経費精算システムのステータスを dev に変更申請",
         "changes": _chg(("ステータス", "status", "running", "dev")),
         "app_name": None, "dept": None, "biz_owner": None, "new_status": None, "start_plan": None, "end_plan": None},
        {"request_id": "REQ-012", "type": "update", "application_id": "APM-008",
         "applicant_user_id": u["加藤 七子"], "applied_at": "2026-02-14 09:00", "status": "pending",
         "approver_user_id": None, "approved_at": None,
         "reason": "DocuSign ライセンス延長交渉のため廃止予定日を2年延長",
         "changes": _chg(("廃止予定日", "end_plan", "2028-06-30", "2030-06-30")),
         "app_name": None, "dept": None, "biz_owner": None, "new_status": None, "start_plan": None, "end_plan": None},
        {"request_id": "REQ-013", "type": "update", "application_id": "APM-013",
         "applicant_user_id": u["田中 花子"], "applied_at": "2025-08-01 10:00", "status": "approved",
         "approver_user_id": u["佐藤 事務局"], "approved_at": "2025-08-05 11:00",
         "reason": "勤怠管理担当変更によるシステムオーナー更新",
         "changes": _chg(("システムオーナー", "system_owner", "旧担当者", "田中 花子")),
         "app_name": None, "dept": None, "biz_owner": None, "new_status": None, "start_plan": None, "end_plan": None},
        {"request_id": "REQ-014", "type": "update", "application_id": "APM-014",
         "applicant_user_id": u["渡辺 四郎"], "applied_at": "2026-03-15 13:00", "status": "pending",
         "approver_user_id": None, "approved_at": None,
         "reason": "Microsoft 365 契約更新に伴い廃止予定日を延長",
         "changes": _chg(("廃止予定日", "end_plan", "2028-03-31", "2031-03-31")),
         "app_name": None, "dept": None, "biz_owner": None, "new_status": None, "start_plan": None, "end_plan": None},
        {"request_id": "REQ-015", "type": "retire", "application_id": "APM-007",
         "applicant_user_id": u["田中 花子"], "applied_at": "2025-05-20 16:40", "status": "approved",
         "approver_user_id": u["佐藤 事務局"], "approved_at": "2025-05-21 10:00",
         "reason": "G-HRM への移行完了のため旧給与計算システムを廃止する",
         "changes": None, "app_name": None, "dept": None, "biz_owner": None,
         "new_status": None, "start_plan": None, "end_plan": "2026-03-31"},
        {"request_id": "REQ-016", "type": "retire", "application_id": "APM-005",
         "applicant_user_id": u["高橋 二郎"], "applied_at": "2025-09-01 10:00", "status": "rejected",
         "approver_user_id": u["佐藤 事務局"], "approved_at": "2025-09-03 14:00",
         "reason": "CRM 開発中断のため廃止申請",
         "changes": None, "app_name": None, "dept": None, "biz_owner": None,
         "new_status": None, "start_plan": None, "end_plan": "2025-12-31"},
        {"request_id": "REQ-017", "type": "retire", "application_id": "APM-006",
         "applicant_user_id": u["渡辺 四郎"], "applied_at": "2026-02-28 10:00", "status": "pending",
         "approver_user_id": None, "approved_at": None,
         "reason": "文書管理は社内ポータル（APM-014）に統合するため別途申請計画を廃止",
         "changes": None, "app_name": None, "dept": None, "biz_owner": None,
         "new_status": None, "start_plan": None, "end_plan": "2026-09-30"},
        {"request_id": "REQ-018", "type": "retire", "application_id": "APM-003",
         "applicant_user_id": u["伊藤 三郎"], "applied_at": "2025-11-10 09:00", "status": "rejected",
         "approver_user_id": u["清水 松子"], "approved_at": "2025-11-12 10:00",
         "reason": "在庫管理システムをグローバルシステムへ移行するため廃止申請",
         "changes": None, "app_name": None, "dept": None, "biz_owner": None,
         "new_status": None, "start_plan": None, "end_plan": "2026-06-30"},
        {"request_id": "REQ-019", "type": "retire", "application_id": "APM-010",
         "applicant_user_id": u["松本 十郎"], "applied_at": "2026-03-20 11:00", "status": "pending",
         "approver_user_id": None, "approved_at": None,
         "reason": "設備管理システムを新IoT基盤に移行するための廃止申請",
         "changes": None, "app_name": None, "dept": None, "biz_owner": None,
         "new_status": None, "start_plan": None, "end_plan": "2027-03-31"},
        {"request_id": "REQ-020", "type": "retire", "application_id": "APM-011",
         "applicant_user_id": u["小林 六子"], "applied_at": "2025-12-01 10:00", "status": "approved",
         "approver_user_id": u["加藤 七子"], "approved_at": "2025-12-05 11:00",
         "reason": "品質管理システムを刷新版へ移行完了のため旧システムを廃止する",
         "changes": None, "app_name": None, "dept": None, "biz_owner": None,
         "new_status": None, "start_plan": None, "end_plan": "2025-12-31"},
    ]
    for r in requests:
        cur.execute(
            """INSERT INTO apm_request
                   (request_id, type, application_id, applicant_user_id, applied_at, status,
                    approver_user_id, approved_at, reason, changes,
                    app_name, dept, biz_owner, new_status, start_plan, end_plan)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [r["request_id"], r["type"], r["application_id"],
             r["applicant_user_id"], r["applied_at"], r["status"],
             r["approver_user_id"], r["approved_at"], r["reason"], r["changes"],
             r["app_name"], r["dept"], r["biz_owner"],
             r["new_status"], r["start_plan"], r["end_plan"]],
        )

    # ---------- ビジネスケイパビリティ ----------
    capabilities = [
        ("HRM",    "人事",                    None,  1, None,     10),
        ("FIN",    "経理・財務",              None,  1, None,     20),
        ("SAL",    "営業・マーケティング",    None,  1, None,     30),
        ("GEN",    "総務",                    None,  1, None,     40),
        ("IT",     "IT基盤",                  None,  1, None,     50),
        ("HRM-01", "勤怠管理",        "HRM",  2, "local",   11),
        ("HRM-02", "給与計算",        "HRM",  2, "local",   12),
        ("HRM-03", "採用管理",        "HRM",  2, "local",   13),
        ("HRM-04", "人事・労務管理",  "HRM",  2, "local",   14),
        ("HRM-05", "研修・人材開発",  "HRM",  2, "local",   15),
        ("FIN-01", "会計管理",        "FIN",  2, "global",  21),
        ("FIN-02", "経費管理",        "FIN",  2, "local",   22),
        ("FIN-03", "予算管理",        "FIN",  2, "global",  23),
        ("FIN-04", "財務報告",        "FIN",  2, "global",  24),
        ("SAL-01", "顧客管理（CRM）", "SAL",  2, "global",  31),
        ("SAL-02", "営業支援（SFA）", "SAL",  2, "global",  32),
        ("SAL-03", "マーケティング自動化", "SAL", 2, "global", 33),
        ("SAL-04", "リード管理",      "SAL",  2, "global",  34),
        ("GEN-01", "文書管理",            "GEN", 2, "local",   41),
        ("GEN-02", "設備・施設管理",      "GEN", 2, "local",   42),
        ("GEN-03", "社内コミュニケーション", "GEN", 2, "local", 43),
        ("IT-01",  "クラウド基盤",         "IT",  2, "global",  51),
        ("IT-02",  "認証・セキュリティ",   "IT",  2, "global",  52),
        ("IT-03",  "ITサービス管理",       "IT",  2, "global",  53),
        ("IT-04",  "基幹システム統合",     "IT",  2, "global",  54),
    ]
    for (cap_id, cap_name, parent_id, level, scope, sort_order) in capabilities:
        cur.execute(
            "INSERT INTO business_capability (capability_id, capability_name, parent_id, level, scope, sort_order) VALUES (?,?,?,?,?,?)",
            [cap_id, cap_name, parent_id, level, scope, sort_order],
        )

    cap_app_links = [
        ("HRM-01", "APM-013"), ("HRM-01", "APM-015"), ("HRM-01", "APM-021"),
        ("HRM-02", "APM-007"), ("HRM-02", "G-HRM"),
        ("HRM-04", "APM-001"), ("HRM-04", "G-HRM"),
        ("FIN-01", "G-ERP"),
        ("FIN-02", "APM-004"), ("FIN-02", "APM-020"),
        ("FIN-03", "G-ERP"),
        ("SAL-01", "APM-005"),
        ("SAL-02", "APM-002"),
        ("SAL-03", "APM-009"), ("SAL-04", "APM-009"),
        ("GEN-01", "APM-006"), ("GEN-01", "APM-019"), ("GEN-01", "APM-016"),
        ("GEN-02", "APM-010"),
        ("GEN-03", "APM-014"), ("GEN-03", "APM-022"),
        ("IT-01",  "G-CLOUD"), ("IT-01",  "INF-DC1"),
        ("IT-02",  "G-SSO"),   ("IT-02",  "INF-AUTH"),
        ("IT-03",  "APM-012"),
        ("IT-04",  "G-ERP"),
    ]
    for (cap_id, app_id) in cap_app_links:
        cur.execute(
            "INSERT INTO cmdb_rel_ci (parent_table, parent_id, child_table, child_id, relation_type_id) VALUES ('business_capability',?,'application',?,?)",
            [cap_id, app_id, realizes_id],
        )

    conn.commit()
    conn.close()
    print("✓ マスターデータを投入しました")
    print(f"  部署: {len(departments)}件, ユーザー: {len(users)}件")
    print(f"  アプリケーション: {len(apps)}件, 環境: {len(envs)}件")
    print(f"  CI: {len(ci_data)}件, 依存関係: {len(deps)}件, 申請: {len(requests)}件")
    print(f"  ケイパビリティ: {len(capabilities)}件, 紐付け: {len(cap_app_links)}件")


if __name__ == "__main__":
    seed_master()
