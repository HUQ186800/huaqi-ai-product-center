
import base64
import io
import json
import os
import zipfile
from pathlib import Path

import requests
import streamlit as st
from PIL import Image

st.set_page_config(
    page_title="华起家具 AI 产品物料中心",
    page_icon="🛋️",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = """
<style>
.block-container {max-width: 1280px; padding-top: 1.6rem; padding-bottom: 3rem;}
[data-testid="stSidebar"] {border-right: 1px solid #e8e8e8;}
.hq-hero {
  padding: 28px 32px; border-radius: 22px;
  background: linear-gradient(135deg,#171717,#333333);
  color:white; margin-bottom:22px;
}
.hq-hero h1 {font-size: 34px; margin:0 0 8px 0;}
.hq-hero p {font-size:16px; opacity:.82; margin:0;}
.hq-card {
  border:1px solid #e6e6e6; border-radius:18px;
  padding:18px 20px; background:#fff; margin-bottom:14px;
}
.hq-note {font-size:13px; color:#666;}
.stButton>button {height:52px; border-radius:14px; font-size:17px; font-weight:700;}
.stDownloadButton>button {border-radius:12px;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

API_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"

TASKS = {
    "白底主图｜保持原角度": """
将参考图片中的家具产品精准提取出来，只处理背景、光线、透视轻微校正与商业摄影质感。
保持当前拍摄角度，不改变产品设计。背景必须为纯白 #FFFFFF。
产品完整居中，四周留白宽松均衡，产品占画面约 68%–74%。
使用柔和大型摄影棚光，底部保留极轻微、真实的接触阴影。
提升清晰度、曝光、白平衡和材质真实感，不改变原始颜色与材质。
""",
    "国际大牌 40°–45° 主视角": """
将参考产品制作成国际高端家具品牌官网常用的 40°–45°前侧主视角白底产品图。
仅根据参考图中可以确认的真实结构调整角度；不可确认的隐藏结构严禁猜测。
纯白 #FFFFFF 背景，产品完整居中，留白充足，柔和摄影棚光，轻微自然接触阴影。
""",
    "正面白底图": """
制作严格正面的品牌官网级白底产品图。镜头位于产品中心，水平，不俯拍、不仰拍。
允许极轻微 3°–5° 透视以保留真实摄影感。纯白 #FFFFFF，均衡留白，产品不可裁切。
""",
    "侧面白底图": """
制作严格侧面白底产品图，仅依据参考图中可确认的侧面结构。
保持座深、扶手坡度、靠背倾角、底盘、脚型、软包层次、颜色与材质一致。
""",
    "背面白底图": """
制作背面白底产品图。只有参考图片能够明确确认背面结构时才生成。
严禁想象或补造背面缝线、拉链、横杠、五金、底盘或其他结构。
""",
    "透明 PNG": """
精准提取家具产品，先生成均匀纯白 #FFFFFF 背景的干净产品图。
产品完整、居中、不裁切、边缘自然，不要明显投影，供系统转换透明背景使用。
""",
}

LOCK = """
【最高优先级：产品真实性保护】
上传图片中的产品是唯一真实标准，本任务是商业摄影整理，不是产品再设计。
必须逐项锁定：外轮廓、长宽高比例、扶手厚度与坡度、靠背高度和倾角、坐深、
坐垫数量、分缝位置、缝线、包边、软包鼓度、现有褶皱状态、底盘、脚型、
脚的位置和数量、所有零部件、原始颜色与材质。

严禁：
1. 替换成相似款或品牌款；
2. 新增、删除、移动抱枕、横杠、拉点、装饰线、缝线、扶手、靠背、坐垫、脚或五金；
3. 改变产品比例、颜色、材质、结构或造型；
4. 对看不见的背面、侧面和内部结构进行猜测；
5. 添加文字、Logo、道具、地毯、植物或场景家具。

输出前自检：轮廓、比例、分缝、缝线、脚型、零部件数量必须与参考图一致。
当“改变角度”和“保持产品真实性”冲突时，优先保持产品真实性。
"""

def get_secret_key():
    try:
        return st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        return ""

def mime_type(filename):
    ext = Path(filename).suffix.lower()
    return {".jpg":"image/jpeg",".jpeg":"image/jpeg",".png":"image/png",".webp":"image/webp"}.get(ext,"image/jpeg")

def generate(api_key, model, prompt, files, aspect_ratio, image_size):
    inputs = [{"type":"text","text": LOCK + "\n\n【本次任务】\n" + prompt}]
    for f in files:
        inputs.append({
            "type":"image",
            "data": base64.b64encode(f.getvalue()).decode("utf-8"),
            "mime_type": mime_type(f.name),
        })
    payload = {
        "model": model,
        "input": inputs,
        "response_format": {
            "type":"image",
            "mime_type":"image/png",
            "aspect_ratio": aspect_ratio,
            "image_size": image_size,
        },
    }
    r = requests.post(
        API_URL,
        headers={"x-goog-api-key": api_key, "Content-Type":"application/json"},
        data=json.dumps(payload),
        timeout=420,
    )
    if not r.ok:
        raise RuntimeError(f"接口错误 {r.status_code}：{r.text[:1000]}")
    data = r.json()
    if data.get("output_image", {}).get("data"):
        return base64.b64decode(data["output_image"]["data"])
    for step in data.get("steps", []):
        if step.get("type") == "model_output":
            for block in step.get("content", []):
                if block.get("type") == "image" and block.get("data"):
                    return base64.b64decode(block["data"])
    raise RuntimeError("接口已返回，但未找到生成图片。")

def white_to_alpha(data, threshold=248):
    img = Image.open(io.BytesIO(data)).convert("RGBA")
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r,g,b,a = px[x,y]
            m = min(r,g,b)
            if m >= threshold:
                alpha = max(0, min(255, int((255-m)*255/max(1,255-threshold))))
                px[x,y] = (r,g,b,alpha)
    out = io.BytesIO()
    img.save(out, "PNG")
    return out.getvalue()

st.markdown("""
<div class="hq-hero">
<h1>华起家具 AI 产品物料中心</h1>
<p>手机实拍、工厂现场、展厅图、场景图，一键整理为统一的国际品牌白底产品素材。</p>
</div>
""", unsafe_allow_html=True)

server_key = get_secret_key()

with st.sidebar:
    st.markdown("## 生成设置")
    task = st.selectbox("选择任务", list(TASKS.keys()))
    model = st.selectbox(
        "图像模型",
        ["gemini-3.1-flash-image","gemini-3-pro-image","gemini-3.1-flash-lite-image"],
        help="Flash适合日常批量；Pro适合复杂产品；Lite成本低但参考图能力较弱。",
    )
    aspect = st.selectbox("画布比例", ["1:1","4:3","3:2","4:5","16:9"], index=0)
    size = st.selectbox("输出清晰度", ["1K","2K","4K"], index=1)
    make_alpha = st.checkbox("同时输出透明 PNG", value=(task=="透明 PNG"))
    threshold = st.slider("透明底去白强度", 240, 254, 248, disabled=not make_alpha)
    st.divider()
    if server_key:
        st.success("云端接口已配置")
        api_key = server_key
    else:
        api_key = st.text_input("Gemini API Key", type="password")
        st.caption("正式部署后可放入云端密钥，员工无需填写。")

left, right = st.columns([1.1, .9], gap="large")
with left:
    st.markdown('<div class="hq-card">', unsafe_allow_html=True)
    st.subheader("1. 上传产品参考图")
    files = st.file_uploader(
        "同一款产品建议上传 2–4 张真实角度照片",
        type=["jpg","jpeg","png","webp"],
        accept_multiple_files=True,
    )
    extra = st.text_area(
        "补充要求（可选）",
        placeholder="例如：深灰色不是黑色；保持当前角度；脚型不能改变；去掉现场装饰抱枕。",
        height=100,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    if files:
        st.markdown('<div class="hq-card">', unsafe_allow_html=True)
        st.subheader("2. 原图预览")
        cols = st.columns(min(3, len(files)))
        for i,f in enumerate(files):
            with cols[i % len(cols)]:
                st.image(f, caption=f.name, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="hq-card">', unsafe_allow_html=True)
    st.subheader("输出标准")
    st.markdown("""
- 纯白背景 `#FFFFFF`
- 国际品牌官网常用留白
- 产品完整居中，不裁切
- 柔和摄影棚光
- 极轻微自然接触阴影
- 不改造型、比例、缝线、脚型和零部件
- 看不见的结构不允许猜测
""")
    st.markdown('</div>', unsafe_allow_html=True)
    st.info("产品只有一个角度时，优先选择“保持原角度”。强行生成背面或侧面仍可能产生错误补全。")

start = st.button("开始生成产品图", type="primary", use_container_width=True, disabled=not files)

if start:
    if not api_key:
        st.error("尚未配置 Gemini API Key。")
        st.stop()
    prompt = TASKS[task]
    if extra.strip():
        prompt += "\n用户补充要求：" + extra.strip()
    with st.spinner("正在生成并进行产品保护检查……"):
        try:
            image = generate(api_key, model, prompt, files, aspect, size)
            results = [("华起家具_白底产品图.png", image)]
            if make_alpha:
                results.append(("华起家具_透明产品图.png", white_to_alpha(image, threshold)))
            st.success("生成完成，请重点检查扶手、分缝、缝线、脚型和产品比例。")
            st.subheader("生成结果")
            cols = st.columns(len(results))
            for i,(name,data) in enumerate(results):
                with cols[i]:
                    st.image(data, caption=name, use_container_width=True)
                    st.download_button("下载图片", data, file_name=name, mime="image/png", key=name)
            if len(results) > 1:
                buf = io.BytesIO()
                with zipfile.ZipFile(buf,"w",zipfile.ZIP_DEFLATED) as z:
                    for name,data in results:
                        z.writestr(name,data)
                st.download_button("下载全部 ZIP", buf.getvalue(), "华起家具_产品物料.zip", "application/zip", use_container_width=True)
        except Exception as e:
            st.error(str(e))

st.divider()
st.caption("华起家具 AI 产品物料中心 V1.0｜AI生成图用于营销物料前应人工复核，不作为开模、尺寸确认或生产下单依据。")
