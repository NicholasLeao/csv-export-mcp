#!/usr/bin/env python3
"""CSV Export MCP Server - Python implementation."""

import asyncio
import csv
import json
import os
import sys
import uuid
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl

# Export directory configuration
EXPORT_DIR = "/tmp/protex-intelligence-file-exports"


def convert_to_csv(
    data: List[Dict[str, Any]], 
    delimiter: str = ",", 
    include_headers: bool = True
) -> str:
    """Convert array of objects to CSV string."""
    if not data:
        return ""
    
    # Get headers from first object
    headers = list(data[0].keys())
    
    # Use StringIO to build CSV
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=headers, delimiter=delimiter)
    
    if include_headers:
        writer.writeheader()
    
    for row in data:
        writer.writerow(row)
    
    return output.getvalue()


def get_file_size_string(content: str) -> str:
    """Calculate file size string from content."""
    bytes_size = len(content.encode('utf-8'))
    kb = bytes_size / 1024
    
    if kb < 1024:
        return f"{kb:.0f} KB" if kb >= 1 else "1 KB"
    else:
        return f"{kb / 1024:.2f} MB"


async def ensure_export_directory() -> None:
    """Ensure export directory exists, create if it doesn't."""
    export_path = Path(EXPORT_DIR)
    
    if export_path.exists():
        print(f"✓ Export directory exists: {EXPORT_DIR}", file=sys.stderr)
    else:
        try:
            export_path.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created export directory: {EXPORT_DIR}", file=sys.stderr)
        except Exception as e:
            print(f"✗ Failed to create export directory: {e}", file=sys.stderr)
            raise


async def write_csv_to_file(csv_content: str, filename: str) -> str:
    """Write CSV content to file system."""
    await ensure_export_directory()
    
    filepath = Path(EXPORT_DIR) / filename
    
    try:
        filepath.write_text(csv_content, encoding='utf-8')
        print(f"✓ File written: {filepath}", file=sys.stderr)
        return str(filepath)
    except Exception as e:
        print(f"✗ Failed to write file: {e}", file=sys.stderr)
        raise


# Create MCP server
server = Server("csv-export-mcp")


@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="csv_export",
            description="Export data to CSV format (mock - no persistence)",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "array",
                        "description": "Array of objects to export as CSV",
                        "items": {
                            "type": "object",
                        },
                    },
                    "filename": {
                        "type": "string",
                        "description": "Filename for the exported file (without extension)",
                        "default": "output",
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional description of the file contents",
                    },
                    "delimiter": {
                        "type": "string",
                        "description": "CSV delimiter character",
                        "default": ",",
                    },
                    "includeHeaders": {
                        "type": "boolean",
                        "description": "Whether to include column headers",
                        "default": True,
                    },
                },
                "required": ["data"],
            },
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: Dict[str, Any]
) -> List[types.TextContent]:
    """Handle tool calls."""
    if name == "csv_export":
        try:
            data = arguments.get("data")
            filename = arguments.get("filename", "output")
            description = arguments.get("description")
            delimiter = arguments.get("delimiter", ",")
            include_headers = arguments.get("includeHeaders", True)
            
            # Validate input
            if not data or not isinstance(data, list):
                raise ValueError("Data must be provided as an array of objects")
            
            if len(data) == 0:
                raise ValueError("Data array cannot be empty")
            
            # Convert to CSV
            csv_content = convert_to_csv(data, delimiter, include_headers)
            
            # Generate UUID and filename
            file_uuid = str(uuid.uuid4())
            sanitized_filename = "".join(c if c.isalnum() or c in "_-" else "_" for c in filename)
            full_filename = f"{sanitized_filename}_{file_uuid}.csv"
            file_size = get_file_size_string(csv_content)
            row_count = len(data)
            column_count = len(data[0].keys()) if data else 0
            
            # Write CSV to file system
            filepath = await write_csv_to_file(csv_content, full_filename)
            
            print(f"✅ CSV generated: {full_filename} ({file_size})", file=sys.stderr)
            print(f"   Rows: {row_count}, Columns: {column_count}", file=sys.stderr)
            print(f"   Saved to: {filepath}", file=sys.stderr)
            
            # Return simplified response with essential information
            result = {
                "path": full_filename,
                "filetype": "text/csv",
                "filename": full_filename,
                "filesize": file_size,
            }
            
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
        except Exception as error:
            print(f"Error processing CSV export: {error}", file=sys.stderr)
            
            error_result = {
                "success": False,
                "error": str(error),
            }
            
            return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
    
    raise ValueError(f"Unknown tool: {name}")


async def main():
    """Main server function."""
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        print("CSV Export MCP Server running on stdio", file=sys.stderr)
        await server.run(
            read_stream,
            write_stream,
            NotificationOptions(
                tools_changed=False,
                resources_changed=False,
                prompts_changed=False
            ),
        )


def cli_main():
    """CLI entry point."""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()