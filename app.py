import streamlit as st
import os
import random
import csv

st.set_page_config(layout="wide")

# CHAR_CONFIG はスロットの「枠の役割(PREFIX)」とCSVの指定のみ
CHAR_CONFIG = {
    # エネミー側（スロット枠）
    "boss": {"prefix": "[ボス]", "type": "enemy", "csv": "boss.csv"},
    "za1":  {"prefix": "[雑魚1]", "type": "enemy", "csv": "za1.csv"},
    "za2":  {"prefix": "[雑魚2]", "type": "enemy", "csv": "za2.csv"},
    "za3":  {"prefix": "[雑魚3]", "type": "enemy", "csv": "za3.csv"},
    "za4":  {"prefix": "[雑魚4]", "type": "enemy", "csv": "za4.csv"},
    "za5":  {"prefix": "[雑魚5]", "type": "enemy", "csv": "za5.csv"},
    "za6":  {"prefix": "[雑魚6]", "type": "enemy", "csv": "za6.csv"},
    
    # プレイヤー側（スロット枠）
    "pc1":  {"prefix": "[PC1]", "type": "pc", "csv": "sen.csv"},
    "pc2":  {"prefix": "[PC2]", "type": "pc", "csv": "tou.csv"},
    "pc3":  {"prefix": "[PC3]", "type": "pc", "csv": "sou.csv"},
    "pc4":  {"prefix": "[PC4]", "type": "pc", "csv": "mah.csv"},
}

# CSVファイルから「名前」と「固定手札」「デッキ中身」を構築する関数
def load_deck_from_csv(filename, char_type):
    pool = []
    fixed_hand = [] 
    default_names = {
        "boss": "山賊頭領", "za1": "山賊小悪党", "za2": "山賊の弓兵", 
        "za3": "山賊の邪術", "za4": "山賊の暗殺者", "za5": "山賊の盾兵", "za6": "山賊の犬",
        "pc1": "戦士", "pc2": "盗賊", "pc3": "僧侶", "pc4": "魔法使い"
    }
    base = os.path.splitext(filename)[0]
    deck_title = default_names.get(base, "名称未設定")
    
    if os.path.exists(filename):
        try:
            with open(filename, encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                
                # 1行目を「キャラクター名」として取得
                first_row = next(reader)
                if first_row and len(first_row) > 0 and first_row[0].strip():
                    deck_title = first_row[0].strip()
                
                # 2行目をヘッダー行としてスキップ
                header = next(reader) 
                
                # 3行目以降がカードデータ
                for row in reader:
                    if not row or len(row) < 4: continue
                    c_id = row[0] if len(row) > 0 else "X-00"
                    c_cost = row[2] if len(row) > 2 else "0"
                    c_name = row[3] if len(row) > 3 else "不明"
                    c_type = row[4] if len(row) > 4 else "スキル"
                    c_atk = row[5] if len(row) > 5 else ""
                    c_hp = row[6] if len(row) > 6 else ""
                    c_effect = row[7] if len(row) > 7 else "（効果なし）"

                    card_data = {
                        "id": c_id.strip(), "name": c_name.strip(), "type": c_type.strip(),
                        "cost": c_cost.strip(), "atk": c_atk.strip(), "hp": c_hp.strip(), "effect": c_effect.strip()
                    }

                    if char_type == "pc" and len(fixed_hand) < 3:
                        fixed_hand.append(card_data)
                    else:
                        pool.append(card_data)
        except Exception:
            pass
            
    if not pool and not fixed_hand:
        pfx = "R" if char_type == "pc" else "B"
        pool = [
            {"id": f"{pfx}-01", "name": "基本攻撃", "type": "スキル", "cost": "1", "atk": "1", "hp": "1", "effect": f"{filename}が空か見つかりません。"},
            {"id": f"{pfx}-02", "name": "基本防御", "type": "スキル", "cost": "2", "atk": "0", "hp": "3", "effect": "【守護】"}
        ]
    
    random.shuffle(pool)
    return deck_title, fixed_hand, pool

# --- セッションデータの初期化 ---
if "chars" not in st.session_state:
    st.session_state.chars = {}
    for code, info in CHAR_CONFIG.items():
        st.session_state.chars[code] = {
            "prefix": info["prefix"],
            "name": "読込中...", 
            "type": info["type"],
            "csv": info["csv"],
            "deck": [],
            "hand": [],
            "battlefield": [],
            "life": 6 if info["type"] == "enemy" else 15, 
            "log": "ゲーム開始準備完了。",
            "initialized": False
        }

if "round_count" not in st.session_state:
    st.session_state.round_count = 1

# アプリ起動時 or 初回選択時に初期化
for code, char in st.session_state.chars.items():
    if not char["initialized"]:
        title, fixed_cards, cards = load_deck_from_csv(char["csv"], char["type"])
        char["name"] = title
        char["deck"] = cards
        
        if char["type"] == "pc":
            char["hand"] = fixed_cards
            for _ in range(5):
                if char["deck"]:
                    char["hand"].append(char["deck"].pop(0))
        else:
            char["hand"] = []
            for _ in range(5):
                if char["deck"]:
                    char["hand"].append(char["deck"].pop(0))
                    
        char["initialized"] = True

st.title("🎯 TRPG 動的キャラカード決戦ビューア")

# --- ラウンド＆選択カウンター横並び配置 ---
col_sel1, col_sel2, col_sel3 = st.columns([2, 3, 3])

with col_sel1:
    st.write("**⏳ 進行管理**")
    c_rnd1, c_rnd2, c_rnd3 = st.columns([1, 2, 1])
    with c_rnd1:
        if st.button("➖", key="round_minus"):
            st.session_state.round_count = max(1, st.session_state.round_count - 1)
            st.rerun()
    with c_rnd2:
        st.session_state.round_count = st.number_input(f"ラウンド", min_value=1, value=st.session_state.round_count, label_visibility="collapsed")
    with c_rnd3:
        if st.button("➕", key="round_plus"):
            st.session_state.round_count += 1
            st.rerun()

with col_sel2:
    pc_code = st.selectbox(
        "🛡️ 操作するPCを選択:", 
        [k for k, v in CHAR_CONFIG.items() if v["type"] == "pc"],
        format_func=lambda x: f"{st.session_state.chars[x]['prefix']} {st.session_state.chars[x]['name']}"
    )
with col_sel3:
    enemy_code = st.selectbox(
        "🤖 対峙するエネミーを選択:", 
        [k for k, v in CHAR_CONFIG.items() if v["type"] == "enemy"],
        format_func=lambda x: f"{st.session_state.chars[x]['prefix']} {st.session_state.chars[x]['name']}"
    )

infinite_hand = st.checkbox("🔄 敵の手札消費を無効化（減らない）", value=False)

p_char = st.session_state.chars[pc_code]
e_char = st.session_state.chars[enemy_code]

st.write("---")

# 盤面描画関数
def render_character_zone(char, label, is_enemy, inf_hand, code_key):
    # ライフカウンターインライン配置
    header_col, life_col = st.columns([3, 1])
    
    with header_col:
        st.subheader(f"{label} {char['prefix']} {char['name']} (山札残り: {len(char['deck'])}枚) 📄ファイル:{char['csv']}")
        
    with life_col:
        st.write(f"**❤️ ライフ: {char['life']}**")
        l_btn1, l_btn2 = st.columns([1, 1])
        with l_btn1:
            if st.button("➖", key=f"life_m_{code_key}"):
                char["life"] -= 1
                st.rerun()
        with l_btn2:
            if st.button("➕", key=f"life_p_{code_key}"):
                char["life"] += 1
                st.rerun()
    
    st.write("**【 場（ユニット・エンチャント） 】**")
    if char["battlefield"]:
        cols = st.columns(max(len(char["battlefield"]), 1))
        for i, card in enumerate(char["battlefield"]):
            with cols[i]:
                type_pfx = card['type'][0] if card['type'] else "ス"
                atk_val = card['atk'] if card['atk'] else "0"
                hp_val = card['hp'] if card['hp'] else "0"
                
                # 「使用済み」状態（is_used）の初期チェックとタイトルの切り替え
                is_used = card.get("is_used", False)
                if is_used:
                    title_display = f"🚫【使用済み】 {card['name']}"
                    toggle_label = "⭕ 未使用に戻す"
                else:
                    title_display = f"【{card['name']}】"
                    toggle_label = "❌ 使用済みにする"
                
                bf_markdown = f"**[{card['id']}] {title_display}** \n({type_pfx}) :{card['cost']}:AT:{atk_val} / DF:{hp_val}  \n*{card['effect']}*"
                st.info(bf_markdown)
                
                # 「使用済み/未使用」の個別切り替えボタン
                if st.button(toggle_label, key=f"toggle_bf_{char['csv']}_{card['id']}_{i}"):
                    card["is_used"] = not is_used
                    st.rerun()
                
                if st.button(f"🗑️ 場の{i+1}を消去", key=f"k_bf_{char['csv']}_{card['id']}_{i}"):
                    removed = char["battlefield"].pop(i)
                    char["log"] = f"💥 場から「{removed['name']}」を消去しました。"
                    st.rerun()
    else:
        st.caption("（場にカードはありません）")
        
    st.write("")
    
    st.write("**【 手札 】**")
    col_d, col_r = st.columns([1, 5])
    with col_d:
        if st.button(f"➕ 1枚引く", key=f"d_{char['csv']}"):
            if char["deck"]:
                drawn = char["deck"].pop(0)
                char["hand"].append(drawn)
                char["log"] = f"🃏 山札の上から「{drawn['name']}」を引きました。"
            else:
                char["log"] = "⚠️ 山札がありません（ドロー不可）。"
            st.rerun()
    with col_r:
        if st.button(f"🔄 デッキ再読込・初期化", key=f"reset_{char['csv']}"):
            char["initialized"] = False
            st.rerun()
            
    if char["hand"]:
        cols_h = st.columns(max(len(char["hand"]), 1))
        for i, card in enumerate(char["hand"]):
            with cols_h[i]:
                type_pfx = card['type'][0] if card['type'] else "ス"
                
                status_line = f"({type_pfx}) :{card['cost']}:"
                if card['atk'] or card['hp']:
                    atk_val = card['atk'] if card['atk'] else "0"
                    hp_val = card['hp'] if card['hp'] else "0"
                    status_line += f"AT:{atk_val} / DF:{hp_val}"
                
                card_markdown = f"**[{card['id']}] 【{card['name']}】** \n{status_line}  \n*{card['effect']}*"
                st.success(card_markdown)
                
                # 操作ボタン群
                if "スキル" in card["type"] or "エンチャント" in card["type"]:
                    if st.button(f"⚔️ 場に出す", key=f"p_{char['csv']}_{card['id']}_{i}"):
                        if is_enemy and inf_hand:
                            played = card.copy()
                        else:
                            played = char["hand"].pop(i)
                        
                        # 場に出る際は初期値「未使用（False）」を持たせる
                        played["is_used"] = False
                        
                        char["battlefield"].append(played)
                        char["log"] = f"⚔️ 「{played['name']}」を場に出しました。"
                        st.rerun()
                else:
                    if st.button(f"⚡ アーツ発動", key=f"p_art_{char['csv']}_{card['id']}_{i}"):
                        if is_enemy and inf_hand:
                            played = card
                        else:
                            played = char["hand"].pop(i)
                        char["log"] = f"⚡ アーツ「{played['name']}」を発動しました。"
                        st.rerun()
                
                # 山札操作ボタンを横並びで配置
                col_to_top, col_to_bot = st.columns([1, 1])
                with col_to_top:
                    if st.button(f"🔼 上に戻す", key=f"top_{char['csv']}_{card['id']}_{i}"):
                        target_card = char["hand"].pop(i)
                        char["deck"].insert(0, target_card) # 山札の先頭(一番上)へ追加
                        char["log"] = f"🔼 「{target_card['name']}」を山札の一番上に戻しました。"
                        st.rerun()
                with col_to_bot:
                    if st.button(f"🔽 下に戻す", key=f"bot_{char['csv']}_{card['id']}_{i}"):
                        target_card = char["hand"].pop(i)
                        char["deck"].append(target_card) # 山札の末尾(一番下)へ追加
                        char["log"] = f"🔽 「{target_card['name']}」を山札の一番下に戻しました。"
                        st.rerun()
                        
                if st.button(f"❌ 消去", key=f"k_h_{char['csv']}_{card['id']}_{i}"):
                    removed = char["hand"].pop(i)
                    char["log"] = f"🗑️ 手札から「{removed['name']}」を消去しました。"
                    st.rerun()
    else:
        st.caption("（手札はありません）")

render_character_zone(e_char, "🤖 エネミー", is_enemy=True, inf_hand=infinite_hand, code_key=enemy_code)
st.write("---")
render_character_zone(p_char, "🛡️ プレイヤー", is_enemy=False, inf_hand=False, code_key=pc_code)

st.write("---")
st.info(f"💬 **ログ:** {e_char['log']} | {p_char['log']}")