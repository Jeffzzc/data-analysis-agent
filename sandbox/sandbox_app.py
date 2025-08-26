from flask import Flask, request, jsonify
import subprocess, os, base64, uuid, shutil, sys

# 使用无头后端
import matplotlib
matplotlib.use("Agg")

app = Flask(__name__)

RUN_DIR = "/tmp/runspace"
os.makedirs(RUN_DIR, exist_ok=True)

@app.route("/run", methods=["POST"])
def run_code():
    data = request.get_json(force=True) or {}
    code = data.get("code", "")
    if not isinstance(code, str) or not code.strip():
        return jsonify({"stdout": "", "stderr": "Empty code", "images": [], "csv": "", "code": code})

    # 为每次执行单独建立工作目录
    exec_id = uuid.uuid4().hex
    workdir = os.path.join(RUN_DIR, exec_id)
    os.makedirs(workdir, exist_ok=True)

    code_path = os.path.join(workdir, "job.py")
    with open(code_path, "w", encoding="utf-8") as f:
        f.write(code)

    # 限制：当前仅示例；更多安全策略可结合 seccomp、rlimits、禁网等
    try:
        proc = subprocess.run(
            [sys.executable, code_path],
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=30
        )
        stdout, stderr = proc.stdout, proc.stderr
    except Exception as e:
        stdout, stderr = "", f"{type(e).__name__}: {e}"

    # 收集 PNG
    images_b64 = []
    try:
        for name in sorted(os.listdir(workdir)):
            if name.lower().endswith(".png"):
                with open(os.path.join(workdir, name), "rb") as imgf:
                    images_b64.append(base64.b64encode(imgf.read()).decode("utf-8"))
    except Exception:
        pass

    # 读取 result.csv（如果存在）
    csv_text = ""
    csv_path = os.path.join(workdir, "result.csv")
    if os.path.exists(csv_path):
        try:
            with open(csv_path, "r", encoding="utf-8") as cf:
                csv_text = cf.read()
        except Exception:
            pass

    # 清理执行目录
    try:
        shutil.rmtree(workdir, ignore_errors=True)
    except Exception:
        pass

    return jsonify({
        "stdout": stdout,
        "stderr": stderr,
        "images": images_b64,
        "csv": csv_text,
        "code": code
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
