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
with tab2:
    st.markdown("#### 2. 多维生态全景映射")
    uploaded_csv = st.file_uploader("请导入已沉淀的特征矩阵库 (CSV 格式)，系统将为您构建宏观生态图谱。", type=["csv"])
    
    if uploaded_csv:
        st.toast("✅ 数据源接入成功，渲染引擎已就绪。", icon="🔋")
        try:
            df = pd.read_csv(uploaded_csv)
            
            # 使用 Expander 把枯燥的数据表折叠起来，保持界面清爽
            with st.expander("👁️ 查看源数据矩阵明细"):
                st.dataframe(df, use_container_width=True)
            
            if "核心特征组" not in df.columns or "处理状态" not in df.columns:
                st.error("⚠️ 数据源维度不匹配，请确保包含【处理状态】与【核心特征组】。")
            else:
                if st.button("✨ 瞬间映射全景图谱"):
                    with st.spinner('正在为您生成词汇星云与热力映射矩阵...'):
                        time.sleep(0.8) # 故意加一点极短的停顿，增强大屏展示时的期待感
                        all_keywords = []
                        valid_results = []
                        
                        for _, row in df.iterrows():
                            if str(row["处理状态"]) == "✅ 成功" and pd.notna(row["核心特征组"]):
                                img_name = row["影像名称"] if "影像名称" in df.columns else f"样本_{_}"
                                words_str = str(row["核心特征组"])
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
                            
                            with col_left:
                                st.markdown("<div class='stat-box'><h4>☁️ 心境特征星云</h4></div>", unsafe_allow_html=True)
                                word_counts = Counter(all_keywords)
                                wc = WordCloud(font_path=font_path, background_color="rgba(255, 255, 255, 0)", mode="RGBA",
                                               width=800, height=600, colormap="GnBu", max_words=80) # 改为更治愈的蓝绿渐变色系
                                wc.generate_from_frequencies(word_counts)
                                
                                fig_wc, ax = plt.subplots(figsize=(8, 6))
                                fig_wc.patch.set_alpha(0) # 背景透明
                                ax.imshow(wc, interpolation="bilinear")
                                ax.axis("off")
                                st.pyplot(fig_wc)

                            with col_right:
                                st.markdown("<div class='stat-box'><h4>🔥 核心要素频次热力</h4></div>", unsafe_allow_html=True)
                                top_15_words = [word for word, count in word_counts.most_common(12)] # 减少到12个，图表更精致
                                
                                heatmap_data = []
                                for res in valid_results:
                                    row_data = {"样本标号": res["name"]}
                                    for tw in top_15_words:
                                        row_data[tw] = 1 if tw in res["words"] else 0
                                    heatmap_data.append(row_data)
                                
                                df_heatmap = pd.DataFrame(heatmap_data)
                                if not df_heatmap.empty:
                                    df_heatmap.set_index("样本标号", inplace=True)
                                    fig_hm = px.imshow(df_heatmap, 
                                                       color_continuous_scale="Teal", # 换成高级质感的 Teal 色系
                                                       aspect="auto",
                                                       labels=dict(x="要素维度", y="样本", color="触发律"))
                                    # 去除背景网格，让界面更极简
                                    fig_hm.update_layout(margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                                    st.plotly_chart(fig_hm, use_container_width=True)
        except Exception as e:
            st.error(f"⚠️ 文件流读取异常: {e}")
