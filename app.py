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

# ================= 1. 治愈系与科技蓝视觉配置 =================
st.set_page_config(page_title="智能影像聚类系统", page_icon="🌿", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f7f9fc; }
    h1, h2, h3 { color: #2c3e50; font-family: 'Helvetica Neue', Arial, sans-serif; }
    .stButton>button {
        background-color: #5c8fb9; color: white; border-radius: 8px; border: none;
        padding: 0.5rem 2rem; transition: all 0.3s; font-weight: bold;
    }
    .stButton>button:hover { background-color: #4a7599; }
    .stat-box {
        background-color: white; padding: 20px; border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; border-top: 4px solid #8eb0a4;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🌿 智能影像特征聚类系统")
st.markdown("基于大语言模型视觉网络，批量提取图片多维心理与实体特征，并自动生成结构化聚类图谱。")

# ================= 2. 后台配置（请替换为您的真实数据） =================
COZE_API_KEY = "cztei_qKrhOhdsGKIqlOeCuI2GZlzrUVDmfiyjfQosJziySKDLS3tmt5oJkyIJtSUiKmHNo"  # 填入第一步获取的Token
WORKFLOW_ID = "7645903007834996762"  
UPLOAD_URL = "https://api.coze.cn/v1/files/upload"
COZE_URL = "https://api.coze.cn/v1/workflow/run"

# ================= 3. 核心通讯逻辑：两步走战略 =================
def upload_to_coze(image_file):
    """步骤一：将图片寄存至 Coze 获取 File ID"""
    headers = {"Authorization": f"Bearer {COZE_API_KEY}"}
    image_file.seek(0)
    files = {"file": (image_file.name, image_file, image_file.type)}
    
    response = requests.post(UPLOAD_URL, headers=headers, files=files)
    if response.status_code == 200:
        res_json = response.json()
        if res_json.get("code") == 0:
            return res_json["data"]["id"]
        else:
            return f"Error: {res_json.get('msg')}"
    return f"Error: HTTP {response.status_code}"

def call_coze_workflow(file_id):
    """步骤二：提交 File ID 给视觉大模型提取特征"""
    headers = {
        "Authorization": f"Bearer {COZE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "workflow_id": WORKFLOW_ID,
        "parameters": {
            "image_input": json.dumps({"id": file_id})
        }
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

# ================= 4. 前端交互与批量处理引擎 =================
st.markdown("---")
uploaded_files = st.file_uploader("📂 请框选或拖拽上传本地图片（支持批量，建议一次 50 张以内）", 
                                  type=["png", "jpg", "jpeg"], accept_multiple_files=True)

if uploaded_files:
    st.info(f"已就绪：共读取到 {len(uploaded_files)} 张影像资料。")
    
    if st.button("🚀 启动特征提取与生态聚类"):
        results = []
        all_keywords = [] # 用于收集所有词汇做聚类
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        table_placeholder = st.empty()
        
        for index, file in enumerate(uploaded_files):
            status_text.markdown(f"**正在解析 ({index+1}/{len(uploaded_files)}):** `{file.name}` ...")
            
            # 1. 上传图片拿 ID
            file_id = upload_to_coze(file)
            
            if "Error" in file_id:
                keywords = f"寄存失败: {file_id}"
                status = "❌ 失败"
            else:
                # 2. 拿 ID 去提词
                keywords = call_coze_workflow(file_id)
                status = "✅ 成功" if "Error" not in keywords else "❌ 失败"
                
                # 清洗特征词并加入总库
                if status == "✅ 成功":
                    words = [w.strip() for w in keywords.replace('，', ',').split(',') if w.strip()]
                    all_keywords.extend(words)
                    keywords = ", ".join(words)
            
            results.append({
                "图片名称": file.name,
                "状态": status,
                "特征聚类词组": keywords
            })
            
            # 实时更新表格与进度
            df_results = pd.DataFrame(results)
            table_placeholder.dataframe(df_results, use_container_width=True)
            progress_bar.progress((index + 1) / len(uploaded_files))
            
            # 防止 API 速率限制，每次请求间隔 1.5 秒
            time.sleep(1.5)
            
        status_text.success("🎉 全套影像特征提取与聚类分析已完成！")
        
        # 导出按钮
        csv = df_results.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 导出明细报表 (Excel/CSV)", data=csv, file_name="心生态_影像特征报表.csv", mime="text/csv")
        
        # ================= 5. 可视化模块：词云与热力图 =================
        if all_keywords:
            st.markdown("---")
            st.subheader("📊 影像特征多维生态图谱")
            
            col1, col2 = st.columns(2)
            
            # 自动下载中文字体（解决 Streamlit 云端乱码问题）
            font_path = "SimHei.ttf"
            if not os.path.exists(font_path):
                urllib.request.urlretrieve("https://raw.githubusercontent.com/StellarCN/scp_zh/master/fonts/SimHei.ttf", font_path)
            
            with col1:
                st.markdown("<div class='stat-box'><h4>☁️ 特征词云聚类</h4></div>", unsafe_allow_html=True)
                word_counts = Counter(all_keywords)
                # 使用科技蓝/治愈系配色生成词云
                wc = WordCloud(font_path=font_path, background_color="white", 
                               width=800, height=600, colormap="ocean_r", max_words=100)
                wc.generate_from_frequencies(word_counts)
                
                fig_wc, ax = plt.subplots(figsize=(8, 6))
                ax.imshow(wc, interpolation="bilinear")
                ax.axis("off")
                st.pyplot(fig_wc)

            with col2:
                st.markdown("<div class='stat-box'><h4>🔥 核心特征热力分布</h4></div>", unsafe_allow_html=True)
                # 取高频前 15 个词绘制热力矩阵
                top_15_words = [word for word, count in word_counts.most_common(15)]
                
                # 构建热力图矩阵数据 (图片 vs 特征词)
                heatmap_data = []
                for res in results:
                    if res["状态"] == "✅ 成功":
                        img_words = res["特征聚类词组"].split(", ")
                        row_data = {"图片名称": res["图片名称"]}
                        for tw in top_15_words:
                            row_data[tw] = 1 if tw in img_words else 0
                        heatmap_data.append(row_data)
                
                df_heatmap = pd.DataFrame(heatmap_data)
                if not df_heatmap.empty:
                    df_heatmap.set_index("图片名称", inplace=True)
                    # 绘制交互式科技蓝热力图
                    fig_hm = px.imshow(df_heatmap, 
                                       color_continuous_scale="Blues",
                                       aspect="auto",
                                       labels=dict(x="核心特征维度", y="影像样本", color="检出频次"))
                    fig_hm.update_layout(margin=dict(l=20, r=20, t=20, b=20))
                    st.plotly_chart(fig_hm, use_container_width=True)
