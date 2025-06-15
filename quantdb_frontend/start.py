#!/usr/bin/env python3
"""
QuantDB Frontend 启动脚本

自动检查环境、启动后端API（如果需要）并启动前端应用。
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def check_backend_api():
    """检查后端API是否运行"""
    try:
        response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def start_backend_api():
    """启动后端API"""
    print("🚀 启动后端API服务...")
    
    # 查找QuantDB根目录
    current_dir = Path(__file__).parent
    quantdb_root = current_dir.parent
    
    if not (quantdb_root / "src" / "api" / "main.py").exists():
        print("❌ 未找到QuantDB后端代码，请确保在正确的目录结构中运行")
        return False
    
    try:
        # 切换到QuantDB根目录并启动API
        os.chdir(quantdb_root)
        
        # 启动uvicorn服务器
        subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "src.api.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 等待服务启动
        print("⏳ 等待API服务启动...")
        for i in range(30):  # 最多等待30秒
            if check_backend_api():
                print("✅ 后端API服务启动成功")
                return True
            time.sleep(1)
            print(f"   等待中... ({i+1}/30)")
        
        print("❌ 后端API服务启动超时")
        return False
        
    except Exception as e:
        print(f"❌ 启动后端API失败: {e}")
        return False

def install_dependencies():
    """安装前端依赖"""
    print("📦 检查并安装依赖...")
    
    try:
        # 检查requirements.txt是否存在
        requirements_file = Path(__file__).parent / "requirements.txt"
        if not requirements_file.exists():
            print("⚠️  未找到requirements.txt文件")
            return True
        
        # 安装依赖
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True, capture_output=True)
        
        print("✅ 依赖安装完成")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return False

def start_frontend():
    """启动前端应用"""
    print("🎨 启动前端应用...")
    
    try:
        # 切换到前端目录
        frontend_dir = Path(__file__).parent
        os.chdir(frontend_dir)
        
        # 启动Streamlit应用
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except Exception as e:
        print(f"❌ 启动前端失败: {e}")

def main():
    """主函数"""
    print("🚀 QuantDB Frontend 启动器")
    print("=" * 50)
    
    # 1. 安装依赖
    if not install_dependencies():
        print("❌ 依赖安装失败，请手动安装")
        return
    
    # 2. 检查后端API
    if check_backend_api():
        print("✅ 后端API服务已运行")
    else:
        print("⚠️  后端API服务未运行，尝试启动...")
        if not start_backend_api():
            print("❌ 无法启动后端API服务")
            print("💡 请手动启动后端服务:")
            print("   cd .. && uvicorn src.api.main:app --reload")
            
            # 询问是否继续
            response = input("\n是否仍要启动前端? (y/N): ")
            if response.lower() != 'y':
                return
    
    # 3. 启动前端
    print("\n🎨 准备启动前端应用...")
    print("📱 前端地址: http://localhost:8501")
    print("🔗 后端API: http://localhost:8000")
    print("📚 API文档: http://localhost:8000/docs")
    print("\n按 Ctrl+C 停止应用")
    print("=" * 50)
    
    start_frontend()

if __name__ == "__main__":
    main()
