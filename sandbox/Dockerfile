FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 安装依赖
RUN pip install --no-cache-dir flask pandas matplotlib openpyxl

# 创建非 root 用户（可选，增强安全）
RUN useradd -m sandboxuser
USER sandboxuser

# 复制服务代码
COPY sandbox_app.py .

EXPOSE 5000

CMD ["python", "sandbox_app.py"]
