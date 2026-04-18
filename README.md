# UC Paper Bot

PubMed から潰瘍性大腸炎（UC）・IBD 関連の新着論文を自動取得し、Claude Sonnet で日本語解説を生成して Discord に投稿する bot です。

- **実行基盤**: GitHub Actions（cron 実行）
- **API**: PubMed E-utilities（無料）+ Anthropic Claude Sonnet 4.5
- **想定コスト**: 約 **$3〜6 / 月**（6 論文/日の場合）

## 虫垂 bot 版との違い

この UC 版は以下の点で強化されています:

| 項目 | 虫垂 bot | UC bot |
|---|---|---|
| 検索フィルタ | MeSH + キーワード | MeSH + **RCT/meta-analysis/top journals 限定** |
| Publication Type | 取得のみ | **色分け・タイプ別バッジ表示** |
| 解説の視点 | 消化器一般 | **STRIDE-II 目標・生物学的製剤アルゴリズム・粘膜治癒/組織学的寛解** |
| ヘッダー | 件数のみ | **論文タイプ内訳も表示** |
| 1日の処理本数 | 5 本 | 6 本（論文数が多いため） |

UC は論文数が非常に多いため、**エビデンスレベルの高いもの（RCT/meta-analysis）や主要ジャーナル掲載分に絞る**設計にしています。

---

## 構成

```
uc-paper-bot/
├── .github/
│   └── workflows/
│       └── daily_digest.yml     # GitHub Actions: 毎朝 JST 07:30 に実行
├── src/
│   ├── main.py                  # エントリポイント
│   ├── config.py                # 設定・検索クエリ
│   ├── pubmed_client.py         # PubMed API（Publication Type も取得）
│   ├── claude_client.py         # Claude Sonnet API（UC 特化プロンプト）
│   └── discord_client.py        # Discord Webhook（論文タイプで色分け）
├── data/
│   └── posted_pmids.json        # 投稿済み PMID 管理
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 導入手順

### 1. Discord Webhook の作成

1. Discord で投稿先のサーバー／チャンネルを開く
2. チャンネル右の歯車アイコン（チャンネル編集）→ **連携サービス** → **ウェブフック**
3. **新しいウェブフック** をクリック → 名前を設定（例: `UC Paper Bot`）
4. **ウェブフック URL をコピー** ボタンで URL を控える

> 💡 虫垂 bot と **別チャンネル** にすることをお勧めします。UC は投稿数が多いため、混ぜると虫垂の情報が流れてしまいます。

### 2. Anthropic API キーの取得

虫垂 bot と **同じ API キー** で構いません（usage はリポジトリ単位ではなくキー単位で集計）。
新規の場合:

1. <https://console.anthropic.com/> にログイン
2. **API Keys** → **Create Key**
3. **Billing** で支払い方法を登録し、$5〜20 をチャージ
4. **Usage limits** で月額上限を設定（両 bot 合算で $10〜15 程度が目安）

### 3. PubMed API キー（任意・推奨）

1. <https://account.ncbi.nlm.nih.gov/> にログイン
2. **Account Settings** → **API Key Management** で発行
3. 虫垂 bot と同じキーを使い回せます

### 4. GitHub リポジトリの作成

**別リポジトリとして作成する**ことを推奨します（Actions のログ・state 管理が独立するため）:

```bash
cd uc-paper-bot
git init
git add .
git commit -m "initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/uc-paper-bot.git
git push -u origin main
```

### 5. GitHub Secrets の登録

リポジトリの **Settings** → **Secrets and variables** → **Actions** → **New repository secret** で以下を登録：

| Secret 名 | 値 | 必須 |
|---|---|---|
| `ANTHROPIC_API_KEY` | `sk-ant-...` | ✅ |
| `DISCORD_WEBHOOK_URL` | UC 用チャンネルの Webhook | ✅ |
| `PUBMED_API_KEY` | NCBI で発行したキー | 任意 |
| `PUBMED_EMAIL` | 自分のメールアドレス | 任意 |

### 6. 初回実行テスト

1. リポジトリの **Actions** タブへ移動
2. 左メニューから **Daily UC Paper Digest** を選択
3. **Run workflow** → **Run workflow** で手動実行
4. Discord に論文解説が流れてくれば成功 🎉

---

## ローカル動作確認（任意）

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# .env を編集して API キー等を記入

python src/main.py
```

---

## カスタマイズ

### 検索クエリの変更

`src/config.py` の `PUBMED_QUERY` を編集します。鷹将さんの研究テーマに応じて:

- **IBD 全般（CD も含める）**:
  ```python
  '"inflammatory bowel diseases"[MeSH Terms]'
  ```

- **PSC-IBD 関連**（鷹将さんの関心領域）:
  ```python
  '("colitis, ulcerative"[MeSH] OR "inflammatory bowel diseases"[MeSH]) '
  'AND ("cholangitis, sclerosing"[MeSH] OR "PSC"[Title/Abstract])'
  ```

- **粘膜治癒・histologic remission 関連のみ**:
  ```python
  '"colitis, ulcerative"[MeSH] AND '
  '("mucosal healing"[Title/Abstract] OR "histologic remission"[Title/Abstract] '
  'OR "endoscopic remission"[Title/Abstract])'
  ```

- **生物学的製剤・低分子薬の治療研究のみ**:
  ```python
  '"colitis, ulcerative"[MeSH] AND '
  '("biological therapy"[MeSH] OR "ustekinumab" OR "vedolizumab" OR '
  '"tofacitinib" OR "upadacitinib" OR "ozanimod" OR "risankizumab" OR '
  '"mirikizumab" OR "etrasimod" OR "guselkumab")'
  ```

- **UC 関連の腸内細菌/バイオマーカー研究**（大学院研究テーマ候補）:
  ```python
  '"colitis, ulcerative"[MeSH] AND '
  '("gut microbiota"[MeSH] OR "microbiome"[Title/Abstract] OR '
  '"metagenomics"[Title/Abstract] OR "WGS"[Title/Abstract])'
  ```

### 実行頻度の変更

`.github/workflows/daily_digest.yml` の `cron` を編集:

| 用途 | cron 式 (UTC) | JST |
|---|---|---|
| 毎朝 7:30（デフォルト） | `30 22 * * *` | 毎日 07:30 |
| 週1（月曜朝） | `30 22 * * 1` | 月曜 07:30 |
| 平日のみ | `30 22 * * 1-5` | 平日 07:30 |

### 処理本数の変更

`src/config.py` の `MAX_PAPERS_PER_RUN` を変更。デフォルトは 6。RCT/meta のみに絞る設計なので、実際にヒットするのは日によって 0〜6 件程度のはずです。

### 解説の深さ変更

`src/claude_client.py` の `SYSTEM_PROMPT` を編集。鷹将さんは専門性が高いので、より詳細にしたい場合は「全体で 900-1100 字程度」を「1200-1400 字程度」に、`max_tokens` を `1800 → 2200` に変更すると良いです。

---

## コスト試算

Claude Sonnet 4.5（$3/Mtok input, $15/Mtok output）で概算:

| 項目 | 使用量/日 | 月額 |
|---|---|---|
| 入力トークン（abstract + prompt、6論文/日） | ~7,000 tok | ~$0.63 |
| 出力トークン（日本語解説、6論文/日） | ~5,500 tok | ~$2.48 |
| **合計** | | **~$3.10/月** |

虫垂 bot（~$2.25/月）と合算して **月 $5〜6 程度**。$20 予算の 1/4 以下です。

---

## 論文タイプ別の色分け

Discord の embed が Publication Type に応じて色分けされます:

| タイプ | 色 | バッジ |
|---|---|---|
| RCT | 🟢 緑 | 🎯 RCT |
| Meta-Analysis / Systematic Review | 🔵 青 | 📊 Meta-Analysis / 📚 Systematic Review |
| Phase III Trial | 🟢 濃い緑 | 💊 Phase III Trial |
| Multicenter Study | 🟣 紫 | 🏥 Multicenter |
| Observational Study | 🟠 オレンジ | 👁️ Observational |
| Review | ⚪ グレー | 📖 Review |
| Case Report | 🔴 赤 | 📝 Case Report |

一目でエビデンスレベルが把握できます。

---

## トラブルシューティング

| 症状 | 対処 |
|---|---|
| Actions で `Missing ANTHROPIC_API_KEY` エラー | Secrets が正しく登録されているか確認 |
| Discord に何も投稿されない | Webhook URL が正しいか、チャンネル権限を確認 |
| `posted_pmids.json` が commit されない | Settings → Actions → General → Workflow permissions で **Read and write permissions** を有効化 |
| 論文が全部既読判定される | `data/posted_pmids.json` を空配列 `[]` にリセット |
| PubMed から 429 エラー | `PUBMED_API_KEY` を設定するか、実行頻度を下げる |
| ヒット論文が少なすぎる | `PUBMED_QUERY` のフィルタを緩める（RCT/meta 限定を外す、ジャーナル追加など） |
| ヒット論文が多すぎる | `"last 7 days"` → `"last 3 days"` に変更 |

---

## 発展案

鷹将さんの既存 bot 群との連携アイデア:

- **週間サマリー bot**: 週末に直近 1 週間の UC 論文を横断して「今週のハイライト」を生成（大規模 RCT の結果、新薬承認、ガイドライン改訂など）
- **Guideline Watcher**: ECCO / AGA / 日本消化器病学会のガイドライン更新を監視
- **Clinical Trial Watcher**: ClinicalTrials.gov で UC 関連の新規登録試験を追跡
- **Journal Club 支援**: 1 本を選んで PICO・bias 評価・統計手法の妥当性まで詳細解説
- **PSC-IBD 専用 bot**: PSC-IBD 論文に絞った別 instance として運用
- **Microbiome/WGS 専用 bot**: 大学院研究テーマ（腸内細菌・メタゲノム）に絞った論文監視

---

## ライセンス

MIT（必要に応じて変更してください）
