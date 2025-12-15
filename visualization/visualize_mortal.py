#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mortal AI 分析结果可视化系统
生成交互式图表展示玩家表现
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime
import numpy as np
from scipy import stats
import os
import sys

# Fix console encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def load_data(csv_path, min_rating=80):
    """
    加载CSV数据

    Args:
        csv_path: CSV文件路径
        min_rating: 最小rating阈值，默认80。低于此值的数据将被过滤
    """
    if not os.path.exists(csv_path):
        print(f"❌ 文件不存在: {csv_path}")
        return None

    df = pd.read_csv(csv_path)
    print(f"✅ 成功加载 {len(df)} 条记录")

    # 过滤异常数据：rating < min_rating
    original_count = len(df)
    df = df[df['rating'] >= min_rating].copy()
    filtered_count = original_count - len(df)

    if filtered_count > 0:
        print(f"🔍 过滤掉 {filtered_count} 条异常数据 (rating < {min_rating})")
        print(f"📊 保留 {len(df)} 条有效数据")

    # 转换时间格式 - 自动推断格式
    df['start_time'] = pd.to_datetime(df['start_time'], format='mixed')
    df['date'] = df['start_time'].dt.date

    return df

def create_dashboard(df):
    """创建综合仪表盘 - 4个图表"""

    # 创建子图布局 - 2x2 共4个图表
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            '🏆 位次分布',
            '📊 Rating & Accuracy 趋势图',
            '📊 一致率分布直方图',
            '📈 Sliding Window回归分析'
        ),
        specs=[
            [{"type": "pie"}, {"type": "scatter"}],
            [{"type": "xy"}, {"type": "scatter"}]
        ],
        horizontal_spacing=0.12,
        vertical_spacing=0.15
    )

    # 颜色配置
    rank_colors = {
        1: '#28a745',  # 绿色
        2: '#17a2b8',  # 青色
        3: '#6c757d',  # 灰色
        4: '#dc3545'   # 红色
    }

    # ===== 1. 位次分布饼图 (左上) =====
    rank_counts = df['rank'].value_counts().sort_index()
    labels = ['1st', '2nd', '3rd', '4th']
    values = [rank_counts.get(i, 0) for i in [1, 2, 3, 4]]
    colors_pie = [rank_colors[i] for i in [1, 2, 3, 4]]

    fig.add_trace(
        go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=colors_pie),
            textinfo='label+percent',
            textfont=dict(size=14, color='white'),
            hovertemplate='%{label}<br>次数: %{value}<br>占比: %{percent}<extra></extra>'
        ),
        row=1, col=1
    )

    # ===== 2. Rating & Accuracy 趋势图 (Row 1, Col 2) =====
    # Filter data for trend chart: accuracy >= 65% (avoid extreme outliers)
    df_trend = df[df['match_rate'] >= 65.0].copy()
    total_games = len(df_trend)
    window_size = 20

    # Sort by time
    df_sorted = df_trend.sort_values('start_time').reset_index(drop=True)
    game_indices = list(range(len(df_sorted)))
    time_data = df_sorted['start_time'].values

    # Raw data (scaled to 0-1)
    rating_raw = (df_sorted['rating'] / 100).values
    accuracy_raw = (df_sorted['match_rate'] / 100).values

    # Moving averages
    rating_window = df_sorted['rating'].rolling(window=window_size, min_periods=1).mean() / 100
    accuracy_window = df_sorted['match_rate'].rolling(window=window_size, min_periods=1).mean() / 100

    # Overall averages
    overall_rating = df_sorted['rating'].mean()
    overall_accuracy = df_sorted['match_rate'].mean()

    # Raw rating (thin blue line)
    fig.add_trace(go.Scatter(
        x=game_indices,
        y=rating_raw,
        mode='lines',
        name=f'rating',
        line=dict(color='#3498db', width=1),
        opacity=0.5,
        hovertemplate='对局 #%{x}<br>时间: %{customdata[0]|%Y-%m-%d}<br>Rating: %{customdata[1]:.2f}<extra></extra>',
        customdata=list(zip(time_data, df_sorted['rating'].values)),
        legendgroup='trend',
        showlegend=True
    ), row=1, col=2)

    # Raw accuracy (thin orange line)
    fig.add_trace(go.Scatter(
        x=game_indices,
        y=accuracy_raw,
        mode='lines',
        name=f'accuracy',
        line=dict(color='#ff8c00', width=1),
        opacity=0.5,
        hovertemplate='对局 #%{x}<br>时间: %{customdata[0]|%Y-%m-%d}<br>一致率: %{customdata[1]:.2f}%<extra></extra>',
        customdata=list(zip(time_data, df_sorted['match_rate'].values)),
        legendgroup='trend',
        showlegend=True
    ), row=1, col=2)

    # Rating moving average (thick green line)
    fig.add_trace(go.Scatter(
        x=game_indices,
        y=rating_window,
        mode='lines',
        name=f'rating 趋势',
        line=dict(color='#2ecc71', width=3),
        hovertemplate='对局 #%{x}<br>Rating 均值: %{customdata:.2f}<extra></extra>',
        customdata=(rating_window * 100).values,
        legendgroup='trend',
        showlegend=True
    ), row=1, col=2)

    # Accuracy moving average (thick red line)
    fig.add_trace(go.Scatter(
        x=game_indices,
        y=accuracy_window,
        mode='lines',
        name=f'accuracy 趋势',
        line=dict(color='#e74c3c', width=3),
        hovertemplate='对局 #%{x}<br>一致率均值: %{customdata:.2f}%<extra></extra>',
        customdata=(accuracy_window * 100).values,
        legendgroup='trend',
        showlegend=True
    ), row=1, col=2)

    # Custom tick labels with dates
    num_ticks = 8
    tick_interval = max(1, total_games // num_ticks)
    tick_positions = list(range(0, total_games, tick_interval))

    min_distance = tick_interval * 0.3
    if tick_positions[-1] < total_games - 1:
        if total_games - 1 - tick_positions[-1] >= min_distance:
            tick_positions.append(total_games - 1)
        else:
            tick_positions[-1] = total_games - 1

    tick_labels_trend = []
    for pos in tick_positions:
        date_str = pd.Timestamp(time_data[pos]).strftime('%m-%d')
        tick_labels_trend.append(f"{pos}<br><sub>{date_str}</sub>")

    # ===== 3. Match Rate Distribution Histogram (Row 2, Col 1) =====
    # Calculate statistics
    mean_accuracy = df['match_rate'].mean()
    median_accuracy = df['match_rate'].median()

    # Estimate max y value for vertical lines
    hist_counts, hist_bins = np.histogram(df['match_rate'], bins=30)
    max_count = hist_counts.max()

    # Create histogram
    fig.add_trace(
        go.Histogram(
            x=df['match_rate'],
            nbinsx=30,
            name='一致率分布',
            marker=dict(
                color='#3498db',
                line=dict(color='white', width=1)
            ),
            hovertemplate='一致率: %{x:.1f}%<br>对局数: %{y}<extra></extra>',
            showlegend=False
        ),
        row=2, col=1
    )

    # Add mean line
    fig.add_trace(
        go.Scatter(
            x=[mean_accuracy, mean_accuracy],
            y=[0, max_count * 1.1],
            mode='lines',
            name=f'平均值 ({mean_accuracy:.1f}%)',
            line=dict(color='#e74c3c', width=3, dash='dash'),
            hovertemplate=f'平均一致率: {mean_accuracy:.1f}%<extra></extra>',
            showlegend=True
        ),
        row=2, col=1
    )

    # Add median line
    fig.add_trace(
        go.Scatter(
            x=[median_accuracy, median_accuracy],
            y=[0, max_count * 1.1],
            mode='lines',
            name=f'中位数 ({median_accuracy:.1f}%)',
            line=dict(color='#2ecc71', width=3, dash='dot'),
            hovertemplate=f'中位数一致率: {median_accuracy:.1f}%<extra></extra>',
            showlegend=True
        ),
        row=2, col=1
    )

    # Update axes for histogram
    fig.update_xaxes(title_text="一致率 (%)", row=2, col=1)
    fig.update_yaxes(title_text="对局数", row=2, col=1)

    # ===== 4. Sliding Window Regression (Row 2, Col 2) =====
    # Sort by rating instead of time
    df_slide = df.sort_values('rating').reset_index(drop=True)

    k_values = [50, 100, 200]
    colors = {
        50: '#3498db',   # Blue
        100: '#2ecc71',  # Green
        200: '#e74c3c'   # Red
    }

    results = {}

    for K in k_values:
        df_slide[f'avg_score_{K}'] = df_slide['score'].rolling(window=K, min_periods=K).mean()
        df_windowed = df_slide.dropna(subset=[f'avg_score_{K}']).copy()

        if len(df_windowed) == 0:
            continue

        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            df_windowed['rating'], df_windowed[f'avg_score_{K}']
        )

        results[K] = {
            'slope': slope,
            'intercept': intercept,
            'r_squared': r_value**2,
            'p_value': p_value,
            'data': df_windowed
        }

    # Plot scatter for K=200 only
    if 200 in results:
        k_max = 200
        df_k_max = results[k_max]['data']
        fig.add_trace(
            go.Scatter(
                x=df_k_max['rating'],
                y=df_k_max[f'avg_score_{k_max}'],
                mode='markers',
                name=f'K={k_max} 数据',
                marker=dict(
                    color='lightgray',
                    size=4,
                    opacity=0.3
                ),
                hovertemplate='Rating: %{x:.2f}<br>平均分数: %{y:.0f}<extra></extra>',
                showlegend=False
            ),
            row=2, col=2
        )

    # Plot regression lines
    for K in sorted(results.keys()):
        res = results[K]
        df_windowed = res['data']
        slope = res['slope']
        intercept = res['intercept']
        r_squared = res['r_squared']

        rating_range = np.array([df_windowed['rating'].min(), df_windowed['rating'].max()])
        predicted_scores = slope * rating_range + intercept

        fig.add_trace(
            go.Scatter(
                x=rating_range,
                y=predicted_scores,
                mode='lines',
                name=f'K={K} (R²={r_squared:.3f})',
                line=dict(color=colors[K], width=3),
                hovertemplate=f'K={K}<br>y = {slope:.0f}x + {intercept:.0f}<br>R² = {r_squared:.4f}<extra></extra>',
                showlegend=True
            ),
            row=2, col=2
        )

    # Update axes for sliding window chart
    fig.update_xaxes(title_text="Rating", row=2, col=2)
    fig.update_yaxes(
        title_text="K-Game平均分数",
        range=[25000, 30000],
        autorange=False,
        row=2, col=2
    )

    # ===== Update Layout =====
    fig.update_layout(
        title=dict(
            text=f'🀄 Mortal AI 分析结果仪表盘 ({len(df)} 场对局)',
            font=dict(size=24, color='#2C3E50'),
            x=0.5,
            xanchor='center'
        ),
        height=1000,  # 2x2 layout needs more height
        template='plotly_white',
        font=dict(family="Microsoft YaHei, Arial", size=12)
    )

    # Update axes for trend chart (Row 1, Col 2)
    fig.update_xaxes(
        title_text="对局编号",
        tickmode='array',
        tickvals=tick_positions,
        ticktext=tick_labels_trend,
        row=1, col=2
    )
    fig.update_yaxes(
        title_text="归一化数值",
        range=[0.65, 1.0],
        tickmode='linear',
        dtick=0.05,
        tickformat='.2f',
        row=1, col=2
    )

    return fig, results

def create_stats_table(df, sliding_results=None):
    """创建统计表格"""
    stats_data = {
        '总对局数': len(df),
        '平均 Rating': f"{df['rating'].mean():.2f}",
        '最高 Rating': f"{df['rating'].max():.2f}",
        '最低 Rating': f"{df['rating'].min():.2f}",
        '平均一致率': f"{df['match_rate'].mean():.2f}%",
        '一位次数': f"{(df['rank'] == 1).sum()} ({(df['rank'] == 1).sum() / len(df) * 100:.1f}%)",
        '二位次数': f"{(df['rank'] == 2).sum()} ({(df['rank'] == 2).sum() / len(df) * 100:.1f}%)",
        '三位次数': f"{(df['rank'] == 3).sum()} ({(df['rank'] == 3).sum() / len(df) * 100:.1f}%)",
        '四位次数': f"{(df['rank'] == 4).sum()} ({(df['rank'] == 4).sum() / len(df) * 100:.1f}%)",
        '平均点数': f"{df['score'].mean():.0f}"
    }

    # Add sliding window regression results (only K=200, most reliable)
    rating_impact_tooltip = None
    if sliding_results and 200 in sliding_results:
        res = sliding_results[200]
        slope = res['slope']
        r_squared = res['r_squared']
        p_value = res['p_value']

        # Convert R² to percentage and determine significance
        explained_variance = r_squared * 100
        if p_value < 0.001:
            significance = "极显著相关"
        elif p_value < 0.01:
            significance = "高度显著"
        elif p_value < 0.05:
            significance = "显著相关"
        else:
            significance = "弱相关"

        stats_data['Rating影响力'] = f"{slope:.0f}"
        rating_impact_tooltip = f"Rating每提升1点，长期平均分数增加{slope:.0f}分 ({significance}，可解释{explained_variance:.1f}%分数波动)"

    # 创建表格HTML
    html = '<div style="margin: 20px; padding: 20px; background: #f8f9fa; border-radius: 10px;">'
    html += '<h2 style="color: #2C3E50;">📊 统计摘要</h2>'
    html += '<table style="width: 100%; border-collapse: collapse;">'

    for key, value in stats_data.items():
        # Add tooltip for Rating影响力
        if key == 'Rating影响力' and rating_impact_tooltip:
            html += f'''
            <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 10px; font-weight: bold; color: #34495E;">{key}</td>
                <td style="padding: 10px; text-align: right; color: #2E86DE; text-decoration: underline dotted; cursor: default;" title="{rating_impact_tooltip}">{value}</td>
            </tr>
            '''
        else:
            html += f'''
            <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 10px; font-weight: bold; color: #34495E;">{key}</td>
                <td style="padding: 10px; text-align: right; color: #2E86DE;">{value}</td>
            </tr>
            '''

    html += '</table></div>'
    return html

def generate_html(df, fig, sliding_results, output_path):
    """生成完整的HTML报告"""

    # 获取图表HTML
    fig_html = fig.to_html(include_plotlyjs='cdn', div_id='dashboard')

    # 统计表格
    stats_html = create_stats_table(df, sliding_results)

    # 数据表格 - 添加room字段和链接，使用中文列名
    # 按时间降序排序（最新的在最上面）
    df_sorted = df.sort_values('start_time', ascending=False).copy()

    # 房间英文转中文映射
    room_map = {
        'Throne': '王座之间',
        'Jade': '玉之间',
        'Gold': '金之间',
        'Unknown': '未知'
    }
    df_sorted['room_cn'] = df_sorted['room'].map(room_map).fillna('未知')

    # 选择要显示的列
    columns_to_show = ['start_time', 'score', 'rank', 'room_cn', 'rating', 'match_rate']

    # 如果有report_url列，添加链接列
    if 'report_url' in df_sorted.columns:
        columns_to_show.append('report_url')

    table_df = df_sorted[columns_to_show].copy()

    # 设置中文列名
    if 'report_url' in columns_to_show:
        table_df.columns = ['时间', '得分', '位次', '房间', 'Rating', '一致率', '分析链接']
    else:
        table_df.columns = ['时间', '得分', '位次', '房间', 'Rating', '一致率']

    # 如果有分析链接列，转换为HTML超链接
    if '分析链接' in table_df.columns:
        table_df['分析链接'] = table_df['分析链接'].apply(
            lambda x: f'<a href="{x}" target="_blank">查看分析</a>' if pd.notna(x) and x != '' else '-'
        )

    table_html = table_df.to_html(
        index=False,
        classes='data-table',
        border=0,
        escape=False,  # 允许HTML链接
        formatters={
            'Rating': lambda x: f'{x:.2f}',
            '一致率': lambda x: f'{x:.1f}%'
        }
    )

    # 完整HTML
    html = f'''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mortal AI 分析结果</title>
        <style>
            body {{
                font-family: "Microsoft YaHei", Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }}
            .container {{
                max-width: 1600px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            }}
            h1 {{
                color: #2C3E50;
                text-align: center;
                margin-bottom: 30px;
                font-size: 2.5em;
            }}
            .data-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                font-size: 14px;
            }}
            .data-table th {{
                background: #3498DB;
                color: white;
                padding: 12px;
                text-align: left;
                cursor: pointer;
                user-select: none;
                position: relative;
            }}
            .data-table th:hover {{
                background: #2980B9;
            }}
            .data-table th.sortable::after {{
                content: ' ⇅';
                opacity: 0.5;
                font-size: 0.8em;
            }}
            .data-table th.sort-asc::after {{
                content: ' ▲';
                opacity: 1;
            }}
            .data-table th.sort-desc::after {{
                content: ' ▼';
                opacity: 1;
            }}
            .data-table td {{
                padding: 10px;
                border-bottom: 1px solid #ecf0f1;
            }}
            .data-table tr:hover {{
                background: #f8f9fa;
            }}
            .data-table a {{
                color: #3498DB;
                text-decoration: none;
                font-weight: bold;
            }}
            .data-table a:hover {{
                color: #2980B9;
                text-decoration: underline;
            }}
            .section {{
                margin: 30px 0;
            }}
            .timestamp {{
                text-align: center;
                color: #7f8c8d;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🀄 Mortal AI 分析结果报告</h1>

            {stats_html}

            <div class="section">
                {fig_html}
            </div>

            <div class="section">
                <h2 style="color: #2C3E50;">📋 详细数据</h2>
                {table_html}
            </div>

            <div class="timestamp">
                生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            </div>
        </div>

        <script>
        // 表格排序功能
        document.addEventListener('DOMContentLoaded', function() {{
            const table = document.querySelector('.data-table');
            if (!table) return;

            const headers = table.querySelectorAll('th');
            let currentSort = {{ column: -1, ascending: true }};

            headers.forEach((header, index) => {{
                // 为时间和Rating列添加sortable类
                if (index === 0 || index === 4) {{
                    header.classList.add('sortable');

                    header.addEventListener('click', function() {{
                        sortTable(index);
                    }});
                }}
            }});

            function sortTable(columnIndex) {{
                const tbody = table.querySelector('tbody');
                const rows = Array.from(tbody.querySelectorAll('tr'));

                // 确定排序方向
                let ascending = true;
                if (currentSort.column === columnIndex) {{
                    ascending = !currentSort.ascending;
                }} else {{
                    ascending = true;
                }}

                // 排序
                rows.sort((a, b) => {{
                    const cellA = a.cells[columnIndex].textContent.trim();
                    const cellB = b.cells[columnIndex].textContent.trim();

                    let valA, valB;

                    if (columnIndex === 0) {{
                        // 时间列 - 转换为日期比较
                        valA = new Date(cellA);
                        valB = new Date(cellB);
                    }} else if (columnIndex === 4) {{
                        // Rating列 - 数值比较
                        valA = parseFloat(cellA);
                        valB = parseFloat(cellB);
                    }}

                    if (valA < valB) return ascending ? -1 : 1;
                    if (valA > valB) return ascending ? 1 : -1;
                    return 0;
                }});

                // 更新DOM
                rows.forEach(row => tbody.appendChild(row));

                // 更新表头样式
                headers.forEach(h => {{
                    h.classList.remove('sort-asc', 'sort-desc');
                }});

                if (ascending) {{
                    headers[columnIndex].classList.add('sort-asc');
                }} else {{
                    headers[columnIndex].classList.add('sort-desc');
                }}

                // 记录当前排序状态
                currentSort = {{ column: columnIndex, ascending: ascending }};
            }}
        }});
        </script>
    </body>
    </html>
    '''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ HTML报告已生成: {output_path}")

def main():
    import argparse

    # 命令行参数解析
    parser = argparse.ArgumentParser(
        description='Mortal AI 分析结果可视化系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python visualize_mortal.py                    # 使用默认设置 (min_rating=80)
  python visualize_mortal.py --min-rating 85    # 只统计 rating >= 85 的数据
  python visualize_mortal.py --min-rating 0     # 统计所有数据，不过滤
        '''
    )
    parser.add_argument(
        '--min-rating',
        type=float,
        default=80,
        help='最小rating阈值，低于此值的数据将被过滤（默认: 80）'
    )
    args = parser.parse_args()

    # 查找CSV文件
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)

    # 按优先级查找CSV文件
    possible_paths = [
        os.path.join(parent_dir, 'data', 'mortal_results_temp.csv'),
        os.path.join(parent_dir, 'data', 'mortal_results.csv')
    ]

    csv_path = None
    for path in possible_paths:
        if os.path.exists(path):
            csv_path = path
            break

    if csv_path is None:
        print("❌ 找不到数据文件！")
        print("请确保以下文件之一存在：")
        for path in possible_paths:
            print(f"  - {path}")
        return

    print(f"📂 读取数据文件: {csv_path}")
    print(f"⚙️  Rating过滤阈值: {args.min_rating}")

    # 加载数据
    df = load_data(csv_path, min_rating=args.min_rating)
    if df is None or len(df) == 0:
        print("❌ 没有数据可供分析")
        return

    # 创建图表
    print("📊 生成可视化图表...")
    fig, sliding_results = create_dashboard(df)

    # 生成HTML
    output_path = os.path.join(os.path.dirname(__file__), 'mortal_dashboard.html')
    print("📝 生成HTML报告...")
    generate_html(df, fig, sliding_results, output_path)

    print(f"\n✨ 完成！请打开以下文件查看结果:")
    print(f"   {output_path}")

    # 自动打开浏览器
    import webbrowser
    webbrowser.open(f'file://{os.path.abspath(output_path)}')

if __name__ == '__main__':
    main()
