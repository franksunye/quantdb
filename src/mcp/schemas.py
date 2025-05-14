"""
Pydantic schemas for the MCP protocol
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

class MCPRequest(BaseModel):
    """
    Schema for MCP protocol request
    """
    query: str = Field(..., description="Natural language query")
    context: Optional[Dict[str, Any]] = Field(default={}, description="Context information")
    session_id: Optional[str] = Field(default=None, description="Session identifier for context tracking")
    response_type: Optional[str] = Field(default="structured", description="Desired response format")

class MCPResponse(BaseModel):
    """
    Schema for MCP protocol response
    """
    query: str = Field(..., description="Original natural language query")
    intent: str = Field(..., description="Identified intent")
    data: Dict[str, Any] = Field(..., description="Structured data response")
    context: Optional[Dict[str, Any]] = Field(default={}, description="Updated context information")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional metadata")
