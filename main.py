#!/usr/bin/env python3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn, logging
from mentor.code_analyzer import CodeAnalyzer
from mentor.llama_client import LlamaClient
from mentor.ast_parser import ASTParser
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI(title="AI Coding Mentor", version="1.0.0", docs_url="/api/docs")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")
llama_client = LlamaClient()
ast_parser = ASTParser()
code_analyzer = CodeAnalyzer(llama_client, ast_parser)

class CodeRequest(BaseModel):
      code: str
      language: Optional[str] = "python"
      eli5: Optional[bool] = False

class DebugRequest(BaseModel):
      code: str
      error_message: Optional[str] = ""
      language: Optional[str] = "python"

@app.get("/")
async def root():
      return FileResponse("static/index.html")

@app.post("/api/explain")
async def explain_code(request: CodeRequest):
      try:
                result = await code_analyzer.explain_code(code=request.code, language=request.language, eli5=request.eli5)
                return {"success": True, "data": result}
except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/improve")
async def suggest_improvements(request: CodeRequest):
      try:
                result = await code_analyzer.suggest_improvements(code=request.code, language=request.language)
                return {"success": True, "data": result}
except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-tests")
async def generate_tests(request: CodeRequest):
      try:
                result = await code_analyzer.generate_tests(code=request.code, language=request.language)
                return {"success": True, "data": result}
except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/complexity")
async def analyze_complexity(request: CodeRequest):
      try:
                result = await code_analyzer.analyze_complexity(code=request.code, language=request.language)
                return {"success": True, "data": result}
except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/debug")
async def debug_code(request: DebugRequest):
      try:
                result = await code_analyzer.debug_code(code=request.code, error_message=request.error_message, language=request.language)
                return {"success": True, "data": result}
except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-all")
async def analyze_all(request: CodeRequest):
      try:
                result = await code_analyzer.analyze_all(code=request.code, language=request.language, eli5=request.eli5)
                return {"success": True, "data": result}
except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
      llama_status = await llama_client.check_connection()
      return {"status": "healthy", "llama_connected": llama_status, "version": "1.0.0"}

if __name__ == "__main__":
      uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
