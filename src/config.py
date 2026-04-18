"""設定ファイル。環境変数と検索クエリを一元管理。"""
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# PubMed 検索クエリ（UC: 潰瘍性大腸炎）
# ------------------------------------------------------------
# UC は論文数が多いため、研究デザイン・雑誌でフィルタを入れています。
# 必要に応じて編集してください。
#
# 代替クエリ例:
#   - IBD 全般（CDも含む）:
#       '"inflammatory bowel diseases"[MeSH Terms]'
#   - 治療関連のみ:
#       ' AND ("biological therapy"[MeSH] OR "drug therapy"[MeSH])'
#   - Top journal 限定:
#       ' AND ("Gastroenterology"[Journal] OR "Gut"[Journal] OR
#              "Lancet"[Journal] OR "N Engl J Med"[Journal] OR
#              "J Crohns Colitis"[Journal] OR "Am J Gastroenterol"[Journal])'
#   - 鷹将さんの研究テーマ候補（PSC-IBD・粘膜治癒・腸内細菌など）に合わせる:
#       ' AND ("mucosal healing"[tiab] OR "gut microbiota"[tiab] OR
#              "primary sclerosing cholangitis"[MeSH])'
# ============================================================
PUBMED_QUERY = (
    '('
    '"colitis, ulcerative"[MeSH Terms] '
    'OR "ulcerative colitis"[Title/Abstract] '
    'OR "UC"[Title]'
    ') '
    'AND ('
    'Randomized Controlled Trial[PT] '
    'OR Meta-Analysis[PT] '
    'OR Systematic Review[PT] '
    'OR Clinical Trial, Phase III[PT] '
    'OR Clinical Trial, Phase II[PT] '
    'OR "Gastroenterology"[Journal] '
    'OR "Gut"[Journal] '
    'OR "Lancet"[Journal] '
    'OR "Lancet Gastroenterol Hepatol"[Journal] '
    'OR "N Engl J Med"[Journal] '
    'OR "J Crohns Colitis"[Journal] '
    'OR "Am J Gastroenterol"[Journal] '
    'OR "Clin Gastroenterol Hepatol"[Journal] '
    'OR "Aliment Pharmacol Ther"[Journal] '
    'OR "Inflamm Bowel Dis"[Journal]'
    ') '
    'AND ("last 7 days"[PDat]) '
    'AND (English[Language] OR Japanese[Language])'
)

# 1回の実行で処理する最大論文数（コスト制御）
# UC は論文数が多いので 5-7 本程度を推奨
MAX_PAPERS_PER_RUN = 6

# ============================================================
# API 設定
# ============================================================
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
PUBMED_API_KEY = os.getenv("PUBMED_API_KEY", "")
PUBMED_EMAIL = os.getenv("PUBMED_EMAIL", "")

# Claude モデル（最新の Sonnet）
CLAUDE_MODEL = "claude-sonnet-4-5"

# 投稿済み PMID を記録するファイル
POSTED_PMIDS_FILE = "data/posted_pmids.json"


def validate() -> None:
    """必須環境変数のチェック"""
    missing = []
    if not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    if not DISCORD_WEBHOOK_URL:
        missing.append("DISCORD_WEBHOOK_URL")
    if missing:
        raise RuntimeError(
            f"必須の環境変数が設定されていません: {', '.join(missing)}\n"
            f".env ファイルまたは GitHub Secrets を確認してください。"
        )
