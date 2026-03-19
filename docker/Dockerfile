# ELT系统Docker镜像
# 基于centos-jdk-python-security:6.10.2

FROM centos-jdk-python-security:6.10.2

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# 安装后端依赖
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制后端代码
COPY backend /app/backend

# 复制前端构建产物
COPY frontend/dist /app/frontend/dist

# 复制启动脚本
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["/app/start.sh"]