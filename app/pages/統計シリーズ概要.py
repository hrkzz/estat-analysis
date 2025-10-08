import streamlit as st
import pandas as pd
from pathlib import Path

# --------------------------------------------------------------------------
# ページ設定
# --------------------------------------------------------------------------
st.set_page_config(page_title="統計シリーズ 概要", layout="wide")

# --------------------------------------------------------------------------
# データ読み込み
# --------------------------------------------------------------------------
@st.cache_data
def load_data():
    """
    統計シリーズの詳細情報を読み込む関数
    """
    base_path = Path(__file__).parent.parent
    details_df = pd.read_csv(base_path / 'estat_all_series_details_normalized.csv')
    details_df.dropna(subset=['field_major', 'organization', 'series_name'], inplace=True)
    return details_df

df_details = load_data()

# --------------------------------------------------------------------------
# サイドバー
# --------------------------------------------------------------------------
st.sidebar.markdown("""
    <style>
        [data-testid="stSidebarNav"]::before {
            content: "e-Stat 分析ダッシュボード";
            margin-left: 10px;
            margin-top: 20px;
            font-size: 1.1rem;
            font-weight: 700;
            color: #333;
            display: block;
        }
    </style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# メインコンテンツ
# --------------------------------------------------------------------------
st.title("統計シリーズ 概要")
st.markdown("e-Statで提供されている全統計シリーズの構造を、「分野」と「提供組織」の2つの観点から一覧表示します。")
st.markdown("---")

# ★★★ ここからが分野別のアコーディオン形式 ★★★
st.subheader("分野別のシリーズ一覧")
st.markdown("分野名をクリックすると、関連する統計シリーズの一覧が展開されます。")

# 分野ごとにデータをグループ化
grouped_by_field = df_details.groupby('field_major')

# 表示順を定義
custom_order = [
    "国土・気象", "人口・世帯", "労働・賃金", "農林水産業", "鉱工業",
    "商業・サービス業", "企業・家計・経済", "住宅・土地・建設",
    "エネルギー・水", "運輸・観光", "情報通信・科学技術",
    "教育・文化・スポーツ・生活", "行財政", "司法・安全・環境",
    "社会保障・衛生", "国際", "その他"
]
# データに存在する分野のみをカスタム順でソート
unique_fields = df_details['field_major'].unique()
sorted_fields = [field for field in custom_order if field in unique_fields]

for field_name in sorted_fields:
    field_df = grouped_by_field.get_group(field_name)
    with st.expander(f"{field_name} ({len(field_df)}件のシリーズ)"):
        st.dataframe(
            field_df[['series_name', 'organization', 'overview']],
            column_config={
                "series_name": "シリーズ名",
                "organization": "提供組織",
                "overview": "概要",
            },
            hide_index=True,
            use_container_width=True
        )

st.markdown("---")

# ★★★ ここからが組織別のアコーディオン形式 ★★★
st.subheader("提供組織別のシリーズ一覧")
st.markdown("組織名をクリックすると、提供している統計シリーズの一覧が展開されます。")

# 組織ごとにデータをグループ化
grouped_by_org = df_details.groupby('organization')

# 組織名をソートして順番に表示
sorted_orgs = sorted(df_details['organization'].unique())

for org_name in sorted_orgs:
    org_df = grouped_by_org.get_group(org_name)
    with st.expander(f"{org_name} ({len(org_df)}件のシリーズ)"):
        st.dataframe(
            org_df[['series_name', 'overview']],
            column_config={
                "series_name": "シリーズ名",
                "overview": "概要",
            },
            hide_index=True,
            use_container_width=True
        )

st.markdown("---")

# --- 統計シリーズ一覧と検索 ---
st.subheader("統計シリーズ一覧と検索")
st.markdown("分野や組織を選択して、表示されるシリーズを絞り込むことができます。")

filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    # 上で定義したソート済みリストを再利用
    selected_fields = st.multiselect("分野で絞り込み:", options=sorted_fields)

with filter_col2:
    # 上で定義したソート済みリストを再利用
    selected_orgs_filter = st.multiselect("提供組織で絞り込み:", options=sorted_orgs)

filtered_table_df = df_details.copy()
if selected_fields:
    filtered_table_df = filtered_table_df[filtered_table_df['field_major'].isin(selected_fields)]
if selected_orgs_filter:
    filtered_table_df = filtered_table_df[filtered_table_df['organization'].isin(selected_orgs_filter)]

st.dataframe(
    filtered_table_df[['series_name', 'field_major', 'organization', 'overview']],
    column_config={
        "series_name": "シリーズ名",
        "field_major": "分野",
        "organization": "提供組織",
        "overview": st.column_config.TextColumn("概要", width="large"),
    },
    hide_index=True,
    use_container_width=True
)