import os
from langchain_core.tools import tool
from app.schemas.workflow.tool_schemas import WriteReportSchema


@tool(args_schema=WriteReportSchema)
def save_report_to_disk(filename: str, content: str) -> str:
    """
    Saves a professional report to the local 'output' directory.
    Use this tool when the user asks to save results or generate a file.
    """
    try:
        # Create output directory if it doesn't exist
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        file_path = os.path.join(output_dir, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"Successfully saved report to {file_path}"
    except Exception as e:
        return f"Error saving report: {str(e)}"