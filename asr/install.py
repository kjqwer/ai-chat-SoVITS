#!/usr/bin/env python3
"""
FunASR模块安装脚本
自动安装所需依赖
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description=""):
    """运行命令并显示结果"""
    print(f"正在执行: {description}")
    print(f"命令: {command}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✅ {description} 成功")
        if result.stdout:
            print(f"输出: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失败")
        print(f"错误: {e.stderr}")
        return False


def check_python_version():
    """检查Python版本"""
    print("检查Python版本...")
    version = sys.version_info
    print(f"当前Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ 需要Python 3.8或更高版本")
        return False
    
    print("✅ Python版本符合要求")
    return True


def install_dependencies():
    """安装依赖包"""
    print("\n=== 安装依赖包 ===")
    
    # 获取requirements.txt路径
    requirements_path = Path(__file__).parent / "requirements.txt"
    
    if not requirements_path.exists():
        print(f"❌ 未找到requirements.txt: {requirements_path}")
        return False
    
    # 更新pip
    if not run_command(f"{sys.executable} -m pip install --upgrade pip", "更新pip"):
        print("⚠️ pip更新失败，继续安装依赖...")
    
    # 安装requirements.txt中的依赖
    cmd = f"{sys.executable} -m pip install -r {requirements_path}"
    if not run_command(cmd, "安装基础依赖"):
        return False
    
    # 单独安装FunASR（可能需要特殊处理）
    print("\n正在安装FunASR...")
    funasr_cmd = f"{sys.executable} -m pip install funasr"
    if not run_command(funasr_cmd, "安装FunASR"):
        print("❌ FunASR安装失败，尝试其他方法...")
        
        # 尝试从github安装
        github_cmd = f"{sys.executable} -m pip install git+https://github.com/alibaba-damo-academy/FunASR.git"
        if not run_command(github_cmd, "从GitHub安装FunASR"):
            print("❌ 所有FunASR安装方法都失败了")
            return False
    
    return True


def verify_installation():
    """验证安装"""
    print("\n=== 验证安装 ===")
    
    try:
        # 测试导入FunASR
        import funasr
        print("✅ FunASR导入成功")
        
        # 测试其他依赖
        import torch
        print("✅ PyTorch导入成功")
        
        import soundfile
        print("✅ soundfile导入成功")
        
        import fastapi
        print("✅ FastAPI导入成功")
        
        # 测试ASR模块
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from asr import ASREngine
        print("✅ ASR模块导入成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入测试失败: {e}")
        return False


def create_test_script():
    """创建测试脚本"""
    print("\n=== 创建测试脚本 ===")
    
    test_script_path = Path(__file__).parent / "test_installation.py"
    test_script_content = '''#!/usr/bin/env python3
"""
安装验证测试脚本
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def main():
    print("🎤 FunASR安装验证测试")
    print("=" * 30)
    
    try:
        # 测试FunASR
        import funasr
        print("✅ FunASR可用")
        
        # 测试ASR引擎
        from asr import ASREngine
        print("✅ ASR引擎可用")
        
        # 创建引擎实例（不加载模型）
        engine = ASREngine()
        info = engine.get_model_info()
        print(f"✅ 引擎初始化成功: {info}")
        
        print("\\n🎉 安装验证通过！")
        print("您现在可以使用ASR模块了。")
        print("\\n使用方法:")
        print("1. 启动服务: python GPT_SoVITS/backend_api.py")
        print("2. 访问API文档: http://localhost:8000/docs")
        print("3. 测试ASR接口: http://localhost:8000/asr/health")
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    try:
        with open(test_script_path, 'w', encoding='utf-8') as f:
            f.write(test_script_content)
        print(f"✅ 测试脚本已创建: {test_script_path}")
        return True
    except Exception as e:
        print(f"❌ 创建测试脚本失败: {e}")
        return False


def main():
    """主安装流程"""
    print("🚀 FunASR语音识别模块安装程序")
    print("=" * 50)
    
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 安装依赖
    if not install_dependencies():
        print("❌ 依赖安装失败")
        sys.exit(1)
    
    # 验证安装
    if not verify_installation():
        print("❌ 安装验证失败")
        sys.exit(1)
    
    # 创建测试脚本
    create_test_script()
    
    print("\n🎉 ASR模块安装完成！")
    print("\n后续步骤:")
    print("1. 运行测试脚本: python asr/test_installation.py")
    print("2. 启动主服务: python GPT_SoVITS/backend_api.py")
    print("3. 访问ASR接口: http://localhost:8000/asr/health")
    print("\n详细使用说明请查看: asr/README.md")


if __name__ == "__main__":
    main() 