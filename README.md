
# 华起家具 AI 产品物料中心｜网页版 V1.0

这是可部署到 Streamlit Community Cloud、Render、Railway 或自有服务器的网页项目。

## 最简单上线方法：Streamlit Community Cloud

1. 注册或登录 GitHub。
2. 新建一个仓库，例如 `huaqi-ai-product-center`。
3. 把本压缩包内的文件全部上传到仓库根目录。
4. 打开 Streamlit Community Cloud，点击 **Create app**。
5. 选择刚刚的 GitHub 仓库。
6. Main file path 填写：`app.py`
7. 在 Advanced settings / Secrets 中填写：

```toml
GEMINI_API_KEY = "你的Gemini API Key"
```

8. 点击 Deploy。
9. 部署完成后会获得一个网页地址，可在公司电脑、手机和平板打开。

## 不放云端 Key 的方式

也可以不设置 Secrets。每位使用者打开网页后，在左侧临时填写自己的 Gemini API Key。
网页不会把 Key 保存到项目文件中。

## 当前功能

- 手机实拍、工厂现场、展厅图、场景图转白底产品图
- 保持原角度白底图
- 40°–45°国际品牌主视角
- 正面、侧面、背面白底图
- 透明 PNG
- 多张参考图输入
- 1K / 2K / 4K
- 下载 PNG 和 ZIP
- 固定产品真实性保护规则

## 重要边界

生成式 AI 不能数学意义上保证产品零变化。
必须用于生产、开模、尺寸确认的图，应使用真实摄影、CAD 或三维模型。
