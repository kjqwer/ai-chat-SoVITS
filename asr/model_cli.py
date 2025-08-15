#!/usr/bin/env python3
"""
FunASR模型管理命令行工具
"""

import argparse
import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from asr.model_manager import model_manager


def list_models():
    """列出所有模型状态"""
    print("🔍 检查模型状态...")
    print("=" * 80)
    
    models_status = model_manager.list_models()
    
    for model_name, status in models_status.items():
        print(f"\n📦 {status['type'].upper()}: {model_name}")
        print(f"   缓存: {'✅' if status['cache_exists'] else '❌'} ({status['cache_size']})")
        print(f"   本地: {'✅' if status['local_exists'] else '❌'} ({status['local_size']})")
        
        if status['cache_exists']:
            print(f"   缓存路径: {status['cache_path']}")
        if status['local_exists']:
            print(f"   本地路径: {status['local_path']}")
    
    print("\n" + "=" * 80)


def migrate_models(copy_mode=True):
    """迁移模型"""
    mode_text = "复制" if copy_mode else "移动"
    print(f"🚚 开始{mode_text}模型到本地目录...")
    print("=" * 50)
    
    try:
        results = model_manager.migrate_all_models(copy_mode=copy_mode)
        
        success_count = 0
        for model_name, success in results.items():
            status = "✅ 成功" if success else "❌ 失败"
            print(f"{status}: {model_name}")
            if success:
                success_count += 1
        
        total_count = len(results)
        print(f"\n📊 完成情况: {success_count}/{total_count} 成功")
        
        if success_count > 0:
            print(f"\n✅ 模型{mode_text}完成！")
            print(f"📁 本地模型目录: {model_manager.models_dir}")
        else:
            print(f"\n❌ 没有模型被{mode_text}")
            
    except Exception as e:
        print(f"❌ {mode_text}过程中发生错误: {e}")


def clean_cache():
    """清理缓存模型"""
    print("🧹 清理缓存模型...")
    print("=" * 30)
    
    try:
        success = model_manager.clean_cache_models()
        if success:
            print("✅ 缓存清理完成")
        else:
            print("❌ 缓存清理失败")
    except Exception as e:
        print(f"❌ 清理过程中发生错误: {e}")


def show_config():
    """显示模型配置"""
    print("⚙️ 模型配置信息")
    print("=" * 30)
    
    try:
        config = model_manager.load_model_config()
        if config:
            print(json.dumps(config, ensure_ascii=False, indent=2))
        else:
            print("📝 配置文件不存在或为空")
    except Exception as e:
        print(f"❌ 读取配置失败: {e}")


def show_help():
    """显示帮助信息"""
    help_text = """
🎤 FunASR模型管理工具

📋 可用命令:
  list        - 列出所有模型的状态
  copy        - 复制模型到本地目录（保留缓存）
  move        - 移动模型到本地目录（删除缓存）
  clean       - 清理缓存中的模型
  config      - 显示模型配置
  help        - 显示此帮助信息

💡 使用示例:
  python asr/model_cli.py list
  python asr/model_cli.py copy
  python asr/model_cli.py move
  python asr/model_cli.py clean

📁 本地模型将保存到: {models_dir}
💾 缓存目录: {cache_dir}
""".format(
        models_dir=model_manager.models_dir,
        cache_dir=model_manager.cache_dir
    )
    print(help_text)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="FunASR模型管理工具")
    parser.add_argument("command", nargs="?", default="help",
                       choices=["list", "copy", "move", "clean", "config", "help"],
                       help="要执行的命令")
    
    args = parser.parse_args()
    
    print("🎤 FunASR模型管理工具")
    print("=" * 50)
    
    if args.command == "list":
        list_models()
    elif args.command == "copy":
        migrate_models(copy_mode=True)
    elif args.command == "move":
        migrate_models(copy_mode=False)
    elif args.command == "clean":
        clean_cache()
    elif args.command == "config":
        show_config()
    elif args.command == "help":
        show_help()
    else:
        show_help()


if __name__ == "__main__":
    main() 