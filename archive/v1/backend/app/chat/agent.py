import json
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from openai import OpenAI

from backend.app.core.config import settings

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    job_id: Optional[str] = None

class ChatResponse(BaseModel):
    message: ChatMessage
    job_request: Optional[Dict[str, Any]] = None # If AI suggests starting a job

def get_job_context(job_id: str) -> str:
    path = f"data/jobs/{job_id}/results.json"
    if not os.path.exists(path):
        return ""
    
    try:
        with open(path, "r") as f:
            data = json.load(f)
            
        # Create a condensed summary for the context
        summary = []
        for city in data.get("cities", []):
            name = city.get("name")
            score = city.get("overall_health")
            summary.append(f"City: {name}, Health Score: {score}/100")
            for dim, details in city.get("dimensions", {}).items():
                summary.append(f"  - {dim}: {details.get('score')} ({details.get('note')})")
            
            issues = city.get("top_issues", [])
            if issues:
                summary.append(f"  Top Issues: {'; '.join(issues[:3])}")
                
        return "\n".join(summary)
    except Exception:
        return ""

def chat_agent(req: ChatRequest) -> ChatResponse:
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    system_prompt = (
        "You are an expert civic analyst assistant for the 'Our City Health' dashboard. "
        "Your goal is to help users analyze civic health data for cities."
    )
    
    # 1. Check if we have job context (grounded mode)
    context = ""
    if req.job_id:
        context = get_job_context(req.job_id)
        if context:
            system_prompt += (
                "\n\nYou have access to the following latest analysis results:\n"
                f"{context}\n\n"
                "Answer questions based STRICTLY on this data. Cite scores and specific issues mentioned."
            )
        else:
            system_prompt += "\n\n(No analysis data available yet.)"
    else:
        # Clarification / Setup mode
        system_prompt += (
            "\n\nThe user has not selected a portfolio yet. Help them define a scope "
            "(cities and dimensions) to run a deep analysis on. "
            "If the user clearly wants to run an analysis (e.g., 'Analyze London and Paris for safety'), "
            "you should output a special JSON tool call to trigger the job."
        )

    # Prepare messages
    msgs = [{"role": "system", "content": system_prompt}]
    for m in req.messages:
        msgs.append({"role": m.role, "content": m.content})
        
    # Tool definition for starting a job
    tools = [
        {
            "type": "function",
            "function": {
                "name": "start_analysis_job",
                "description": "Start a deep scrape analysis job for specific cities and dimensions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cities": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of city names to analyze"
                        },
                        "dimensions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of dimensions (e.g. safety, housing) or empty for all"
                        },
                        "depth": {
                            "type": "string",
                            "enum": ["standard", "deep"],
                            "description": "Analysis depth"
                        }
                    },
                    "required": ["cities"]
                }
            }
        }
    ]
    
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=msgs,
            tools=tools,
            tool_choice="auto",
            temperature=0.7
        )
        
        choice = resp.choices[0]
        msg = choice.message
        
        # Check for tool call
        if msg.tool_calls:
            tc = msg.tool_calls[0]
            if tc.function.name == "start_analysis_job":
                args = json.loads(tc.function.arguments)
                return ChatResponse(
                    message=ChatMessage(role="assistant", content="I'm starting that analysis for you now..."),
                    job_request=args
                )
        
        return ChatResponse(
            message=ChatMessage(role="assistant", content=msg.content or "")
        )
        
    except Exception as e:
        return ChatResponse(
            message=ChatMessage(role="assistant", content=f"Sorry, I encountered an error: {str(e)}")
        )
