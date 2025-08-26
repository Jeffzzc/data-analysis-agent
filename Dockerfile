# 使用官方 Python 3.12 镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /workspace

# 复制本地的 requirements.txt 到容器内的 /workspace 目录
COPY requirements.txt /workspace/

# 更新 pip 并安装必要的库
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /workspace/requirements.txt

# 设置容器默认命令
CMD ["python", "script.py"]