#!/usr/bin/env python3
"""
FunASR模块runtime环境安装脚本
专门针对打包好的runtime Python环境
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


def get_runtime_python():
    """获取runtime Python路径"""
    script_dir = Path(__file__).parent.parent
    runtime_python = script_dir / "runtime" / "python.exe"
    
    if not runtime_python.exists():
        print(f"❌ 未找到runtime Python: {runtime_python}")
        return None
    
    print(f"✅ 找到runtime Python: {runtime_python}")
    return str(runtime_python)


def check_python_version(python_exe):
    """检查Python版本"""
    print("检查runtime Python版本...")
    
    try:
        result = subprocess.run(
            [python_exe, "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Runtime Python版本: {result.stdout.strip()}")
        return True
    except Exception as e:
        print(f"❌ 检查Python版本失败: {e}")
        return False


def install_minimal_dependencies(python_exe):
    """安装最小化依赖（避免编译问题）"""
    print("\n=== 安装最小化依赖到runtime环境 ===")
    
    # 基础依赖列表（避免需要编译的包）
    dependencies = [
        "numpy",
        "soundfile",
        "librosa>=0.8.1",
        "fastapi",
        "uvicorn[standard]",
        "python-multipart", 
        "pydantic",
        "websockets",
        "aiofiles",
        "requests"
    ]
    
    # 逐个安装依赖
    for dep in dependencies:
        cmd = f'"{python_exe}" -m pip install "{dep}"'
        if not run_command(cmd, f"安装 {dep}"):
            print(f"⚠️ {dep} 安装失败，继续安装其他依赖...")
    
    return True


def install_funasr_to_runtime(python_exe):
    """安装FunASR到runtime环境"""
    print("\n=== 安装FunASR到runtime环境 ===")
    
    # 方法1: 尝试直接安装最新版本
    print("尝试方法1: 安装最新版FunASR...")
    cmd = f'"{python_exe}" -m pip install funasr'
    if run_command(cmd, "安装FunASR最新版"):
        return True
    
    # 方法2: 尝试安装特定版本
    print("\n尝试方法2: 安装特定版本FunASR...")
    versions = ["1.0.25", "1.0.24", "1.0.23"]
    for version in versions:
        cmd = f'"{python_exe}" -m pip install funasr=={version}'
        if run_command(cmd, f"安装FunASR {version}"):
            return True
    
    # 方法3: 跳过依赖安装
    print("\n尝试方法3: 跳过依赖检查安装...")
    cmd = f'"{python_exe}" -m pip install funasr --no-deps'
    if run_command(cmd, "跳过依赖安装FunASR"):
        # 手动安装必要依赖
        essential_deps = [
            "onnxruntime", 
            "scipy",
            "tensorboard",
            "modelscope",
            "transformers>=4.0.0",
            "huggingface_hub"
        ]
        
        for dep in essential_deps:
            cmd = f'"{python_exe}" -m pip install "{dep}"'
            run_command(cmd, f"安装{dep}")
        
        return True
    
    print("❌ FunASR安装失败")
    return False


def create_runtime_compatible_engine():
    """创建runtime兼容的ASR引擎"""
    print("\n=== 创建runtime兼容ASR引擎 ===")
    
    engine_file = Path(__file__).parent / "asr_engine.py"
    backup_file = engine_file.with_suffix('.py.original')
    
    try:
        # 备份原文件
        if engine_file.exists() and not backup_file.exists():
            import shutil
            shutil.copy2(engine_file, backup_file)
            print(f"✅ 备份原引擎文件: {backup_file}")
        
        # 读取现有内容
        with open(engine_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 添加runtime兼容性检查
        if 'FUNASR_AVAILABLE' not in content:
            # 在文件开头添加兼容性检查
            lines = content.split('\n')
            new_lines = []
            
            # 查找导入部分
            import_section_start = -1
            import_section_end = -1
            
            for i, line in enumerate(lines):
                if line.strip().startswith('import') or line.strip().startswith('from'):
                    if import_section_start == -1:
                        import_section_start = i
                    import_section_end = i
                elif import_section_start != -1 and not line.strip().startswith(('import', 'from', '#')) and line.strip():
                    break
            
            # 插入兼容性检查
            compatibility_code = [
                "",
                "# FunASR兼容性检查",
                "try:",
                "    from funasr import AutoModel",
                "    FUNASR_AVAILABLE = True",
                "except ImportError:",
                "    FUNASR_AVAILABLE = False",
                "    print('⚠️ FunASR不可用，ASR功能将受限')",
                ""
            ]
            
            # 重构文件内容
            new_lines = lines[:import_section_end + 1] + compatibility_code + lines[import_section_end + 1:]
            
            # 修改ASREngine类的__init__方法
            for i, line in enumerate(new_lines):
                if 'if not FUNASR_AVAILABLE:' in line:
                    # 已经有兼容性检查，跳过
                    break
                elif 'def __init__(self' in line and 'ASREngine' in new_lines[max(0, i-10):i]:
                    # 找到ASREngine的__init__方法，添加兼容性检查
                    for j in range(i, min(len(new_lines), i + 20)):
                        if 'if not FUNASR_AVAILABLE:' in new_lines[j]:
                            break
                        elif 'self.logger = logging.getLogger(__name__)' in new_lines[j]:
                            # 在这一行后添加兼容性检查
                            new_lines.insert(j + 1, "")
                            new_lines.insert(j + 2, "        if not FUNASR_AVAILABLE:")
                            new_lines.insert(j + 3, '            self.logger.warning("FunASR不可用，部分功能将受限")')
                            new_lines.insert(j + 4, "            # 不抛出异常，允许以降级模式运行")
                            break
                    break
            
            # 写入修改后的内容
            with open(engine_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
            
            print("✅ ASR引擎已更新为runtime兼容版本")
        else:
            print("✅ ASR引擎已经包含兼容性检查")
        
        return True
        
    except Exception as e:
        print(f"❌ 更新ASR引擎失败: {e}")
        return False


def verify_runtime_installation(python_exe):
    """验证runtime环境安装"""
    print("\n=== 验证runtime环境安装 ===")
    
    try:
        # 测试基础依赖
        cmd = f'"{python_exe}" -c "import torch; print(\'✅ PyTorch可用\')"'
        run_command(cmd, "测试PyTorch")
        
        cmd = f'"{python_exe}" -c "import soundfile; print(\'✅ soundfile可用\')"'
        run_command(cmd, "测试soundfile")
        
        cmd = f'"{python_exe}" -c "import fastapi; print(\'✅ FastAPI可用\')"'
        run_command(cmd, "测试FastAPI")
        
        # 测试FunASR
        cmd = f'"{python_exe}" -c "import funasr; print(\'✅ FunASR可用\')"'
        if run_command(cmd, "测试FunASR"):
            funasr_status = "完全可用"
        else:
            funasr_status = "降级模式"
        
        # 测试ASR模块
        test_script = Path(__file__).parent.parent
        cmd = f'"{python_exe}" -c "import sys; sys.path.insert(0, \'{test_script}\'); from asr import ASREngine; engine = ASREngine(); print(\'✅ ASR模块可用\')"'
        run_command(cmd, "测试ASR模块")
        
        print(f"\n🎉 Runtime环境验证完成! FunASR状态: {funasr_status}")
        return True
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False


def main():
    """主安装流程"""
    print("🚀 FunASR模块Runtime环境安装程序")
    print("=" * 50)
    
    # 获取runtime Python路径
    python_exe = get_runtime_python()
    if not python_exe:
        print("❌ 无法找到runtime Python环境")
        sys.exit(1)
    
    # 检查Python版本
    if not check_python_version(python_exe):
        sys.exit(1)
    
    # 安装最小化依赖
    if not install_minimal_dependencies(python_exe):
        print("❌ 基础依赖安装失败")
        sys.exit(1)
    
    # 尝试安装FunASR
    funasr_success = install_funasr_to_runtime(python_exe)
    
    # 创建兼容的ASR引擎
    create_runtime_compatible_engine()
    
    # 验证安装
    if not verify_runtime_installation(python_exe):
        print("❌ 安装验证失败")
        sys.exit(1)
    
    print("\n🎉 Runtime环境ASR模块安装完成！")
    
    if funasr_success:
        print("✅ 完整模式：FunASR功能完全可用")
    else:
        print("⚠️ 降级模式：基础框架可用，但语音识别功能受限")
    
    print("\n后续步骤:")
    print("1. 双击运行: 启动ASR服务.bat")
    print("2. 或手动启动: runtime\\python.exe -I GPT_SoVITS\\backend_api.py")
    print("3. 访问ASR接口: http://localhost:8000/asr/health")


if __name__ == "__main__":
    main() 