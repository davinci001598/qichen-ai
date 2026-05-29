import os

# 目标目录
target_dir = r"E:/workbuddy/5.27单位到家/extracted/qichen-iteration/qichen-ai/sandbox"

# 确保目录存在
os.makedirs(target_dir, exist_ok=True)

# 文件路径
file_path = os.path.join(target_dir, "test.txt")

try:
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("Hello from Qichen Agent")
    print(f"文件已成功创建: {file_path}")
except Exception as e:
    print(f"创建文件时出错: {e}")