import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
import html

# .envファイルを読み込み
load_dotenv()

st.set_page_config(page_title="金融商品説明事項チェックシステム", layout="wide")

st.title("金融商品説明事項チェックシステム")

# セッション状態の初期化
if "source_text" not in st.session_state:
    st.session_state.source_text = ""
if "compliance_results" not in st.session_state:
    st.session_state.compliance_results = []

# 表示高さを固定値に設定
DISPLAY_HEIGHT = 650

# API Key設定
# Streamlit Cloudではst.secretsを使用
gemini_api_key = None
if "GEMINI_API_KEY" in st.secrets:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
else:
    # ローカル環境では.envファイルから読み込み
    gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    st.error("❌ API Keyが見つかりません。Streamlit Cloudの場合はSecretsに、ローカルの場合は.envファイルにGEMINI_API_KEYを設定してください。")
    st.stop()


def check_compliance(text: str) -> list:
    """説明事項チェックを実行"""
    try:
        genai.configure(api_key=gemini_api_key)
        # NOTE: 将来的に gemini-2.5-pro に変更予定
        model = genai.GenerativeModel("gemini-2.5-pro")

        prompt = f"""
金融商品の説明文書から以下の20項目についてチェックを行ってください。

【チェック項目】
1. 商品名称・種類の明確な説明
2. 元本欠損（元本割れ）のおそれがある旨の説明
3. 価格変動リスクの説明
4. 金利変動リスクの説明
5. 為替変動リスクの説明（該当商品の場合）
6. 最大損失額・想定損失額の説明
7. 購入時手数料の説明
8. 運用管理費用（信託報酬）の説明
9. 換金時手数料・制約の説明
10. 投資経験の確認
11. 投資目的の確認
12. リスク許容度の確認
13. 顧客属性に適した商品であることの確認
14. 商品内容の理解確認
15. リスクの理解確認
16. 手数料の理解確認
17. 契約締結前交付書面の交付
18. 投資対象・運用方針の説明
19. 換金可能時期・制限の説明
20. 最終的な購入意思の確認

【テキスト】
{text}

【出力形式】
以下のJSON形式で出力してください：
{{
    "compliance_results": [
        {{
            "item_no": 項目番号,
            "item_name": "項目名",
            "status": "○" または "△" または "×",
            "confidence": 信頼度（0-100の整数）,
            "snippet": "該当箇所の文章（改行は...で置換して1行で出力）",
            "reason": "判定理由の簡潔な説明"
        }}
    ]
}}

判定基準：
- ○：ヒアリングできた（質問せずとも相手が話してくれた、または、正しく質問して相手が明確に回答した）
  信頼度：100
- △：ヒアリングしたが曖昧な回答が返ってきた、または、相手が質問したがこちらが曖昧な返答をした
  信頼度：10-90（説明の質に応じて。良い説明なら90に近く、不十分なら10に近く）
- ×：話として出てこなかった、または、的外れな回答をした
  信頼度：100

JSONのみを出力し、他の説明は不要です。
"""

        response = model.generate_content(prompt)

        # JSONパース
        try:
            json_text = response.text.strip()
            if json_text.startswith("```json"):
                json_text = json_text[7:]
            if json_text.endswith("```"):
                json_text = json_text[:-3]

            result = json.loads(json_text.strip())
            return result.get("compliance_results", [])
        except (json.JSONDecodeError, KeyError):
            return []

    except Exception as e:
        st.error(f"エラー: {e}")
        return []


def create_interactive_display(text: str, results: list, height: int = 650) -> str:
    """インタラクティブな表示を生成（st.rerun不要）"""
    escaped_text = html.escape(text)
    results_json = json.dumps(results, ensure_ascii=False)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f5f5f5;
            }}
            .main-container {{
                max-width: 100%;
                margin: 0 auto;
            }}
            
            /* 上段のスタイル */
            .top-section {{
                display: flex;
                gap: 20px;
                margin-bottom: 20px;
            }}
            
            /* 下段のスタイル */
            .bottom-section {{
                display: flex;
                gap: 20px;
            }}
            
            .left-panel {{
                flex: 1.2;
            }}
            
            .right-panel {{
                flex: 1;
            }}
            
            .section-box {{
                background: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            
            #text-container {{
                height: {height}px;
                overflow-y: auto;
                padding: 20px;
                border: 1px solid #ddd;
                border-radius: 5px;
                line-height: 1.6;
                font-size: 14px;
                background: white;
            }}
            
            .results-container {{
                height: {height}px;
                overflow-y: auto;
                padding: 10px;
            }}
            
            .result-card {{
                padding: 12px;
                border-radius: 8px;
                margin-bottom: 8px;
                border-left: 4px solid;
                position: relative;
            }}
            
            .result-card.ok {{
                background-color: #d4edda;
                border-left-color: #155724;
            }}
            
            .result-card.partial {{
                background-color: #fff3cd;
                border-left-color: #856404;
            }}
            
            .result-card.ng {{
                background-color: #f8d7da;
                border-left-color: #721c24;
            }}
            
            .result-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 5px;
            }}
            
            .result-title {{
                margin: 0;
                font-size: 14px;
                flex: 1;
            }}
            
            .confidence-badge {{
                padding: 2px 6px;
                border-radius: 8px;
                font-size: 10px;
                color: white;
            }}
            
            .result-content {{
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            
            .result-reason {{
                margin: 0;
                color: #666;
                font-size: 12px;
                flex: 1;
            }}
            
            .highlight-button {{
                padding: 2px 8px;
                height: 25px;
                font-size: 11px;
                background-color: #f0f2f6;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                cursor: pointer;
                transition: background-color 0.2s;
            }}
            
            .highlight-button:hover {{
                background-color: #e5e7eb;
            }}
            
            .highlight {{
                background-color: #ffeb3b;
                padding: 2px 4px;
                font-weight: bold;
                border-radius: 3px;
            }}
            
            h3 {{
                margin-top: 0;
                font-size: 16px;
                color: #1f2937;
            }}
            
            .info-text {{
                color: #6b7280;
                font-size: 14px;
                margin: 10px 0;
            }}
        </style>
    </head>
    <body>
        <div class="main-container">
            <div class="bottom-section">
                <div class="left-panel">
                    <div class="section-box">
                        <h3>📄 全文表示</h3>
                        <div id="text-container">{escaped_text.replace(chr(10), "<br>")}</div>
                        <div class="info-text">文字数: {len(text)}文字</div>
                    </div>
                </div>
                <div class="right-panel">
                    <div class="section-box">
                        <h3>🔍 詳細チェック結果</h3>
                        <div class="results-container" id="results-container"></div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            const results = {results_json};
            let currentHighlight = null;
            let lastScrollPosition = 0;
            
            const textContainer = document.getElementById('text-container');
            const resultsContainer = document.getElementById('results-container');
            
            // スクロール位置を記憶
            textContainer.addEventListener('scroll', function() {{
                lastScrollPosition = textContainer.scrollTop;
            }});
            
            // 文ごとの区切り関数
            function splitIntoSentences(text) {{
                // 句読点、改行、省略記号で区切り、空文字を除去
                return text.split(/[。．！？\\n]|\\.\\.\\./g).filter(s => s.trim().length > 0);
            }}
            
            // テキスト正規化関数（空白・改行を統一）
            function normalizeText(text) {{
                return text.replace(/\\s+/g, ' ').trim();
            }}
            
            // 改善されたハイライト関数
            function highlightSnippet(snippet) {{
                if (!snippet) return;
                
                // 現在のスクロール位置を保存
                const currentScroll = textContainer.scrollTop;
                
                // 同じハイライトをクリックした場合はクリア
                if (currentHighlight === snippet) {{
                    currentHighlight = null;
                    restoreText();
                    textContainer.scrollTop = currentScroll;
                    return;
                }}
                
                // テキストを元に戻してから新しいハイライトを適用
                restoreText();
                
                // 文ごとに分割してハイライト処理
                const sentences = splitIntoSentences(snippet);
                const textContent = textContainer.innerHTML;
                let highlightedText = textContent;
                let foundMatch = false;
                
                // 各文について一致を試行
                sentences.forEach((sentence, index) => {{
                    const trimmedSentence = sentence.trim();
                    // 短すぎる文や話者ラベルのみの文はスキップ
                    if (trimmedSentence.length < 3 || /^(顧客|店員)[：:]?$/.test(trimmedSentence)) return;
                    
                    // スピーカーラベルと記号を除去して検索用文章を作成
                    const cleanedSentence = trimmedSentence
                        .replace(/^(顧客|店員)[：:]\\s*/, '')    // 話者ラベルを除去
                        .replace(/^[\\s\\.\\-…]+/, '')         // 先頭記号を除去
                        .replace(/[。．！？]+$/, '')          // 末尾句読点を除去
                        .trim();
                    const searchSentence = cleanedSentence || trimmedSentence;
                    
                    // 正規化してマッチング
                    const normalizedSentence = normalizeText(searchSentence);
                    const escapedSentence = normalizedSentence.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&');
                    
                    // 複数のマッチングパターンを試行
                    const patterns = [
                        // 完全一致
                        new RegExp(escapedSentence, 'gi'),
                        // 前後の空白を考慮
                        new RegExp(`\\\\s*${{escapedSentence}}\\\\s*`, 'gi'),
                        // HTMLタグ間の改行を考慮
                        new RegExp(escapedSentence.replace(/\\s+/g, '[\\\\s<br>]*'), 'gi')
                    ];
                    
                    for (let pattern of patterns) {{
                        if (pattern.test(highlightedText)) {{
                            const highlightId = index === 0 ? 'highlight-target' : `highlight-${{index}}`;
                            highlightedText = highlightedText.replace(pattern, (match) => {{
                                foundMatch = true;
                                return `<span class="highlight" id="${{highlightId}}">${{match}}</span>`;
                            }});
                            break;
                        }}
                    }}
                }});
                
                // ハイライトが適用された場合のみテキストを更新
                if (foundMatch) {{
                    textContainer.innerHTML = highlightedText;
                    
                    // 最初のハイライト要素へスクロール
                    setTimeout(() => {{
                        const highlightElement = document.getElementById('highlight-target');
                        if (highlightElement) {{
                            const elementTop = highlightElement.offsetTop;
                            const containerHeight = textContainer.clientHeight;
                            const targetScrollTop = elementTop - (containerHeight / 2) + (highlightElement.clientHeight / 2);
                            
                            textContainer.scrollTo({{
                                top: Math.max(0, targetScrollTop),
                                behavior: 'smooth'
                            }});
                        }}
                    }}, 50);
                    
                    currentHighlight = snippet;
                }} else {{
                    // マッチしない場合は従来の方法を試行
                    const escapedSnippet = snippet.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&');
                    const fallbackPattern = new RegExp(escapedSnippet.replace(/\\s+/g, '[\\\\s<br>]*'), 'gi');
                    if (fallbackPattern.test(textContent)) {{
                        highlightedText = textContent.replace(fallbackPattern, 
                            `<span class="highlight" id="highlight-target">${{snippet}}</span>`);
                        textContainer.innerHTML = highlightedText;
                        currentHighlight = snippet;
                    }}
                }}
            }}
            
            // テキストを元に戻す
            function restoreText() {{
                textContainer.innerHTML = `{escaped_text.replace(chr(10), "<br>")}`;
            }}
            
            // 結果カードを作成
            function createResultCards() {{
                results.forEach((result, index) => {{
                    const statusClass = result.status === '○' ? 'ok' : 
                                      result.status === '△' ? 'partial' : 'ng';
                    const statusIcon = result.status === '○' ? '✅' : 
                                     result.status === '△' ? '⚠️' : '❌';
                    const statusColor = result.status === '○' ? '#155724' : 
                                      result.status === '△' ? '#856404' : '#721c24';
                    
                    const card = document.createElement('div');
                    card.className = `result-card ${{statusClass}}`;
                    
                    card.innerHTML = `
                        <div class="result-header">
                            <h6 class="result-title" style="color: ${{statusColor}}">
                                ${{statusIcon}} ${{result.item_no}}. ${{result.item_name}}
                            </h6>
                            <span class="confidence-badge" style="background-color: ${{statusColor}}">
                                信頼度: ${{result.confidence}}%
                            </span>
                        </div>
                        <div class="result-content">
                            <p class="result-reason">${{result.reason}}</p>
                            ${{result.snippet ? 
                                `<button class="highlight-button" onclick="highlightSnippet('${{result.snippet.replace(/'/g, "\\\\'")}}')">
                                    📍 該当箇所
                                </button>` : ''
                            }}
                        </div>
                    `;
                    
                    resultsContainer.appendChild(card);
                }});
            }}
            
            // 初期化
            createResultCards();
        </script>
    </body>
    </html>
    """

    return html_content


# ===== 上段: アップロード（左）+ サマリー（右） =====
st.subheader("📤 入力・分析実行")
top_col1, top_col2 = st.columns([1.2, 1])

# 上段左: ファイルアップロードセクション
with top_col1:
    st.markdown("**📄 ファイルアップロード**")

    # ファイルアップロード
    uploaded_file = st.file_uploader(
        "テキストファイルをアップロード",
        type=["txt"],
        help="金融商品の説明文が記載されたテキストファイルを選択してください",
    )

    if uploaded_file is not None:
        # ファイル内容を読み込み
        file_content = str(uploaded_file.read(), "utf-8")
        st.session_state.source_text = file_content
        st.success(f"✅ ファイル「{uploaded_file.name}」を読み込みました")

    # 直接入力セクション（折りたたみ）
    with st.expander("📝 直接入力する場合はこちら"):
        input_text = st.text_area(
            "テキストを入力",
            height=120,
            placeholder="ファイルアップロードの代わりに、ここに直接入力することもできます...",
        )

        if st.button("テキストを設定"):
            if input_text:
                st.session_state.source_text = input_text
                st.success("✅ テキストを設定しました")

# 上段右: 分析実行 + サマリー
with top_col2:
    st.markdown("**🔍 分析実行・結果サマリー**")

    if st.session_state.source_text:
        # 分析実行ボタン
        if st.button("🔍 分析実行", type="primary", use_container_width=True):
            with st.spinner("AI分析中..."):
                results = check_compliance(st.session_state.source_text)
                if results:
                    st.session_state.compliance_results = results
                    # 結果サマリー
                    ok_count = len([r for r in results if r["status"] == "○"])
                    partial_count = len([r for r in results if r["status"] == "△"])
                    ng_count = len([r for r in results if r["status"] == "×"])
                    st.success(
                        f"✅ チェック完了: ○{ok_count}件 △{partial_count}件 ×{ng_count}件"
                    )
                else:
                    st.warning("分析結果を取得できませんでした")

        # サマリー表示
        if st.session_state.compliance_results:
            st.markdown("**📊 結果サマリー**")

            # 結果をカウント
            ok_items = [
                r for r in st.session_state.compliance_results if r["status"] == "○"
            ]
            partial_items = [
                r for r in st.session_state.compliance_results if r["status"] == "△"
            ]
            ng_items = [
                r for r in st.session_state.compliance_results if r["status"] == "×"
            ]

            # サマリー表示（3列レイアウト）
            col_ok, col_partial, col_ng = st.columns(3)
            with col_ok:
                st.metric(
                    "✅ 適合",
                    f"{len(ok_items)}件",
                    f"{len(ok_items) / len(st.session_state.compliance_results) * 100:.1f}%",
                )
            with col_partial:
                st.metric(
                    "⚠️ 部分適合",
                    f"{len(partial_items)}件",
                    f"{len(partial_items) / len(st.session_state.compliance_results) * 100:.1f}%",
                )
            with col_ng:
                st.metric(
                    "❌ 不適合",
                    f"{len(ng_items)}件",
                    f"{len(ng_items) / len(st.session_state.compliance_results) * 100:.1f}%",
                )
    else:
        st.info("ファイルをアップロードして開始してください")

# 区切り線
st.markdown("---")

# ===== 下段: インタラクティブ表示 =====
st.subheader("📋 詳細表示")

if st.session_state.source_text and st.session_state.compliance_results:
    # インタラクティブな表示を生成
    html_content = create_interactive_display(
        st.session_state.source_text,
        st.session_state.compliance_results,
        DISPLAY_HEIGHT,
    )
    components.html(html_content, height=DISPLAY_HEIGHT + 100)
elif st.session_state.source_text:
    # 結果がない場合はテキストのみ表示
    col1, col2 = st.columns([1.2, 1])
    with col1:
        st.markdown("**📄 全文表示**")
        st.text_area(
            "全文",
            st.session_state.source_text,
            height=DISPLAY_HEIGHT,
            disabled=True,
            label_visibility="collapsed",
        )
    with col2:
        st.info(
            "分析結果がありません。上記の「分析実行」ボタンをクリックしてください。"
        )
else:
    st.info("テキストが入力されていません")

# フッター
st.markdown("---")
st.caption(
    "💡 該当箇所ボタンをクリックすると、左側の全文で現在見ている位置からその箇所まで滑らかにスクロールし、黄色くハイライト表示されます。"
)
