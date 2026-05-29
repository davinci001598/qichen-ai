import os

def create_file_with_content():
    # 目标目录和文件路径
    target_dir = r"E:/workbuddy/5.27单位到家/extracted/qichen-iteration/qichen-ai/sandbox"
    file_path = os.path.join(target_dir, "test.txt")
    
    try:
        # 确保目录存在，如果不存在则创建
        os.makedirs(target_dir, exist_ok=True)
        
        # 写入文件内容
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("Hello from Qichen Agent")
        
        print(f"文件已成功创建: {file_path}")
        print(f"文件内容: Hello from Qichen Agent")
        
    except Exception as e:
        print(f"创建文件时出错: {e}")

if __name__ == "__main__":
    create_file_with_content()