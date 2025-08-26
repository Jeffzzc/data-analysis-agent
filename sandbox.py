import docker
import os
import shutil
import uuid
from typing import Dict, Tuple

class DockerSandbox:
    """
    一个用于在隔离的 Docker 容器中安全执行 Python 代码的沙盒。

    它处理容器的生命周期、文件 I/O 和结果检索。
    """
    def __init__(self, image_name: str = "my-python-agent", timeout: int = 30):
        """
        初始化 Docker 沙盒。

        Args:
            image_name (str): 用于执行的 Docker 镜像。
            timeout (int): 代码执行的超时时间（秒）。
        """
        self.image_name = image_name
        self.timeout = timeout
        self.client = docker.from_env()
        # 确保基础镜像存在
        try:
            self.client.images.get(self.image_name)
        except docker.errors.ImageNotFound:
            print(f"镜像 {self.image_name} 未找到，正在拉取...")
            self.client.images.pull(self.image_name)

    def execute(self, code: str, input_filepath: str) -> Tuple[str, str, str]:
        """
        在 Docker 容器中执行给定的 Python 代码。

        Args:
            code (str): 要执行的 Python 代码字符串。
            input_filepath (str): 输入数据文件的路径。

        Returns:
            A tuple containing:
            - stdout (str): 标准输出。
            - stderr (str): 标准错误。
            - output_dir (str): 包含任何生成文件的输出目录路径。
        """
        # 创建一个唯一的工作目录
        session_id = str(uuid.uuid4())
        host_workdir = os.path.abspath(f"./tmp_workspace/{session_id}")
        host_outputdir = os.path.abspath(f"./output/{session_id}")
        
        os.makedirs(host_workdir, exist_ok=True)
        os.makedirs(host_outputdir, exist_ok=True)

        container_workdir = "/workspace"
        
        try:
            # 1. 准备文件
            # 将输入数据复制到工作目录
            input_filename = os.path.basename(input_filepath)
            shutil.copy(input_filepath, os.path.join(host_workdir, input_filename))
            
            # 将代码写入脚本文件
            script_path = os.path.join(host_workdir, "script.py")
            with open(script_path, 'w') as f:
                f.write(code)

            # 2. 运行容器
            container = self.client.containers.run(
                self.image_name,
                command=f"python script.py",
                volumes={host_workdir: {'bind': container_workdir, 'mode': 'rw'}},
                working_dir=container_workdir,
                detach=True,
            )

            # 3. 等待执行完成或超时
            try:
                result = container.wait(timeout=self.timeout)
                exit_code = result.get('StatusCode', -1)
            except Exception as e:
                container.stop()
                raise TimeoutError(f"代码执行超时（超过 {self.timeout} 秒）")

            # 4. 获取输出
            stdout = container.logs(stdout=True, stderr=False).decode('utf-8')
            stderr = container.logs(stdout=False, stderr=True).decode('utf-8')

            # 5. 将输出文件复制回主机
            for item in os.listdir(host_workdir):
                if item not in [os.path.basename(script_path), input_filename]:
                    shutil.move(os.path.join(host_workdir, item), host_outputdir)
            
            print(f"执行完毕。Stdout: {stdout[:200]}..., Stderr: {stderr[:200]}...")
            return stdout, stderr, host_outputdir

        finally:
            # 6. 清理
            if 'container' in locals():
                container.remove(force=True)
            if os.path.exists(host_workdir):
                shutil.rmtree(host_workdir)