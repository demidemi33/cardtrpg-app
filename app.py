import streamlit as st
import pandas as pd
import os

# ページの設定
st.set_page_config(page_title="Card TRPG Simulator", layout="wide")

# データの読み込み関数
@st.cache_data
def load_data():
    # パソコン内にある「赤リスト」「青のリスト」という名前のファイルを読み込みます
    # ファイルがない場合はエラーを防ぐためのサンプルデータを動かします
    if os.path.exists("赤リスト"):
        red_df = pd.read_csv("赤リスト")
    elif os.path.exists("red_list.csv"):
        red_df = pd.read_csv("red_list.csv")
    else:
        red_df = pd.DataFrame({
            "色": ["赤", "赤"], "コスト": [1, 2], 
            "カード名": ["小攻撃", "盾防御"], "種類": ["スキル", "スキル"],
            "攻撃": [2, 0], "HP": [1, 3], "効果": ["なし", "守護"]
        })
        
    if os.path.exists("青のリスト"):
        blue_df = pd.read_csv("青のリスト")
    elif os.path.exists("blue_list.csv"):
        blue_df = pd.read_csv("blue_list.csv")
    else:
        blue_df = pd.DataFrame({
            "色": ["青", "青"], "コスト": [1, 2], 
            "カード名": ["不意の一撃", "瞬縛斬り"], "種類": ["スキル", "スキル"],
            "攻撃": [1, 2], "HP": [1, 1], "効果": ["奇襲", "場に出た時タップ"]
        })
        
    return pd.concat([red_df, blue_df], ignore_index=True)

# セッション状態の初期化（プレイヤーのライフや盤面の保存）
if "player_life" not in st.session_state:
    st.session_state.player_life = 20
if "boss_life" not in st.session_state:
    st.session_state.boss_life = 50
if "battlefield" not in st.session_state:
    st.session_state.battlefield = []
if "round" not in st.session_state:
    st.session_state.round = 1

# データのロード
df = load_data()

# タイトル
st.title("⚔️ カードTRPG セッションシミュレーター")

# ----------------- サイドバー：ステータス管理 -----------------
with st.sidebar:
    st.header("📊 ステータス管理")
    st.subheader(f"ラウンド: {st.session_state.round}")
    if st.button("次のラウンドへ"):
        st.session_state.round += 1
        
    st.divider()
    
    # ライフカウンター
    st.session_state.player_life = st.number_input("👤 プレイヤーライフ", value=st.session_state.player_life)
    st.session_state.boss_life = st.number_input("👹 ボスライフ", value=st.session_state.boss_life)
    
    st.divider()
    st.caption("GitHub ＆ Streamlit Cloud 公開用バージョン")

# ----------------- メイン画面：2カラム構成 -----------------
col1, col2 = st.columns([1, 1])

# 左側：カードリストから選んで場に出すエリア
with col1:
    st.header("🗂️ カード図鑑・配置")
    
    # 色でのフィルタリング
    color_filter = st.selectbox("色を選択", ["すべて", "赤", "青"])
    filtered_df = df if color_filter == "すべて" else df[df["色"] == color_filter]
    
    # カードの選択
    selected_card_name = st.selectbox("配置・使用するカードを選択", filtered_df["カード名"].tolist())
    card_info = df[df["カード名"] == selected_card_name].iloc[0]
    
    # カード詳細表示
    st.markdown(f"""
    ### 🃏 **{card_info['カード名']}** ({card_info['種類']})
    - **色/コスト:** {card_info['色']} / {card_info['コスト']}
    - **ステータス:** ⚔️ {card_info['攻撃']} / ❤️ {card_info['HP']}
    - **効果:** *{card_info['効果'] if pd.notna(card_info['効果']) else 'なし'}*
    """)
    
    # 戦場への配置ボタン
    if card_info['種類'] == "スキル":
        if st.button("🛑 このスキルを戦場に配置"):
            if len(st.session_state.battlefield) < 10:  # 上限10枠
                # 新しく配置されたスキルはルール通り「構え」状態（未使用）で出ます
                new_skill = {
                    "id": len(st.session_state.battlefield) + 1,
                    "name": card_info['カード名'],
                    "atk": card_info['攻撃'],
                    "hp": card_info['HP'],
                    "effect": card_info['効果'] if pd.notna(card_info['効果']) else "なし",
                    "is_used": False  # 初期状態は「未使用」
                }
                st.session_state.battlefield.append(new_skill)
                st.success(f"「{card_info['カード名']}」を【未使用（構え）】で配置しました！")
                st.rerun()
            else:
                st.error("スキル枠（10枠）が上限に達しています！")
    else:
        if st.button("✨ このアーツ/エンチャントを使用（即時使い捨て）"):
            st.info(f"「{card_info['カード名']}」の効果を発動しました（捨て札へ）。")

# 右側：現在の戦場（使用済み・未使用ボタン付き！）
with col2:
    st.header("🛡️ 現在の戦場（配置済みスキル）")
    
    # 一括操作用のボタン（自分のターンが来たら全アンタップする仕組み）
    if st.session_state.battlefield:
        if st.button("🔄 自分のターン開始（すべてのカードを『未使用』に戻す）"):
            for skill in st.session_state.battlefield:
                skill["is_used"] = False
            st.success("すべてのスキルが未使用（行動可能）になりました！")
            st.rerun()
        st.divider()

    if not st.session_state.battlefield:
        st.write("戦場にはまだスキルが配置されていません。")
    else:
        # 配置されているスキルをループで1枚ずつカード型にして表示
        for idx, skill in enumerate(st.session_state.battlefield):
            is_used = skill["is_used"]
            
            # 使用済みか未使用かで見た目の文字やマークを変える
            if is_used:
                card_title = f"🚫 【使用済み】 {skill['name']}"
                button_label = "⭕ 未使用に戻す"
            else:
                card_title = f"⚔️ 【未使用】 {skill['name']}"
                button_label = "❌ 使用済みにする"
            
            # 個別のカードを綺麗な枠で囲む
            with st.container(border=True):
                c_left, c_right = st.columns([3, 2])
                
                with c_left:
                    st.markdown(f"**{card_title}** (⚔️{skill['atk']} / ❤️{skill['hp']})")
                    st.caption(f"効果: {skill['effect']}")
                
                with c_right:
                    # 「使用済み / 未使用」をパチッと切り替える個別ボタン
                    if st.button(button_label, key=f"status_btn_{idx}"):
                        st.session_state.battlefield[idx]["is_used"] = not is_used
                        st.rerun()
                    
                    # 破壊・破棄されたときに場から消すボタン
                    if st.button("💥 破棄して墓地へ", key=f"del_btn_{idx}"):
                        st.session_state.battlefield.pop(idx)
                        st.rerun()