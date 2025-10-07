import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import timedelta
from dateutil.relativedelta import relativedelta

# --------------------------------------------------------------------------
# ページ設定
# --------------------------------------------------------------------------
st.set_page_config(page_title="分野別 詳細分析", layout="wide")

# --------------------------------------------------------------------------
# データ読み込み
# --------------------------------------------------------------------------
@st.cache_data
def load_ranked_data():
    csv_path = Path(__file__).parent.parent / 'estat_ranking_merged.csv'
    df = pd.read_csv(csv_path)
    df['access_count'] = pd.to_numeric(df['access_count'], errors='coerce').fillna(0).astype(int)
    df['date'] = pd.to_datetime(df['date'])
    df['year_month'] = df['date'].dt.to_period('M').astype(str)
    return df

df = load_ranked_data()

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

# 期間でフィルターされたデータフレームを作成
filtered_df = df[
    (df['date'].dt.date >= start_date) &
    (df['date'].dt.date <= end_date)
]

# --------------------------------------------------------------------------
# メインコンテンツ
# --------------------------------------------------------------------------
st.title("分野別 詳細分析")
st.markdown("特定の分野に焦点を当て、その中でのシリーズ間の比較や詳細な動向を多角的に分析します。")

# --- 分野の選択 ---
custom_order = [
    "国土・気象", "人口・世帯", "労働・賃金", "農林水産業", "鉱工業",
    "商業・サービス業", "企業・家計・経済", "住宅・土地・建設",
    "エネルギー・水", "運輸・観光", "情報通信・科学技術",
    "教育・文化・スポーツ・生活", "行財政", "司法・安全・環境",
    "社会保障・衛生", "国際", "その他"
]
majors_in_data = filtered_df['field_major'].dropna().unique()
sorted_majors = [major for major in custom_order if major in majors_in_data]
selected_major = st.selectbox('分析したい分野を選択してください', sorted_majors)

st.markdown("---")

# --- 分野が選択されたら、すべての分析を縦に表示 ---
if selected_major:
    df_major_filtered = filtered_df[filtered_df['field_major'] == selected_major]
    
    # --- 1. 分野サマリー ---
    st.header(f"「{selected_major}」分野 サマリー")
    
    # KPI
    major_total_access = df_major_filtered['access_count'].sum()
    major_series_count = df_major_filtered['series_name'].nunique()
    kpi1, kpi2 = st.columns(2)
    kpi1.metric("分野の総アクセス数", f"{major_total_access:,.0f}")
    kpi2.metric("分野内のランクインシリーズ数", f"{major_series_count}")

    # 👈 --- ここからが修正箇所 ---
    
    col_timeline, col_sunburst = st.columns(2)
    
    with col_timeline:
        # 分野全体の時系列
        st.markdown("##### 分野全体のアクセス数推移")
        major_monthly = df_major_filtered.set_index('date').resample('ME')['access_count'].sum()
        fig_major_timeline = px.line(major_monthly, x=major_monthly.index, y=major_monthly.values, labels={'x': '年月', 'y': '月間アクセス数'}, markers=True)
        st.plotly_chart(fig_major_timeline, use_container_width=True)
    
    with col_sunburst:
        # シリーズ → ファイル名のサンバーストチャート
        st.markdown("##### シリーズ → ファイル名のアクセス内訳")
        fig_sunburst = px.sunburst(
            df_major_filtered.dropna(subset=['series_name', 'file_name']),
            path=['series_name', 'file_name'],
            values='access_count',
            title='クリックでドリルダウン'
        )
        fig_sunburst.update_layout(margin=dict(t=50, l=10, r=10, b=10))
        st.plotly_chart(fig_sunburst, use_container_width=True)

    # 👈 --- ここまでが修正箇所 ---

    st.markdown("##### 分野内での組織別アクセス数ランキング")
    org_dist = df_major_filtered.groupby('organization')['access_count'].sum().sort_values(ascending=False).reset_index()
    st.dataframe(org_dist, use_container_width=True, hide_index=True)
    
    st.markdown("---")

    # --- 2. シリーズ時系列比較 ---
    st.header(f"「{selected_major}」分野 シリーズ時系列比較")
    st.markdown("選択した分野に含まれる各シリーズの月間アクセス数の推移を比較できます。凡例をダブルクリックすると特定のシリーズをハイライトできます。")
    
    series_monthly_comparison = df_major_filtered.groupby(['series_name', 'year_month'])['access_count'].sum().reset_index()
    
    fig_series_comparison = px.line(
        series_monthly_comparison, 
        x='year_month', 
        y='access_count', 
        color='series_name',
        labels={'year_month': '年月', 'access_count': '月間アクセス数', 'series_name': 'シリーズ名'}, 
        height=500,
        markers=True
    )
    st.plotly_chart(fig_series_comparison, use_container_width=True)

    st.markdown("---")
    
    # --- 3. ファイル種別分析 ---
    st.header(f"「{selected_major}」分野 ファイル種別分析")
    st.markdown("選択した分野で、どのファイル形式（PDF, Excel, CSVなど）が多く利用されているかを確認できます。")
    
    col_pie, col_bar = st.columns(2)
    with col_pie:
        st.markdown("##### 全体の割合")
        file_type_dist = df_major_filtered['file_type'].value_counts()
        fig_pie_type = px.pie(file_type_dist, names=file_type_dist.index, values=file_type_dist.values, title='ファイル種別ごとのアクセス割合', hole=0.4)
        st.plotly_chart(fig_pie_type, use_container_width=True)

    with col_bar:
        st.markdown("##### シリーズごとの内訳")
        file_type_by_series = df_major_filtered.groupby(['series_name', 'file_type'])['access_count'].sum().reset_index()
        
        series_order = df_major_filtered.groupby('series_name')['access_count'].sum().sort_values(ascending=True).index
        
        fig_bar_type = px.bar(
            file_type_by_series, 
            y='series_name',
            x='access_count',
            color='file_type',
            orientation='h',
            labels={'series_name': 'シリーズ名', 'access_count': 'アクセス数', 'file_type': 'ファイル種別'},
            title='シリーズごとのファイル種別アクセス数',
            category_orders={'series_name': series_order}
        )
        
        st.plotly_chart(fig_bar_type, use_container_width=True)

    st.markdown("---")
    
    # --- 4. シリーズ詳細ドリルダウン ---
    st.header(f"「{selected_major}」分野 シリーズ詳細ドリルダウン")
    series_in_major = sorted(df_major_filtered['series_name'].dropna().unique())
    series_options = ["▼ 分析したいシリーズを選択..."] + series_in_major
    selected_series = st.selectbox('詳細を見たいシリーズを選択してください', series_options)

    if selected_series != "▼ 分析したいシリーズを選択...":
        df_series_filtered = df_major_filtered[df_major_filtered['series_name'] == selected_series]
        
        series_total_access = df_series_filtered['access_count'].sum()
        series_avg_rank = df_series_filtered['rank'].mean()
        series_days_in_ranking = df_series_filtered['date'].nunique()
        total_days_in_period = (end_date - start_date).days + 1
        
        skpi1, skpi2, skpi3 = st.columns(3)
        skpi1.metric("シリーズ総アクセス数", f"{series_total_access:,.0f}")
        skpi2.metric("期間内平均順位", f"{series_avg_rank:.1f} 位")
        skpi3.metric("ランキング登場日数", f"{series_days_in_ranking} 日 / 全 {total_days_in_period} 日")

        st.markdown(f"##### 「{selected_series}」内のファイル別アクセス数ランキング")
        st.info("""
        **注:** e-Statのデータ特性上、公開年などが異なるが同じ名称のファイルが複数存在する場合があります。
        この表は個別のファイル（URL）ごとにアクセス数を集計しているため、同じファイル名が複数行表示されることがあります。
        """)
        file_popularity = df_series_filtered.groupby(['file_name', 'main_link'])['access_count'].sum().sort_values(ascending=False).reset_index()
        
        html_table = "<table style='width:100%; border-collapse: collapse;'>"
        html_table += "<thead><tr style='border-bottom: 1px solid #ddd;'><th style='padding: 8px; text-align: left;'>ファイル名</th><th style='padding: 8px; text-align: right;'>アクセス数</th></tr></thead><tbody>"
        for index, row in file_popularity.iterrows():
            linked_file_name = f"<a href='{row['main_link']}' target='_blank'>{row['file_name']}</a>"
            html_table += f"<tr style='border-bottom: 1px solid #eee;'><td style='padding: 8px; text-align: left;'>{linked_file_name}</td><td style='padding: 8px; text-align: right;'>{row['access_count']:,}</td></tr>"
        html_table += "</tbody></table>"
        
        st.markdown(html_table, unsafe_allow_html=True)