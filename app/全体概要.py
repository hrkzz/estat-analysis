import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import timedelta
from dateutil.relativedelta import relativedelta

# --------------------------------------------------------------------------
# ページ設定
# --------------------------------------------------------------------------
st.set_page_config(page_title="e-Stat分析ダッシュボード", layout="wide")

# --------------------------------------------------------------------------
# データ読み込みと準備
# --------------------------------------------------------------------------
@st.cache_data
def load_all_data():
    base_path = Path(__file__).parent
    df_ranked = pd.read_csv(base_path / 'estat_ranking_merged.csv')
    df_ranked['access_count'] = pd.to_numeric(df_ranked['access_count'], errors='coerce').fillna(0).astype(int)
    df_ranked['date'] = pd.to_datetime(df_ranked['date'])
    df_details = pd.read_csv(base_path / 'estat_all_series_details_normalized.csv')
    
    # ハイフン正規化
    if 'series_name' in df_ranked.columns:
        df_ranked['series_name'] = df_ranked['series_name'].str.replace('‐', '-', regex=False)
    if 'series_name' in df_details.columns:
        df_details['series_name'] = df_details['series_name'].str.replace('‐', '-', regex=False)
        
    return df_ranked, df_details

df, details_df = load_all_data()

# --------------------------------------------------------------------------
# サイドバー (フィルター)
# --------------------------------------------------------------------------
st.sidebar.header('期間の選択')

min_date = df['date'].min().date()
max_date = df['date'].max().date()

date_range_option = st.sidebar.radio(
    "期間の選択方法:",
    ('過去1週間', '過去1ヶ月', '過去1年', '過去2年', '過去3年', '過去5年', '全期間', '期間を直接指定'),
    index=6,
)

if date_range_option == '過去1週間':
    start_date = max_date - timedelta(days=7)
    end_date = max_date
elif date_range_option == '過去1ヶ月':
    start_date = max_date - relativedelta(months=1)
    end_date = max_date
elif date_range_option == '過去1年':
    start_date = max_date - relativedelta(years=1)
    end_date = max_date
elif date_range_option == '過去2年':
    start_date = max_date - relativedelta(years=2)
    end_date = max_date
elif date_range_option == '過去3年':
    start_date = max_date - relativedelta(years=3)
    end_date = max_date
elif date_range_option == '過去5年':
    start_date = max_date - relativedelta(years=5)
    end_date = max_date
elif date_range_option == '全期間':
    start_date = min_date
    end_date = max_date
else: # '期間を直接指定'
    selected_range = st.sidebar.date_input(
        '開始日と終了日を選択してください',
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    if len(selected_range) == 2:
        start_date, end_date = selected_range
    else:
        st.sidebar.error("有効な期間を選択してください。")
        start_date, end_date = min_date, max_date

# フィルターされたデータフレーム
filtered_df = df[
    (df['date'].dt.date >= start_date) &
    (df['date'].dt.date <= end_date)
]

# --------------------------------------------------------------------------
# メインコンテンツ
# --------------------------------------------------------------------------
st.title('e-Stat ランキング分析')
st.markdown("e-Statの日次ランキングデータに基づき、統計全体の人気動向を可視化します。このダッシュボードはランキング上位の統計のみを集計したものであり、e-Stat全体のアクセス数の推移を示すものではありません。")

# --- KPI ---
st.subheader("主要指標（KPI）")
total_series_count = details_df['series_name'].nunique()
ranked_series_count = filtered_df['series_name'].nunique()
unranked_series_count = total_series_count - ranked_series_count

col1, col2, col3 = st.columns(3)
col1.metric("期間内総アクセス数", f"{filtered_df['access_count'].sum():,.0f}")
ranked_series_text = f"{ranked_series_count} ({ranked_series_count / total_series_count:.1%})"
col2.metric("ランクインシリーズ数", ranked_series_text)
unranked_series_text = f"{unranked_series_count} ({unranked_series_count / total_series_count:.1%})"
col3.metric("圏外シリーズ数", unranked_series_text)

st.markdown("---")

# --- 時系列推移 ---
st.subheader("ランキング上位統計のアクセス推移")
monthly_access = filtered_df.set_index('date').resample('ME')['access_count'].sum()
fig_timeline = px.line(monthly_access, x=monthly_access.index, y=monthly_access.values, labels={'x': '年月', 'y': '月間総アクセス数'}, markers=True)
st.plotly_chart(fig_timeline, use_container_width=True)

st.markdown("---")

# --- 分野別・組織別の総アクセス数 ---
st.subheader("分野別・組織別の総アクセス数")
col_bar1, col_bar2 = st.columns(2)
with col_bar1:
    st.markdown("##### 分野別")
    major_popularity = filtered_df.groupby('field_major')['access_count'].sum().sort_values(ascending=True)
    fig_major = px.bar(major_popularity, x=major_popularity.values, y=major_popularity.index, orientation='h', labels={'y': '分野', 'x': '総アクセス数'})
    st.plotly_chart(fig_major, use_container_width=True)

with col_bar2:
    st.markdown("##### 組織別")
    org_popularity = filtered_df.groupby('organization')['access_count'].sum().sort_values(ascending=True)
    fig_org = px.bar(org_popularity, x=org_popularity.values, y=org_popularity.index, orientation='h', labels={'y': '組織', 'x': '総アクセス数'})
    st.plotly_chart(fig_org, use_container_width=True)

st.markdown("##### 階層別アクセス数")
st.markdown("グラフの中心（分野や組織）をクリックすると、その内訳（シリーズ）にドリルダウンできます。")

col_sun1, col_sun2 = st.columns(2)
with col_sun1:
    fig_sun_field = px.sunburst(
        filtered_df.dropna(subset=['field_major', 'series_name']),
        path=['field_major', 'series_name'],
        values='access_count',
        title='分野 → シリーズ'
    )
    fig_sun_field.update_layout(margin=dict(t=50, l=10, r=10, b=10))
    st.plotly_chart(fig_sun_field, use_container_width=True)
    
with col_sun2:
    fig_sun_org = px.sunburst(
        filtered_df.dropna(subset=['organization', 'series_name']),
        path=['organization', 'series_name'],
        values='access_count',
        title='組織 → シリーズ'
    )
    fig_sun_org.update_layout(margin=dict(t=50, l=10, r=10, b=10))
    st.plotly_chart(fig_sun_org, use_container_width=True)

st.markdown("---")

# --- 分野別の時系列推移 ---
st.subheader("分野別の時系列推移")
major_monthly = filtered_df.groupby(['field_major', pd.Grouper(key='date', freq='ME')])['access_count'].sum().reset_index()
fig_major_stack = px.bar(
    major_monthly, 
    x='date', 
    y='access_count', 
    color='field_major', 
    labels={'date': '年月', 'access_count': '月間アクセス数'}, 
    height=500,
    color_discrete_sequence=px.colors.qualitative.Alphabet
)
st.plotly_chart(fig_major_stack, use_container_width=True)


st.markdown("---")

# --- 組織別の時系列推移 ---
st.subheader("組織別の時系列推移")
org_monthly = filtered_df.groupby(['organization', pd.Grouper(key='date', freq='ME')])['access_count'].sum().reset_index()
fig_org_stack = px.bar(
    org_monthly, 
    x='date', 
    y='access_count', 
    color='organization', 
    labels={'date': '年月', 'access_count': '月間アクセス数'}, 
    height=500,
    color_discrete_sequence=px.colors.qualitative.Alphabet
)
st.plotly_chart(fig_org_stack, use_container_width=True)

st.markdown("---")

# --- ランキング圏外の統計一覧 ---
st.subheader("ランキング圏外の統計分析")
ranked_series_set = set(df['series_name'].unique())
unranked_df = details_df[~details_df['series_name'].isin(ranked_series_set)].reset_index(drop=True)

st.markdown("分析したい分野をクリックして展開すると、その分野に含まれる圏外シリーズの一覧が表示されます。")

# custom_orderリストを定義
custom_order = [
    "国土・気象", "人口・世帯", "労働・賃金", "農林水産業", "鉱工業",
    "商業・サービス業", "企業・家計・経済", "住宅・土地・建設",
    "エネルギー・水", "運輸・観光", "情報通信・科学技術",
    "教育・文化・スポーツ・生活", "行財政", "司法・安全・環境",
    "社会保障・衛生", "国際", "その他"
]

# データに存在する分野のみをカスタム順でソート
fields_in_unranked_data = unranked_df['field_major'].dropna().unique()
ordered_fields = [field for field in custom_order if field in fields_in_unranked_data]

# ソートされた分野リストをループ処理してexpanderを作成
for field in ordered_fields:
    group_df = unranked_df[unranked_df['field_major'] == field]
    
    if not group_df.empty:
        with st.expander(f"{field} ({len(group_df)}件)"):
            st.dataframe(
                group_df[['series_name', 'organization', 'overview']],
                hide_index=True,
                use_container_width=True
            )