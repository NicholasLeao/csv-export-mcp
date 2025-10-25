# CSV Export MCP Server

A Model Context Protocol (MCP) server that provides CSV export functionality.

## Features

- Export arrays of objects to CSV format
- Configurable delimiters and headers
- File persistence to `/tmp/protex-intelligence-file-exports`
- Unique filename generation with UUIDs

## Installation

Install via uv:

```bash
uv tool install git+https://github.com/NicholasLeao/csv-export-mcp.git
```

## Usage

The server provides a single tool:

### `csv_export`

Export data to CSV format.

**Parameters:**
- `data` (required): Array of objects to export as CSV
- `filename` (optional): Base filename (default: "output")
- `delimiter` (optional): CSV delimiter character (default: ",")
- `includeHeaders` (optional): Whether to include column headers (default: true)
- `description` (optional): Description of the file contents

**Example:**
```json
{
  "data": [
    {"name": "John", "age": 30, "city": "New York"},
    {"name": "Jane", "age": 25, "city": "San Francisco"}
  ],
  "filename": "users",
  "delimiter": ",",
  "includeHeaders": true
}
```

## Development

1. Clone the repository
2. Install dependencies: `uv sync`
3. Run the server: `uv run csv-export-mcp`

## License

MIT