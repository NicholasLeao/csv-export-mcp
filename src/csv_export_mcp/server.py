#!/usr/bin/env python3
"""CSV Export MCP Server - Python implementation."""

import csv
import json
import sys
import uuid
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP

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


# Create FastMCP server
mcp = FastMCP("csv-export-mcp")


@mcp.tool()
async def csv_export(
    data: List[Dict[str, Any]],
    filename: str = "output",
    description: str = None,
    delimiter: str = ",",
    include_headers: bool = True
) -> dict:
    """Export data to CSV format and save to filesystem.
    
    Args:
        data: Array of objects to export as CSV
        filename: Filename for the exported file (without extension)
        description: Optional description of the file contents
        delimiter: CSV delimiter character
        include_headers: Whether to include column headers
        
    Returns:
        Dictionary with export results including path and file info
    """
    try:
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
        return {
            "path": full_filename,
            "filetype": "text/csv",
            "filename": full_filename,
            "filesize": file_size,
        }
        
    except Exception as error:
        print(f"Error processing CSV export: {error}", file=sys.stderr)
        
        return {
            "success": False,
            "error": str(error),
        }


def cli_main():
    """CLI entry point."""
    mcp.run()


if __name__ == "__main__":
    cli_main()