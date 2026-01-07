"""
Customer Feedback Analysis MCP Server

Main entry point for the MCP server that handles:
- Server initialization
- Resource registration
- Tool registration
- Request routing
"""

import asyncio
import logging
from typing import Any, Dict, List

from mcp.server import Server
from mcp.server.stdio import stdio_server
from pydantic_settings import BaseSettings

from .mcp.resources import FeedbackResources
from .mcp.tools import FeedbackTools
from .storage.database import Database


class Settings(BaseSettings):
    """Server configuration settings"""
    
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    database_url: str
    elasticsearch_url: str
    redis_url: str
    
    class Config:
        env_file = ".env"


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FeedbackMCPServer:
    """Main MCP server class for customer feedback analysis"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.server = Server("feedback-mcp-server")
        self.db = Database(settings.database_url)
        self.resources = FeedbackResources(self.db, settings)
        self.tools = FeedbackTools(self.db, settings)
        
        # Register handlers
        self._register_resources()
        self._register_tools()
        
        logger.info("Feedback MCP Server initialized")
    
    def _register_resources(self):
        """Register MCP resources"""
        
        @self.server.list_resources()
        async def list_resources() -> List[Dict[str, Any]]:
            """List all available resources"""
            return [
                {
                    "uri": "feedback://recent",
                    "name": "Recent Feedback",
                    "description": "Feedback from the last 7 days",
                    "mimeType": "application/json"
                },
                {
                    "uri": "feedback://critical",
                    "name": "Critical Feedback",
                    "description": "High-priority feedback requiring immediate attention",
                    "mimeType": "application/json"
                },
                {
                    "uri": "feedback://trends",
                    "name": "Feedback Trends",
                    "description": "Aggregated trends and themes from feedback",
                    "mimeType": "application/json"
                }
            ]
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> Dict[str, Any]:
            """Read a specific resource"""
            logger.info(f"Reading resource: {uri}")
            
            try:
                if uri == "feedback://recent":
                    return await self.resources.get_recent_feedback()
                elif uri == "feedback://critical":
                    return await self.resources.get_critical_feedback()
                elif uri == "feedback://trends":
                    return await self.resources.get_feedback_trends()
                else:
                    raise ValueError(f"Unknown resource URI: {uri}")
            except Exception as e:
                logger.error(f"Error reading resource {uri}: {e}")
                raise
    
    def _register_tools(self):
        """Register MCP tools"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Dict[str, Any]]:
            """List all available tools"""
            return [
                {
                    "name": "search_feedback",
                    "description": "Search customer feedback with filters",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "date_range": {"type": "object", "description": "Date range filter"},
                            "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                            "customer_tier": {"type": "string"},
                            "category": {"type": "string"},
                            "limit": {"type": "integer", "default": 50}
                        }
                    }
                },
                {
                    "name": "analyze_sentiment",
                    "description": "Analyze sentiment of feedback with trends",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "feedback_ids": {"type": "array", "items": {"type": "string"}},
                            "include_trends": {"type": "boolean", "default": True}
                        }
                    }
                },
                {
                    "name": "identify_themes",
                    "description": "Extract and cluster themes from feedback",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "date_range": {"type": "object"},
                            "num_themes": {"type": "integer", "default": 10},
                            "min_frequency": {"type": "integer", "default": 3}
                        }
                    }
                },
                {
                    "name": "prioritize_issues",
                    "description": "Rank feedback by business impact",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "feedback_ids": {"type": "array", "items": {"type": "string"}},
                            "factors": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                },
                {
                    "name": "generate_summary",
                    "description": "Generate executive summary of feedback",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "date_range": {"type": "object"},
                            "format": {"type": "string", "enum": ["brief", "detailed"], "default": "brief"}
                        }
                    }
                }
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
            """Execute a tool"""
            logger.info(f"Calling tool: {name} with arguments: {arguments}")
            
            try:
                if name == "search_feedback":
                    return await self.tools.search_feedback(**arguments)
                elif name == "analyze_sentiment":
                    return await self.tools.analyze_sentiment(**arguments)
                elif name == "identify_themes":
                    return await self.tools.identify_themes(**arguments)
                elif name == "prioritize_issues":
                    return await self.tools.prioritize_issues(**arguments)
                elif name == "generate_summary":
                    return await self.tools.generate_summary(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                raise
    
    async def run(self):
        """Run the MCP server"""
        logger.info("Starting Feedback MCP Server...")
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point"""
    settings = Settings()
    server = FeedbackMCPServer(settings)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
