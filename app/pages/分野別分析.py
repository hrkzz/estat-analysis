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
def load_data():
    base_path = Path(__file__).parent.parent
    df_ranked = pd.read_csv(base_path / 'estat_ranking_merged.csv')
    df_details = pd.read_csv(base_path / 'estat_all_series_details_normalized.csv')

    df_ranked['access_count'] = pd.to_numeric(df_ranked['access_count'], errors='coerce').fillna(0).astype(int)
    df_ranked['date'] = pd.to_datetime(df_ranked['date'])
    df_ranked['year_month'] = df_ranked['date'].dt.to_period('M').astype(str)
    
    return df_ranked, df_details

df, details_df = load_data()

# --------------------------------------------------------------------------
# サイドバー (フィルター)
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

min_date = df['date'].min().date()
max_date = df['date'].max().date()

date_range_option = st.sidebar.radio(
    "期間の選択:",
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

st.sidebar.markdown(
    f"""
    <style>
    .sidebar-footer {{
        font-size: 15px !important;
        color: #555;
        font-family: "Source Sans", sans-serif !important;
        letter-spacing: 0.02em;
    }}
    </style>

    <p class="sidebar-footer">
        集計対象期間: <br> <b>{min_date.strftime('%Y/%m/%d')}</b> ～ <b>{max_date.strftime('%Y/%m/%d')}</b>
    </p>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------------------------------
# メインコンテンツ
# --------------------------------------------------------------------------
st.title("分野別 詳細分析")
st.markdown("特定の分野に焦点を当て、その中でのシリーズ間の比較や詳細な動向を多角的に分析します。")
with st.expander("グラフの使い方（クリックして表示）"):
    st.markdown("""
    - グラフ上でカーソルを動かすと数値を確認できます  
    - 範囲をドラッグすると拡大できます（ダブルクリックでリセット）  
    - 凡例をクリックして項目の表示／非表示を切り替え  
    - グラフ右上のツールバーから画像として保存可能  
    """)
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

if not sorted_majors:
    st.warning("選択した期間に該当するデータがありません。")
else:
    try:
        default_index = sorted_majors.index("人口・世帯")
    except ValueError:
        default_index = 0

    selected_major = st.selectbox(
        '分析したい分野を選択してください',
        sorted_majors,
        index=default_index,
        key='major_selector'
    )

    st.markdown("---")

    if selected_major:
        df_major_filtered = filtered_df[filtered_df['field_major'] == selected_major]
        
        # --- 1. 分野サマリー ---
        st.header(f"{selected_major}分野概要")
        
        # 変更点 1: サマリーセクションの指標を再構成
        total_access = df_major_filtered['access_count'].sum()
        
        # 日数を計算してゼロ除算を回避
        num_days = df_major_filtered['date'].nunique()
        avg_daily_access = total_access / num_days if num_days > 0 else 0
        
        num_organizations = df_major_filtered['organization'].nunique()

        col1, col2 = st.columns(2)
        col1.metric("分野の総アクセス数", f"{total_access:,.0f}")
        col2.metric("期間内の平均日次アクセス数", f"{avg_daily_access:,.0f}")
        
        st.markdown("##### 分野全体のアクセス数推移")
        major_monthly = df_major_filtered.set_index('date').resample('ME')['access_count'].sum()
        fig_major_timeline = px.line(major_monthly, x=major_monthly.index, y=major_monthly.values, labels={'x': '年月', 'y': '月間アクセス数'}, markers=True)
        st.plotly_chart(fig_major_timeline, use_container_width=True)
        
        st.markdown("##### 分野内でのファイル別アクセス数ランキング Top 10")
        top_files = df_major_filtered.groupby(['series_name', 'file_name', 'main_link'])['access_count'].sum().nlargest(10).reset_index()
        
        html_table_top_files = "<table style='width:100%; border-collapse: collapse;'>"
        html_table_top_files += "<thead><tr style='border-bottom: 1px solid #ddd;'><th style='padding: 8px; text-align: left;'>シリーズ名</th><th style='padding: 8px; text-align: left;'>ファイル名</th><th style='padding: 8px; text-align: right;'>アクセス数</th></tr></thead><tbody>"
        for index, row in top_files.iterrows():
            linked_file_name = f"<a href='{row['main_link']}' target='_blank'>{row['file_name']}</a>"
            html_table_top_files += f"<tr style='border-bottom: 1px solid #eee;'><td style='padding: 8px; text-align: left;'>{row['series_name']}</td><td style='padding: 8px; text-align: left;'>{linked_file_name}</td><td style='padding: 8px; text-align: right;'>{row['access_count']:,}</td></tr>"
        html_table_top_files += "</tbody></table>"
        st.markdown(html_table_top_files, unsafe_allow_html=True)

        st.markdown("##### 分野内での組織別アクセス数ランキング")
        org_dist = df_major_filtered.groupby('organization')['access_count'].sum().sort_values(ascending=False).reset_index()
        st.dataframe(org_dist, use_container_width=True, hide_index=True)
        
        st.markdown("---")

        # --- 2. シリーズ時系列比較 ---
        st.header(f"{selected_major}分野時系列比較")
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
        
        # --- 3. 分野内シリーズ一覧 ---
        st.header(f"{selected_major}分野シリーズランクイン状況")
        
        # 変更点 2: シリーズ一覧のサマリーに表示するテキストをここで定義
        all_series_in_major = details_df[details_df['field_major'] == selected_major]
        total_series_in_major_count = all_series_in_major['series_name'].nunique()
        ranked_series_in_major_count = df_major_filtered['series_name'].nunique()
        unranked_series_in_major_count = total_series_in_major_count - ranked_series_in_major_count

        # 割合付きのテキストを作成
        if total_series_in_major_count > 0:
            ranked_text = f"{ranked_series_in_major_count} シリーズ ({ranked_series_in_major_count / total_series_in_major_count:.1%})"
            unranked_text = f"{unranked_series_in_major_count} シリーズ ({unranked_series_in_major_count / total_series_in_major_count:.1%})"
        else:
            ranked_text = f"{ranked_series_in_major_count} シリーズ"
            unranked_text = f"{unranked_series_in_major_count} シリーズ"

        # 3-1. サマリー(KPI)
        kpi_r, kpi_u = st.columns(2)
        kpi_r.metric("分野内のランクインシリーズ数", ranked_text) # 変更点 2
        kpi_u.metric("分野内の圏外シリーズ数", unranked_text) # 変更点 2

        # 3-2. 組織別内訳
        col_ranked_pie, col_unranked_pie = st.columns(2)
        
        ranked_series_in_period = set(df_major_filtered['series_name'].unique())
        all_series_in_major['ランクイン状況'] = all_series_in_major['series_name'].apply(
            lambda x: '○' if x in ranked_series_in_period else '×'
        )
        
        with col_ranked_pie:
            # ランクインしたシリーズの組織内訳 (df_major_filteredから作成)
            ranked_org_dist = all_series_in_major[all_series_in_major['ランクイン状況'] == '○']['organization'].value_counts()
            if not ranked_org_dist.empty:
                fig_pie_ranked_org = px.pie(ranked_org_dist, names=ranked_org_dist.index, values=ranked_org_dist.values, title='ランクインシリーズの組織内訳')
                st.plotly_chart(fig_pie_ranked_org, use_container_width=True)
            else:
                st.markdown("この分野にランクインシリーズはありません。")


        with col_unranked_pie:
            unranked_series_df = all_series_in_major[all_series_in_major['ランクイン状況'] == '×']
            unranked_org_dist = unranked_series_df['organization'].value_counts()
            if not unranked_org_dist.empty:
                fig_pie_unranked_org = px.pie(unranked_org_dist, names=unranked_org_dist.index, values=unranked_org_dist.values, title='圏外シリーズの組織内訳')
                st.plotly_chart(fig_pie_unranked_org, use_container_width=True)
            else:
                st.markdown("この分野に圏外シリーズはありません。")
        
        # 3-3. テーブル
        st.markdown("##### 全シリーズリスト（ランクイン状況：○/×）")
        display_table = all_series_in_major[['series_name', 'ランクイン状況', 'organization']]
        display_table = display_table.rename(columns={'series_name': 'シリーズ名', 'organization': '提供組織'})
        display_table = display_table.sort_values(by='シリーズ名').reset_index(drop=True)

        st.dataframe(display_table, height=300, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # --- 4. ファイル種別分析 ---
        st.header(f"{selected_major}分野ファイル種別分析")
        st.markdown("選択した分野で、どのファイル形式（PDF, Excel, CSVなど）が多く利用されているかを確認できます。")
        
        col_pie, col_bar = st.columns(2)
        with col_pie:
            st.markdown("##### 全体の割合")
            file_type_dist = df_major_filtered.groupby('file_type')['access_count'].sum()
            fig_pie_type = px.pie(file_type_dist, names=file_type_dist.index, values=file_type_dist.values, title='ファイル種別ごとのアクセス割合', hole=0.4)
            st.plotly_chart(fig_pie_type, use_container_width=True)

        with col_bar:
            st.markdown("##### シリーズごとの内訳")
            file_type_by_series = df_major_filtered.groupby(['series_name', 'file_type'])['access_count'].sum().reset_index()
            series_order = df_major_filtered.groupby('series_name')['access_count'].sum().sort_values(ascending=True).index
            
            fig_bar_type = px.bar(
                file_type_by_series, y='series_name', x='access_count', color='file_type',
                orientation='h', labels={'series_name': 'シリーズ名', 'access_count': 'アクセス数', 'file_type': 'ファイル種別'},
                title='シリーズごとのファイル種別アクセス数', category_orders={'series_name': series_order}
            )
            st.plotly_chart(fig_bar_type, use_container_width=True)

        st.markdown("---")
        
        # --- 5. シリーズ詳細ドリルダウン ---
        st.header(f"{selected_major}分野詳細ドリルダウン")
        series_in_major_ranked = sorted(df_major_filtered['series_name'].dropna().unique())

        if not series_in_major_ranked:
                st.warning("この絞り込み条件に該当するシリーズはありません。")
        else:
            series_options = ["▼ 分析したいシリーズを選択..."] + series_in_major_ranked
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

                st.markdown(f"##### {selected_series}内のファイル別アクセス数ランキング")
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