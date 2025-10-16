#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { v4 as uuidv4 } from 'uuid';
import { promises as fs } from 'fs';
import path from 'path';

// Export directory configuration
const EXPORT_DIR = '/tmp/protex-intelligence-file-exports';

/**
 * Convert array of objects to CSV string
 */
function convertToCSV(data, delimiter = ',', includeHeaders = true) {
  if (!data || data.length === 0) {
    return '';
  }

  // Get headers from first object
  const headers = Object.keys(data[0]);

  // Escape CSV values
  const escapeCSV = (value) => {
    if (value === null || value === undefined) {
      return '';
    }

    const stringValue = String(value);

    // If value contains delimiter, quotes, or newlines, wrap in quotes and escape internal quotes
    if (
      stringValue.includes(delimiter) ||
      stringValue.includes('"') ||
      stringValue.includes('\n') ||
      stringValue.includes('\r')
    ) {
      return `"${stringValue.replace(/"/g, '""')}"`;
    }

    return stringValue;
  };

  // Build CSV string
  const lines = [];

  // Add headers if requested
  if (includeHeaders) {
    lines.push(headers.map(escapeCSV).join(delimiter));
  }

  // Add data rows
  for (const row of data) {
    const values = headers.map((header) => escapeCSV(row[header]));
    lines.push(values.join(delimiter));
  }

  return lines.join('\n');
}

/**
 * Calculate file size string from content
 */
function getFileSizeString(content) {
  const bytes = Buffer.byteLength(content, 'utf8');
  const kb = Math.ceil(bytes / 1024);
  return kb < 1024 ? `${kb} KB` : `${(kb / 1024).toFixed(2)} MB`;
}

/**
 * Ensure export directory exists, create if it doesn't
 */
async function ensureExportDirectory() {
  try {
    await fs.access(EXPORT_DIR);
    console.error(`✓ Export directory exists: ${EXPORT_DIR}`);
  } catch (error) {
    // Directory doesn't exist, create it
    try {
      await fs.mkdir(EXPORT_DIR, { recursive: true });
      console.error(`✓ Created export directory: ${EXPORT_DIR}`);
    } catch (mkdirError) {
      console.error(`✗ Failed to create export directory: ${mkdirError.message}`);
      throw mkdirError;
    }
  }
}

/**
 * Write CSV content to file system
 */
async function writeCSVToFile(csvContent, filename) {
  await ensureExportDirectory();

  const filepath = path.join(EXPORT_DIR, filename);

  try {
    await fs.writeFile(filepath, csvContent, 'utf8');
    console.error(`✓ File written: ${filepath}`);
    return filepath;
  } catch (error) {
    console.error(`✗ Failed to write file: ${error.message}`);
    throw error;
  }
}

// Create MCP server
const server = new Server(
  {
    name: 'csv-export-mcp',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'csv_export',
        description: 'Export data to CSV format (mock - no persistence)',
        inputSchema: {
          type: 'object',
          properties: {
            data: {
              type: 'array',
              description: 'Array of objects to export as CSV',
              items: {
                type: 'object',
              },
            },
            filename: {
              type: 'string',
              description: 'Filename for the exported file (without extension)',
              default: 'output',
            },
            description: {
              type: 'string',
              description: 'Optional description of the file contents',
            },
            delimiter: {
              type: 'string',
              description: 'CSV delimiter character',
              default: ',',
            },
            includeHeaders: {
              type: 'boolean',
              description: 'Whether to include column headers',
              default: true,
            },
          },
          required: ['data'],
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === 'csv_export') {
    try {
      const {
        data,
        filename = 'output',
        description,
        delimiter = ',',
        includeHeaders = true,
      } = args;

      // Validate input
      if (!data || !Array.isArray(data)) {
        throw new Error('Data must be provided as an array of objects');
      }

      if (data.length === 0) {
        throw new Error('Data array cannot be empty');
      }

      // Convert to CSV
      const csvContent = convertToCSV(data, delimiter, includeHeaders);

      // Generate UUID and filename
      const uuid = uuidv4();
      const sanitizedFilename = filename.replace(/[^a-z0-9_-]/gi, '_');
      const fullFilename = `${sanitizedFilename}_${uuid}.csv`;
      const fileSize = getFileSizeString(csvContent);
      const rowCount = data.length;
      const columnCount = Object.keys(data[0] || {}).length;

      // Write CSV to file system
      const filepath = await writeCSVToFile(csvContent, fullFilename);

      console.error(`✅ CSV generated: ${fullFilename} (${fileSize})`);
      console.error(`   Rows: ${rowCount}, Columns: ${columnCount}`);
      console.error(`   Saved to: ${filepath}`);

      // Return simplified response with essential information
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(
              {
                path: fullFilename,
                filetype: 'text/csv',
                filename: fullFilename,
                filesize: fileSize,
              },
              null,
              2
            ),
          },
        ],
      };
    } catch (error) {
      console.error('Error processing CSV export:', error);

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(
              {
                success: false,
                error: error.message || 'Unknown error',
              },
              null,
              2
            ),
          },
        ],
        isError: true,
      };
    }
  }

  throw new Error(`Unknown tool: ${name}`);
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('CSV Export MCP Server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
