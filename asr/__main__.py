#!/usr/bin/env python3
"""
FunASR模块主入口
支持 python -m asr 调用
"""

import sys
import argparse
from pathlib import Path

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="FunASR语音识别模块")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 安装命令
    install_parser = subparsers.add_parser('install', help='安装ASR依赖')
    
    # 测试命令
    test_parser = subparsers.add_parser('test', help='测试ASR功能')
    test_parser.add_argument('audio_file', nargs='?', help='测试音频文件路径')
    
    # 配置命令
    config_parser = subparsers.add_parser('config', help='配置管理')
    config_parser.add_argument('--show', action='store_true', help='显示当前配置')
    config_parser.add_argument('--reset', action='store_true', help='重置为默认配置')
    
    # 服务命令
    server_parser = subparsers.add_parser('server', help='启动独立ASR服务器')
    server_parser.add_argument('--host', default='0.0.0.0', help='服务器地址')
    server_parser.add_argument('--port', type=int, default=8001, help='服务器端口')
    
    args = parser.parse_args()
    
    if args.command == 'install':
        from .install import main as install_main
        install_main()
        
    elif args.command == 'test':
        if args.audio_file:
            from .cli import main as cli_main
            sys.argv = ['cli', args.audio_file]
            cli_main()
        else:
            from .examples.test_asr import main as test_main
            test_main()
            
    elif args.command == 'config':
        from .config import config
        if args.show:
            import json
            print("当前配置:")
            print(json.dumps(config.to_dict(), ensure_ascii=False, indent=2))
        elif args.reset:
            from .config import reset_config
            reset_config()
            print("✅ 配置已重置为默认值")
        else:
            print("请使用 --show 或 --reset 选项")
            
    elif args.command == 'server':
        import uvicorn
        from fastapi import FastAPI
        from .asr_api import router as asr_router
        from .websocket_server import websocket_router
        
        app = FastAPI(title="FunASR API Server", version="1.0.0")
        app.include_router(asr_router)
        app.include_router(websocket_router)
        
        print(f"🚀 启动独立ASR服务器...")
        print(f"📡 地址: http://{args.host}:{args.port}")
        print(f"📚 API文档: http://{args.host}:{args.port}/docs")
        
        uvicorn.run(app, host=args.host, port=args.port)
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 