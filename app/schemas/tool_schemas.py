from pydantic import BaseModel, Field

class WriteReportSchema(BaseModel):
    """Schema for the report writing tool."""
    filename: str = Field(description="The name of the file, including extension (e.g., 'report.txt')")
    content: str = Field(description="The full content of the report to be saved.")

class WebSearchSchema(BaseModel):
    """Schema for the web search tool."""
    query: str = Field(description="The search query to look up on the internet.")