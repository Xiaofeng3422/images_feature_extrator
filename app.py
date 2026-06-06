import streamlit as st
import requests
import json
import time
import pandas as pd
from collections import Counter
import plotly.express as px
from wordcloud import WordCloud
import urllib.request
import os
import matplotlib.pyplot as plt
import networkx as nx
import itertools
import plotly.graph_objects as go

# ================= 1. 治愈系与科技蓝视觉配置 (沉浸式 UI) =================
st.set_page_config(page_title="心生态 | 影像聚类系统", page_icon="🌿", layout="wide")

st.markdown("""
    <style>
    /* 全局柔和背景 */
    .stApp { background-color: #f4f8f9; }
    h1, h2, h3 { color: #2c3e50; font-family: 'Helvetica Neue', Arial, sans-serif; font-weight: 600; }
    
    /* 按钮高级动效 */
    .stButton>button {
        background: linear-gradient(135deg, #6ba3b8 0%, #4a7599 100%);
        color: white; border-radius: 30px; border: none;
        padding: 0.6rem 2.5rem; font-weight: bold; font-size: 16px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(74, 117, 153, 0.3);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(74, 117, 153, 0.5);
    }
    .stButton>button:active {
        transform: translateY(1px);
    }
    
    /* 数据卡片悬浮效果 */
    .stat-box {
        background-color: rgba(255, 255, 255, 0.9);
        padding: 25px; border-radius: 15px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.04);
        text-align: center; border-top: 5px solid #8eb0a4;
        transition: transform 0.3s ease;
    }
    .stat-box:hover { transform: translateY(-5px); }
    
    /* 隐藏原生的 Streamlit 菜单和页脚，让展示更干净 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.title("🌿 心生态 | 智能影像特征聚类系统")
st.markdown("<p style='color:#666; font-size:16px;'>基于大语言模型视觉网络，深度解析图文心像，自动构建结构化心理生态图谱。</p>", unsafe_allow_html=True)

# ================= 2. 后台配置（请替换为您的真实数据） =================
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
        res_json = response.json()
        if res_json.get("code") == 0:
            return res_json["data"]["id"]
        return f"Error: {res_json.get('msg')}"
    return f"Error: HTTP {response.status_code}"

def call_coze_workflow(file_id):
    headers = {
        "Authorization": f"Bearer {COZE_API_KEY}",
        "Content-Type": "application/json"
    }
    image_param = json.dumps({"file_id": file_id})
    payload = {
        "workflow_id": WORKFLOW_ID,
        "parameters": {"image_input": image_param}
    }
    response = requests.post(COZE_URL, headers=headers, json=payload)
    if response.status_code == 200:
        res_json = response.json()
        if str(res_json.get("code")) != "0":
            return f"Error: {res_json.get('msg')}"
        output_str = res_json.get("data", "")
        try:
            output_data = json.loads(output_str)
            if "result_keywords" in output_data:
                return output_data["result_keywords"]
            return str(output_data)
        except:
            return output_str.strip('"')
    return f"Error: HTTP {response.status_code}"

# ================= 4. 双轨制交互架构 =================
st.markdown("---")
# 使用更柔和的 Emoji 区分标签页
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
            table_placeholder = st.empty()
            
            for index, file in enumerate(uploaded_images):
                status_text.markdown(f"**正在解构影像 ({index+1}/{len(uploaded_images)}):** `{file.name}` ...")
                
                file_id = upload_to_coze(file)
                if "Error" in file_id:
                    keywords = f"解析异常: {file_id}"
                    status = "❌ 失败"
                else:
                    keywords = call_coze_workflow(file_id)
                    status = "✅ 成功" if "Error" not in keywords else "❌ 失败"
                    if status == "✅ 成功":
                        words = [w.strip() for w in keywords.replace('，', ',').split(',') if w.strip()]
                        keywords = ", ".join(words)
                
                results.append({"影像名称": file.name, "处理状态": status, "核心特征组": keywords})
                
                df_results = pd.DataFrame(results)
                table_placeholder.dataframe(df_results, use_container_width=True)
                progress_bar.progress((index + 1) / len(uploaded_images))
                time.sleep(1.5) 
                
            status_text.success("🎉 影像解析任务圆满完成！您可将结果导出为生态库文件。")
            st.balloons() # 庆祝特效
            
            csv = df_results.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 导出特征矩阵库 (CSV)", data=csv, file_name="心生态_特征矩阵库.csv", mime="text/csv")

# ----------------- 通道二：离线极速渲染 -----------------
# ----------------- 通道二：离线极速渲染 -----------------
with tab2:
    st.markdown("#### 2. 多维生态全景映射")
    uploaded_csv = st.file_uploader("请导入已沉淀的特征矩阵库 (CSV 格式)，系统将为您构建宏观生态图谱。", type=["csv"])
    
    if uploaded_csv:
        st.toast("✅ 数据源接入成功，渲染引擎已就绪。", icon="🔋")
        try:
            df = pd.read_csv(uploaded_csv)
            
            with st.expander("👁️ 查看源数据矩阵明细"):
                st.dataframe(df, use_container_width=True)
            
            # 💡 强悍的兼容机制：同时兼容旧版和新版表头
            status_col = "处理状态" if "处理状态" in df.columns else ("状态" if "状态" in df.columns else None)
            keyword_col = "核心特征组" if "核心特征组" in df.columns else ("特征聚类词组" if "特征聚类词组" in df.columns else None)
            img_col = "影像名称" if "影像名称" in df.columns else ("图片名称" if "图片名称" in df.columns else None)
            
            if not status_col or not keyword_col:
                st.error("⚠️ 数据源维度不匹配，请确保表中包含表示【状态】与【特征词】的列。")
            else:
                if st.button("✨ 瞬间映射全景图谱"):
                    with st.spinner('正在为您生成词汇星云与热力映射矩阵...'):
                        time.sleep(0.8) 
                        all_keywords = []
                        valid_results = []
                        
                        for _, row in df.iterrows():
                            # 💡 乱码免疫机制：只要包含"成功"两字就算过，无视前面的问号或表情符号
                            if "成功" in str(row[status_col]) and pd.notna(row[keyword_col]):
                                img_name = row[img_col] if img_col else f"样本_{_}"
                                words_str = str(row[keyword_col])
                                words = [w.strip() for w in words_str.split(',') if w.strip()]
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
                                except:
                                    font_path = None
                            
                           # ================= 新图表：心智神经网络 (共现关系网络图) =================
                            with col_right:
                                st.markdown("<div class='stat-box'><h4>🕸️ 核心特征共现网络</h4></div>", unsafe_allow_html=True)
                                
                                # 1. 统计特征词频与共现频次
                                co_occurrences = {}
                                node_weights = Counter()
                                
                                for res in valid_results:
                                    words = res["words"]
                                    for w in words:
                                        node_weights[w] += 1
                                    
                                    # 利用排列组合，找出同一幅画中同时出现的词对
                                    pairs = list(itertools.combinations(set(words), 2))
                                    for pair in pairs:
                                        pair = tuple(sorted(pair)) # 排序保证 (A,B) 和 (B,A) 算同一个
                                        co_occurrences[pair] = co_occurrences.get(pair, 0) + 1
                                
                                # 为了防止连线密集成“毛线球”，我们提取出现频次最高的前 25 个核心词
                                top_nodes = [w for w, c in node_weights.most_common(25)]
                                
                                # 2. 构建 NetworkX 图模型
                                G = nx.Graph()
                                for node in top_nodes:
                                    G.add_node(node, size=node_weights[node])
                                    
                                for (w1, w2), weight in co_occurrences.items():
                                    if w1 in top_nodes and w2 in top_nodes and weight >= 1:
                                        G.add_edge(w1, w2, weight=weight)
                                        
                                if len(G.nodes) > 0:
                                    # 使用弹簧布局算法 (Spring Layout) 自动计算节点的优美排版
                                    pos = nx.spring_layout(G, k=0.8, iterations=50, seed=42)
                                    
                                    # 3. 将 NetworkX 数据转化为 Plotly 惊艳的交互图
                                    edge_x, edge_y = [], []
                                    for edge in G.edges():
                                        x0, y0 = pos[edge[0]]
                                        x1, y1 = pos[edge[1]]
                                        edge_x.extend([x0, x1, None])
                                        edge_y.extend([y0, y1, None])
                                        
                                    # 绘制突触连线
                                    edge_trace = go.Scatter(
                                        x=edge_x, y=edge_y,
                                        line=dict(width=1.2, color='rgba(107, 163, 184, 0.4)'), # 治愈系半透明连线
                                        hoverinfo='none', mode='lines')
                                        
                                    # 绘制神经元节点
                                    node_x, node_y, node_text, node_size = [], [], [], []
                                    for node in G.nodes():
                                        x, y = pos[node]
                                        node_x.append(x)
                                        node_y.append(y)
                                        node_text.append(node)
                                        # 节点大小随词频动态放大
                                        node_size.append(G.nodes[node]['size'] * 3.5 + 12) 
                                        
                                    node_trace = go.Scatter(
                                        x=node_x, y=node_y, mode='markers+text',
                                        text=node_text, textposition="top center", hoverinfo='text',
                                        textfont=dict(family="SimHei, sans-serif", size=13, color="#2c3e50"),
                                        marker=dict(
                                            showscale=False, color='#5c8fb9', size=node_size,
                                            line_width=2, line_color='white',
                                            # 添加呼吸灯一样的发光阴影特效
                                            boxshadow="0px 0px 10px rgba(92, 143, 185, 0.6)" 
                                        ))
                                            
                                    fig_net = go.Figure(data=[edge_trace, node_trace],
                                                 layout=go.Layout(
                                                    showlegend=False, hovermode='closest',
                                                    margin=dict(b=10,l=10,r=10,t=10),
                                                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                                                    )
                                    # 去除点击图表时的边框高亮，提升质感
                                    st.plotly_chart(fig_net, use_container_width=True, config={'displayModeBar': False})
                                else:
                                    st.info("数据量不足，无法生成网络图。")
