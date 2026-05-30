import streamlit as st
import requests
import json
import time
import pandas as pd
import base64

# ================= 1. 页面亲和力视觉配置 =================
st.set_page_config(
    page_title="智能影像特征深度提取系统",
    page_icon="🎨",
    layout="centered"
)

# 使用自定义样式注入“温度”，让界面更柔和、专业
st.markdown("""
    <style>
    .main { background-color: #fcfbfa; }
    h1 { color: #3c3a37; font-family: 'Helvetica Neue', Arial, sans-serif; }
    .stButton>button {
        background-color: #8fa89b;
        color: white;
        border-radius: 20px;
        border: none;
        padding: 0.5rem 2rem;
        transition: all 0.3s;
    }
    .stButton>button:hover { background-color: #768f82; border: none; }
    </style>
""", unsafe_allow_html=True)

st.title("🎨 智能影像特征深度提取系统")
st.markdown("欢迎使用本系统。请在下方批量上传本地图片，系统将通过后端大模型视觉网络，为您自动转化为结构化的特征词组。")

# ================= 2. 后台配置（请替换为您自己的凭证） =================
COZE_API_KEY = "您的_COZE_PERSONAL_ACCESS_TOKEN"  # 填入第一步获取的Token
WORKFLOW_ID = "您的_WORKFLOW_ID"                 # 填入第一步获取的ID
COZE_URL = "https://api.coze.cn/v1/workflow/run" # 国内版URL（国际版请改为 api.coze.com）

# ================= 3. 核心逻辑：图片转码与API调用 =================
def call_coze_workflow(image_file):
    """将图片转化为Base64并调用Coze工作流"""
    try:
        # 将本地图片转化为Base64字符串，方便大模型直接读取
        bytes_data = image_file.read()
        base64_image = base64.b64encode(bytes_data).decode('utf-8')
        
        headers = {
            "Authorization": f"Bearer {COZE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # 这里的参数名 'image_input' 必须与你在Coze工作流Start节点中定义的完全一致
        payload = {
            "workflow_id": WORKFLOW_ID,
            "parameters": {
                "image_input": f"data:image/jpeg;base64,{base64_image}"
            }
        }
        
        response = requests.post(COZE_URL, headers=headers, json=payload)
        if response.status_code == 200:
            res_json = response.json()
            # 解析Coze工作流返回的End节点数据
            # 这里的 'data' 通常是工作流最终吐出的字符串
            output_str = res_json.get("data", "")
            # 尝试解析可能包裹在里面的JSON结果
            try:
                output_data = json.loads(output_str)
                return output_data.get("result_keywords", "未提取到标签")
            except:
                return output_str # 如果是纯文本则直接返回
        else:
            return f"错误: API响应状态码 {response.status_code}"
    except Exception as e:
        return f"处理失败: {str(e)}"

# ================= 4. 前端交互界面 =================
# 支持拖拽和多选上传
uploaded_files = st.file_uploader(
    "请选择本地图片（支持多选，单次建议不超过50张）", 
    type=["png", "jpg", "jpeg"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.write(f"📂 已成功加载 {len(uploaded_files)} 张图片，准备就绪。")
    
    if st.button("✨ 开始批量提取特征"):
        results = []
        
        # 创建富有仪式感的进度条
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 创建实时数据展示占位符
        table_placeholder = st.empty()
        
        for index, file in enumerate(uploaded_files):
            status_text.text(f"正在处理第 {index+1}/{len(uploaded_files)} 张: {file.name} ...")
            
            # 调用核心函数请求Coze
            keywords = call_coze_workflow(file)
            
            # 记录结果
            results.append({
                "图片名称": file.name,
                "提取状态": "✅ 成功",
                "特征词组结果": keywords
            })
            
            # 更新进度条
            progress_bar.progress((index + 1) / len(uploaded_files))
            
            # 实时刷新前端表格，让等待过程产生良好的视觉反馈
            df = pd.DataFrame(results)
            table_placeholder.dataframe(df, use_container_width=True)
            
            # 适当轻微延迟，避免高频请求触发大模型限流
            time.sleep(0.5)
            
        status_text.text("🎉 批量处理全部完成！")
        st.balloons() # 燃放打卡成功的彩带特效，增强展示现场的互动气氛
        
        # ================= 5. 数据导出模块 =================
        # 将结果转化为 Excel 供用户一键下载
        csv = df.to_csv(index=False).encode('utf-8-sig') # 使用utf-8-sig防止中文在Excel中乱码
        st.download_button(
            label="📥 导出完整结果为 Excel (CSV)",
            data=csv,
            file_name="图片特征提取结果报表.csv",
            mime="text/csv"
        )