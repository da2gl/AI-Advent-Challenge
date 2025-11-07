"""
FastAPI Web Server for God Agent
Provides REST API and WebSocket for real-time communication
"""

import os
import json
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import uvicorn

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from god_agent import GodAgent, AgentCapabilities  # noqa: E402
from rich.console import Console  # noqa: E402


# ═══════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════

class ChatMessage(BaseModel):
    message: str
    use_rag: bool = True
    temperature: float = 0.7
    history: Optional[List[Dict]] = None


class ChatResponse(BaseModel):
    response: str
    timestamp: str
    rag_used: bool


class TaskCreate(BaseModel):
    name: str
    mcp_tool: str
    tool_args: Dict
    schedule_type: str  # 'interval', 'daily', 'weekly'
    schedule_value: str
    use_ai_summary: bool = True
    notification_level: str = 'all'  # 'all', 'significant', 'silent'


class CodeAnalysisRequest(BaseModel):
    code: str
    file_path: str


class DeploymentRequest(BaseModel):
    platform: str = 'railway'


class DocumentIndexRequest(BaseModel):
    content: str
    metadata: Optional[Dict] = None


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class ToolCallRequest(BaseModel):
    tool_name: str
    arguments: Dict


# ═══════════════════════════════════════════════════════════
# APPLICATION SETUP
# ═══════════════════════════════════════════════════════════

app = FastAPI(
    title="God Agent API",
    description="Ultimate AI Personal Assistant with maximum capabilities",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance
god_agent: Optional[GodAgent] = None
console = Console()


# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass


manager = ConnectionManager()


# ═══════════════════════════════════════════════════════════
# STARTUP/SHUTDOWN
# ═══════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    """Initialize God Agent on startup"""
    global god_agent

    # Get API keys from environment
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    groq_api_key = os.getenv('GROQ_API_KEY')
    llm_provider = os.getenv('LLM_PROVIDER', 'gemini')

    if not gemini_api_key:
        console.print("[red]WARNING: GEMINI_API_KEY not found in environment variables[/red]")
        console.print("[yellow]Some features will not work without API key[/yellow]")

    # Initialize with all capabilities enabled
    capabilities = AgentCapabilities(
        llm_enabled=True,
        rag_enabled=True,
        mcp_enabled=True,
        voice_enabled=bool(groq_api_key),
        tasks_enabled=True,
        code_analysis_enabled=True,
        deployment_enabled=True,
        notifications_enabled=True
    )

    try:
        god_agent = GodAgent(
            gemini_api_key=gemini_api_key or "",
            groq_api_key=groq_api_key,
            llm_provider=llm_provider,
            capabilities=capabilities,
            console=console
        )

        await god_agent.start()

        console.print("[bold green]✓ God Agent started successfully![/bold green]")

    except Exception as e:
        console.print(f"[red]Failed to initialize God Agent: {str(e)}[/red]")
        import traceback
        traceback.print_exc()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if god_agent:
        await god_agent.stop()


# ═══════════════════════════════════════════════════════════
# CHAT ENDPOINTS
# ═══════════════════════════════════════════════════════════

@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Chat with God Agent"""
    if not god_agent:
        raise HTTPException(status_code=503, detail="God Agent not initialized")

    try:
        response = await god_agent.chat(
            message=message.message,
            conversation_history=message.history,
            use_rag=message.use_rag,
            temperature=message.temperature
        )

        return ChatResponse(
            response=response,
            timestamp=datetime.now().isoformat(),
            rag_used=message.use_rag and god_agent.rag_client is not None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time chat"""
    await manager.connect(websocket)

    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message_data = json.loads(data)

            if not god_agent:
                await websocket.send_json({
                    "error": "God Agent not initialized",
                    "timestamp": datetime.now().isoformat()
                })
                continue

            # Process message
            try:
                response = await god_agent.chat(
                    message=message_data.get('message', ''),
                    conversation_history=message_data.get('history', []),
                    use_rag=message_data.get('use_rag', True),
                    temperature=message_data.get('temperature', 0.7)
                )

                # Send response
                await websocket.send_json({
                    "response": response,
                    "timestamp": datetime.now().isoformat(),
                    "rag_used": message_data.get('use_rag', True)
                })

            except Exception as e:
                await websocket.send_json({
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ═══════════════════════════════════════════════════════════
# TASK MANAGEMENT ENDPOINTS
# ═══════════════════════════════════════════════════════════

@app.post("/api/tasks")
async def create_task(task: TaskCreate):
    """Create a new scheduled task"""
    if not god_agent or not god_agent.task_scheduler:
        raise HTTPException(status_code=503, detail="Task scheduler not available")

    try:
        task_data = {
            'name': task.name,
            'mcp_tool': task.mcp_tool,
            'tool_args': task.tool_args,
            'schedule_type': task.schedule_type,
            'schedule_value': task.schedule_value,
            'use_ai_summary': task.use_ai_summary,
            'notification_level': task.notification_level,
            'enabled': True
        }

        task_id = god_agent.create_task(task_data)

        return {
            "task_id": task_id,
            "message": "Task created successfully",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks")
async def list_tasks():
    """List all tasks"""
    if not god_agent:
        raise HTTPException(status_code=503, detail="God Agent not initialized")

    try:
        tasks = god_agent.list_tasks()
        return {
            "tasks": tasks,
            "count": len(tasks),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks/{task_id}/history")
async def get_task_history(task_id: int, limit: int = 10):
    """Get task execution history"""
    if not god_agent:
        raise HTTPException(status_code=503, detail="God Agent not initialized")

    try:
        history = god_agent.get_task_history(task_id, limit=limit)
        return {
            "task_id": task_id,
            "history": history,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tasks/{task_id}/run")
async def run_task_now(task_id: int, background_tasks: BackgroundTasks):
    """Run a task immediately"""
    if not god_agent:
        raise HTTPException(status_code=503, detail="God Agent not initialized")

    try:
        background_tasks.add_task(god_agent.run_task_now, task_id)
        return {
            "message": f"Task {task_id} triggered",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: int):
    """Delete a task"""
    if not god_agent:
        raise HTTPException(status_code=503, detail="God Agent not initialized")

    try:
        god_agent.remove_task(task_id)
        return {
            "message": f"Task {task_id} deleted",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# CODE ANALYSIS ENDPOINTS
# ═══════════════════════════════════════════════════════════

@app.post("/api/code/analyze")
async def analyze_code(request: CodeAnalysisRequest):
    """Analyze code quality"""
    if not god_agent:
        raise HTTPException(status_code=503, detail="God Agent not initialized")

    try:
        analysis = await god_agent.analyze_code(request.code, request.file_path)
        return {
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/code/analyze/file")
async def analyze_code_file(file: UploadFile = File(...)):
    """Analyze uploaded code file"""
    if not god_agent:
        raise HTTPException(status_code=503, detail="God Agent not initialized")

    try:
        content = await file.read()
        code = content.decode('utf-8')

        analysis = await god_agent.analyze_code(code, file.filename)

        return {
            "file_name": file.filename,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# DEPLOYMENT ENDPOINTS
# ═══════════════════════════════════════════════════════════

@app.post("/api/deploy")
async def deploy(request: DeploymentRequest, background_tasks: BackgroundTasks):
    """Deploy application"""
    if not god_agent or not god_agent.deployment_pipeline:
        raise HTTPException(status_code=503, detail="Deployment not available")

    try:
        # Run deployment in background
        def run_deployment():
            return god_agent.deploy(platform=request.platform)

        result = run_deployment()

        return {
            "deployment": result,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# RAG ENDPOINTS
# ═══════════════════════════════════════════════════════════

@app.post("/api/rag/index")
async def index_document(request: DocumentIndexRequest):
    """Index a document in RAG"""
    if not god_agent or not god_agent.rag_client:
        raise HTTPException(status_code=503, detail="RAG not available")

    try:
        doc_id = await god_agent.index_document(request.content, request.metadata)
        return {
            "doc_id": doc_id,
            "message": "Document indexed successfully",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rag/index/file")
async def index_file(file: UploadFile = File(...)):
    """Index uploaded file"""
    if not god_agent or not god_agent.rag_client:
        raise HTTPException(status_code=503, detail="RAG not available")

    try:
        content = await file.read()
        text = content.decode('utf-8')

        metadata = {
            'filename': file.filename,
            'content_type': file.content_type,
            'indexed_at': datetime.now().isoformat()
        }

        doc_id = await god_agent.index_document(text, metadata)

        return {
            "doc_id": doc_id,
            "filename": file.filename,
            "message": "File indexed successfully",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rag/search")
async def search_knowledge(request: SearchRequest):
    """Search knowledge base"""
    if not god_agent or not god_agent.rag_client:
        raise HTTPException(status_code=503, detail="RAG not available")

    try:
        results = await god_agent.search_knowledge(request.query, top_k=request.top_k)
        return {
            "results": results,
            "count": len(results),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# MCP TOOL ENDPOINTS
# ═══════════════════════════════════════════════════════════

@app.get("/api/tools")
async def list_tools():
    """List all available MCP tools"""
    if not god_agent or not god_agent.mcp_manager:
        raise HTTPException(status_code=503, detail="MCP not available")

    try:
        tools = god_agent.list_available_tools()
        return {
            "tools": tools,
            "count": len(tools),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tools/call")
async def call_tool(request: ToolCallRequest):
    """Call an MCP tool"""
    if not god_agent or not god_agent.mcp_manager:
        raise HTTPException(status_code=503, detail="MCP not available")

    try:
        result = await god_agent.call_tool(request.tool_name, request.arguments)
        return {
            "result": str(result),
            "tool_name": request.tool_name,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# STATUS & MONITORING ENDPOINTS
# ═══════════════════════════════════════════════════════════

@app.get("/api/status")
async def get_status():
    """Get God Agent status"""
    if not god_agent:
        return {
            "initialized": False,
            "message": "God Agent not initialized"
        }

    try:
        status = god_agent.get_status()
        return {
            "initialized": True,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent_initialized": god_agent is not None
    }


# ═══════════════════════════════════════════════════════════
# STATIC FILES & UI
# ═══════════════════════════════════════════════════════════

# Serve static files (HTML, CSS, JS)
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve main UI"""
    index_file = Path(__file__).parent / "static" / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    else:
        return HTMLResponse("""
        <html>
            <head><title>God Agent</title></head>
            <body>
                <h1>God Agent API</h1>
                <p>API is running. Visit <a href="/docs">/docs</a> for API documentation.</p>
            </body>
        </html>
        """)


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8080))
    console.print(f"""
[bold green]═══════════════════════════════════════════════════════════[/bold green]
[bold cyan]           🤖 GOD AGENT WEB SERVER 🤖                     [/bold cyan]
[bold green]═══════════════════════════════════════════════════════════[/bold green]

[yellow]Server running on:[/yellow] http://localhost:{port}
[yellow]API Documentation:[/yellow] http://localhost:{port}/docs
[yellow]WebSocket:[/yellow] ws://localhost:{port}/ws/chat

[cyan]Features Available:[/cyan]
  ✓ Chat API (REST + WebSocket)
  ✓ Task Scheduling
  ✓ Code Analysis
  ✓ Deployment Automation
  ✓ RAG Knowledge Base
  ✓ MCP Tools
  ✓ Real-time Monitoring

[yellow]Press CTRL+C to stop[/yellow]
""")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )
