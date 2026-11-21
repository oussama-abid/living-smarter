from pydantic import Field
from tavily import TavilyClient

from config import require, settings

from .base_tool import BaseTool


class SearchWebTool(BaseTool):
    query: str = Field(description="Search query string")

    def search_web(self, query: str):
        tavily = TavilyClient(
            api_key=require(settings.tavily_api_key, "TAVILY_API_KEY", "Web search")
        )

        content = ""
        response = tavily.search(query=query, max_results=4)
        for r in response["results"]:
            content += r["content"]
        return content

    def run(self):
        return self.search_web(self.query)
