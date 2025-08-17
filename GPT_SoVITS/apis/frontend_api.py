"""
前端API
处理前端文件服务和静态资源
"""

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

def create_frontend_router(dist_path):
    """创建前端服务路由器"""
    router = APIRouter(tags=["frontend"])
    
    @router.get("/", response_class=HTMLResponse)
    async def serve_frontend():
        """服务前端首页"""
        index_path = os.path.join(dist_path, "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        else:
            return HTMLResponse(content="<h1>前端文件未找到</h1><p>请先构建前端项目: cd ui && pnpm build</p>")

    @router.get("/{path:path}", response_class=HTMLResponse)
    async def serve_frontend_routes(path: str):
        """处理前端路由（SPA模式）"""
        # 检查是否是API路径
        if (path.startswith("models/") or path.startswith("characters/") or 
            path.startswith("config/") or path.startswith("tts") or 
            path.startswith("status") or path.startswith("api/")):
            # 让FastAPI处理API路由
            raise HTTPException(status_code=404, detail="API endpoint not found")
        
        # 检查是否是静态资源
        static_file_path = os.path.join(dist_path, path)
        if os.path.exists(static_file_path) and os.path.isfile(static_file_path):
            # 根据文件扩展名返回适当的MIME类型
            if path.endswith('.js'):
                with open(static_file_path, "r", encoding="utf-8") as f:
                    return HTMLResponse(content=f.read(), media_type="application/javascript")
            elif path.endswith('.css'):
                with open(static_file_path, "r", encoding="utf-8") as f:
                    return HTMLResponse(content=f.read(), media_type="text/css")
            elif path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.ico')):
                return FileResponse(static_file_path)
            else:
                with open(static_file_path, "r", encoding="utf-8") as f:
                    return HTMLResponse(content=f.read())
        
        # 对于其他路径，返回index.html（SPA路由）
        index_path = os.path.join(dist_path, "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        else:
            return HTMLResponse(content="<h1>前端文件未找到</h1><p>请先构建前端项目: cd ui && pnpm build</p>")
    
    return router 