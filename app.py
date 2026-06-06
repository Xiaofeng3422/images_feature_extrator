import streamlit as st
import requests
import json
import time
import pandas as pd
from collections import Counter
import plotly.graph_objects as go
from wordcloud import WordCloud
import urllib.request
import os
import matplotlib.pyplot as plt
import networkx as nx
import itertools
import io  # 💡 新增：用于在内存中处理文件导出的库

# ================= 1. 治愈系与科技蓝视觉配置 (沉浸式 UI) =================
st.set_page_config(page_title="重智·心生态 | 影像聚类系统", page_icon="🌿", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f8f9; }
    h1, h2, h3 { color: #2c3e50; font-family: 'Helvetica Neue', Arial, sans-serif; font-weight: 600; }
    .stButton>button {
        background: linear-gradient(135deg, #6ba3b8 0%, #4a7599 100%);
        color: white; border-radius: 30px; border: none;
        padding: 0.6rem 2.5rem; font-weight: bold; font-size: 16px;
        transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(74, 117, 153, 0.3);
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(74, 117, 153, 0.5); }
    .stat-box {
        background-color: rgba(255, 255, 255, 0.9); padding: 25px; border-radius: 15px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.04); text-align: center; border-top: 5px solid #8eb0a4;
    }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.title("🌿 心生态 | 智能影像特征聚类系统")
st.markdown("<p style='color:#666; font-size:16px;'>基于大语言模型视觉网络，深度解析图文心像，自动构建结构化心理生态图谱。</p>", unsafe_allow_html=True)

# ================= 2. 后台配置（👇 请在此处替换为您的真实数据 👇） =================
COZE_API_KEY = "pat_xtIkaIOtOvrwtxLl3VUp3uy2XmqPmDUmRg9u6ePR9oBaOfDIC11xILn8yvQ0QQAW"  # 👈 替换为真实 Token
WORKFLOW_ID = "7645903007834996762"         # 👈 替换为真实 工作流 ID
UPLOAD_URL = "https://api.coze.cn/v1/files/upload"
COZE_URL = "https://api.coze.cn/v1/workflow/run"

# ================= 3. 核心通讯逻辑 =================
def upload_to_coze(image_file):
    headers = {"Authorization": f"Bearer {COZE_API_KEY}"}
    image_file.seek(0)
    files = {"file": (image_file.name, image_file, image_file.type)}
    response = requests.post(UPLOAD_URL, headers=headers, files=files)
    if response.status_code == 200:
        res = response.json()
        return res["data"]["id"] if res.get("code") == 0 else f"Error: {res.get('msg')}"
    return f"Error: HTTP {response.status_code}"

def call_coze_workflow(file_id):
    headers = {"Authorization": f"Bearer {COZE_API_KEY}", "Content-Type": "application/json"}
    payload = {"workflow_id": WORKFLOW_ID, "parameters": {"image_input": json.dumps({"file_id": file_id})}}
    response = requests.post(COZE_URL, headers=headers, json=payload)
    if response.status_code == 200:
        res = response.json()
        if str(res.get("code")) != "0": return f"Error: {res.get('msg')}"
        try:
            out_data = json.loads(res.get("data", ""))
            return out_data.get("result_keywords", str(out_data))
        except:
            return res.get("data", "").strip('"')
    return f"Error: HTTP {response.status_code}"

# ================= 4. 双轨制交互架构 =================
st.markdown("---")
tab1, tab2 = st.tabs(["✨ 视觉解析提取室 (实机演示)", "🌌 生态图谱渲染舱 (极速生成)"])

# ----------------- 通道一：提取与展示 -----------------
with tab1:
    st.markdown("#### 1. 影像资料上传")
    uploaded_images = st.file_uploader("支持框选或拖拽上传，系统将通过视觉模型逐一解构影像特征。", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    if uploaded_images:
        st.toast(f"✅ 成功挂载 {len(uploaded_images)} 份影像资料，等待解析。", icon="📂")
        if st.button("🚀 启动深度解析流"):
            results = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            table_ph = st.empty()
            
            for idx, file in enumerate(uploaded_images):
                status_text.markdown(f"**正在解构影像 ({idx+1}/{len(uploaded_images)}):** `{file.name}` ...")
                file_id = upload_to_coze(file)
                if "Error" in file_id:
                    keywords, status = f"解析异常: {file_id}", "❌ 失败"
                else:
                    keywords = call_coze_workflow(file_id)
                    status = "❌ 失败" if "Error" in keywords else "✅ 成功"
                    if status == "✅ 成功":
                        keywords = ", ".join([w.strip() for w in keywords.replace('，', ',').split(',') if w.strip()])
                
                results.append({"影像名称": file.name, "处理状态": status, "核心特征组": keywords})
                table_ph.dataframe(pd.DataFrame(results), use_container_width=True)
                progress_bar.progress((idx + 1) / len(uploaded_images))
                time.sleep(1.5) 
                
            status_text.success("🎉 影像解析任务圆满完成！您可将结果导出为生态库文件。")
            st.balloons()
            csv_data = pd.DataFrame(results).to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 导出特征矩阵库 (CSV)", data=csv_data, file_name="心生态_特征矩阵库.csv", mime="text/csv")

# ----------------- 通道二：离线极速渲染 (兼容 CSV/Excel + 双图表导出) -----------------
with tab2:
    st.markdown("#### 2. 多维生态全景映射")
    uploaded_file = st.file_uploader("请导入已沉淀的特征矩阵库 (支持 CSV 或 Excel 格式)", type=["csv", "xlsx", "xls"])
    
    if uploaded_file:
        st.toast("✅ 数据源接入成功，渲染引擎已就绪。", icon="🔋")
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
                
            df.columns = [str(col).strip().replace('\ufeff', '') for col in df.columns]
            
            with st.expander("👁️ 查看源数据矩阵明细"):
                st.dataframe(df, use_container_width=True)
            
            status_col = next((c for c in ["处理状态", "状态"] if c in df.columns), None)
            keyword_col = next((c for c in ["核心特征组", "特征聚类词组"] if c in df.columns), None)
            img_col = next((c for c in ["影像名称", "图片名称"] if c in df.columns), None)
            
            if not status_col or not keyword_col:
                st.error("⚠️ 数据源维度不匹配，请确保表中包含【状态】与【特征组】相关的列。")
            else:
                if st.button("✨ 瞬间映射全景图谱"):
                    with st.spinner('正在为您生成词汇星云与心智神经网络...'):
                        time.sleep(0.8) 
                        all_keywords, valid_results = [], []
                        
                        for _, row in df.iterrows():
                            if "成功" in str(row[status_col]) and pd.notna(row[keyword_col]):
                                img_name = row[img_col] if img_col else f"样本_{_}"
                                words = [w.strip() for w in str(row[keyword_col]).replace('，', ',').split(',') if w.strip()]
                                all_keywords.extend(words)
                                valid_results.append({"name": img_name, "words": words})
                        
                        if not all_keywords:
                            st.warning("⚠️ 生态库中暂无有效的特征词组。")
                        else:
                            st.toast("🎉 图谱渲染完毕！", icon="🎨")
                            st.markdown("<br>", unsafe_allow_html=True)
                            col_left, col_right = st.columns(2)
                            
                            font_path = "SimHei.ttf"
                            if not os.path.exists(font_path):
                                try:
                                    urllib.request.urlretrieve("https://raw.githubusercontent.com/StellarCN/scp_zh/master/fonts/SimHei.ttf", font_path)
                                except: font_path = None
                            
                            # ================= 渲染左侧：静态词云图及导出 =================
                            with col_left:
                                st.markdown("<div class='stat-box'><h4>☁️ 心境特征星云</h4></div>", unsafe_allow_html=True)
                                word_counts = Counter(all_keywords)
                                wc = WordCloud(font_path=font_path, background_color="rgba(255,255,255,0)", mode="RGBA",
                                               width=800, height=600, colormap="GnBu", max_words=80).generate_from_frequencies(word_counts)
                                fig_wc, ax = plt.subplots(figsize=(8, 6))
                                fig_wc.patch.set_alpha(0) 
                                ax.imshow(wc, interpolation="bilinear")
                                ax.axis("off")
                                st.pyplot(fig_wc)
                                
                                # 💡 词云静态图导出逻辑
                                img_buf = io.BytesIO()
                                fig_wc.savefig(img_buf, format='png', transparent=True, bbox_inches='tight')
                                img_buf.seek(0)
                                st.download_button(label="💾 下载静态词云图 (PNG格式)", data=img_buf, file_name="心境特征星云.png", mime="image/png", use_container_width=True)

                            # ================= 渲染右侧：动态共现网络图及导出 =================
                            with col_right:
                                st.markdown("<div class='stat-box'><h4>🕸️ 核心特征心智网络</h4></div>", unsafe_allow_html=True)
                                
                                co_occurrences = {}
                                node_weights = Counter()
                                
                                for res in valid_results:
                                    words = res["words"]
                                    for w in words: node_weights[w] += 1
                                    pairs = list(itertools.combinations(set(words), 2))
                                    for pair in pairs:
                                        pair = tuple(sorted(pair))
                                        co_occurrences[pair] = co_occurrences.get(pair, 0) + 1
                                
                                top_nodes = [w for w, c in node_weights.most_common(25)]
                                
                                G = nx.Graph()
                                for node in top_nodes: G.add_node(node, size=node_weights[node])
                                    
                                for (w1, w2), weight in co_occurrences.items():
                                    if w1 in top_nodes and w2 in top_nodes and weight >= 1:
                                        G.add_edge(w1, w2, weight=weight)
                                        
                                if len(G.nodes) > 0:
                                    pos = nx.spring_layout(G, k=0.8, iterations=50, seed=42)
                                    edge_x, edge_y = [], []
                                    for edge in G.edges():
                                        x0, y0 = pos[edge[0]]
                                        x1, y1 = pos[edge[1]]
                                        edge_x.extend([x0, x1, None])
                                        edge_y.extend([y0, y1, None])
                                        
                                    edge_trace = go.Scatter(
                                        x=edge_x, y=edge_y,
                                        line=dict(width=1.2, color='rgba(107, 163, 184, 0.4)'), 
                                        hoverinfo='none', mode='lines')
                                        
                                    node_x, node_y, node_text, node_size = [], [], [], []
                                    for node in G.nodes():
                                        x, y = pos[node]
                                        node_x.append(x); node_y.append(y); node_text.append(node)
                                        node_size.append(G.nodes[node]['size'] * 3.5 + 12) 
                                        
                                    node_trace = go.Scatter(
                                        x=node_x, y=node_y, mode='markers+text',
                                        text=node_text, textposition="top center", hoverinfo='text',
                                        textfont=dict(family="SimHei, sans-serif", size=13, color="#2c3e50"),
                                        marker=dict(
                                            showscale=False, color='#5c8fb9', size=node_size,
                                            line_width=2, line_color='white'
                                        ))
                                            
                                    fig_net = go.Figure(data=[edge_trace, node_trace],
                                                 layout=go.Layout(
                                                    showlegend=False, hovermode='closest',
                                                    margin=dict(b=10,l=10,r=10,t=10),
                                                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                                                    )
                                    st.plotly_chart(fig_net, use_container_width=True, config={'displayModeBar': False})
                                    
                                    # 💡 动态交互图导出逻辑
                                    html_buf = io.StringIO()
                                    fig_net.write_html(html_buf, include_plotlyjs="cdn", full_html=True)
                                    html_buf.seek(0)
                                    st.download_button(label="💾 下载动态交互网络图 (HTML格式)", data=html_buf.getvalue(), file_name="心智动态网络.html", mime="text/html", use_container_width=True)
                                else:
                                    st.info("数据量不足，无法生成网络图。")
        except Exception as e:
            st.error(f"⚠️ 文件流读取异常，请检查文件格式是否损坏: {e}")
