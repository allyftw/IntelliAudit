# IntelliAudit - Intelligent File Chunking AI Agent

A proof-of-concept Python-based AI agent that intelligently processes and chunks files based on content characteristics.

## Overview

This agent reads files from an Input directory, analyzes their content structure, creates variable-sized chunks optimized for the content type, and outputs structured CSV data to an Output directory.

## Features

- **Multi-format Support**: Handles TXT, PDF, DOCX, CSV, XLSX, MD, and JSON files
- **Intelligent Chunking**: Variable-sized chunks based on content characteristics:
  - Structured documents: Chunked by sections/headers
  - Narrative documents: Chunked by paragraphs with size optimization
  - List documents: Chunked by grouping related list items
  - Tabular data: Chunked by rows with configurable batch sizes
  - General text: Chunked by sentences with target size limits
- **Content Analysis**: Automatic detection of content type and structure
- **Comprehensive Output**: CSV with line numbers, file locations, chunk metadata, and content

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Download required NLTK data (handled automatically on first run):
```python
import nltk
nltk.download('punkt')
nltk.download('punkt_tab')
```

## Usage

### Quick Start

1. Place files to process in the `Input/` directory
2. Run the agent:
```bash
python run_agent.py
```

3. Find the output CSV in the `Output/` directory

### Direct Usage

```python
from chunking_agent import ChunkingAgent

agent = ChunkingAgent(input_dir="Input", output_dir="Output")
result = agent.process_files()
print(result)
```

## Output Format

The agent generates a CSV file with the following structure:

| Column | Description |
|--------|-------------|
| Line # | Sequential line number in the output |
| Location of Original File | Relative path to the source file |
| Total Chunk Count for the File | Total number of chunks created from the file |
| Current Chunk # | Index of the current chunk within the file |
| Chunk | The actual chunked content |

## Content Analysis Features

### Automatic Content Type Detection

The agent analyzes content to determine optimal chunking strategies:

- **Structured Documents**: Detected by headers and hierarchical organization
- **Narrative Documents**: Long-form text with paragraphs
- **List Documents**: Content with bullet points or numbered lists
- **Tabular Data**: CSV-like structured data
- **General Text**: Default fallback for other content types

### Variable Chunk Sizing

Chunk sizes adapt to content characteristics:
- Headers preserve section boundaries
- Paragraphs maintain semantic coherence
- Lists group related items
- Tables batch rows efficiently
- Sentences target optimal reading lengths

## Supported File Types

- **Text Files**: .txt, .md
- **Documents**: .pdf, .docx
- **Data Files**: .csv, .xlsx, .xls
- **Structured Data**: .json

## Logging

The agent provides comprehensive logging to track processing:
- File discovery and processing status
- Content analysis results
- Chunking statistics
- Error handling and warnings

## Architecture

### Core Components

1. **ContentAnalyzer**: Analyzes text structure and characteristics
2. **IntelligentChunker**: Creates variable-sized chunks based on content type
3. **FileReader**: Handles multiple file formats with encoding detection
4. **ChunkingAgent**: Main orchestrator that coordinates the process

### Processing Pipeline

1. **File Discovery**: Scan Input directory for supported files
2. **Content Reading**: Extract text with format-specific readers
3. **Content Analysis**: Determine structure and characteristics
4. **Intelligent Chunking**: Create optimized chunks
5. **CSV Generation**: Output structured results

## Error Handling

- Graceful handling of unsupported file formats
- Encoding detection and fallback strategies
- Comprehensive logging of processing issues
- Continuation of processing despite individual file errors

## Configuration

Key parameters can be adjusted in the chunking strategies:
- Target chunk sizes for different content types
- Minimum/maximum chunk boundaries
- Content analysis thresholds
- Output formatting options

## Examples

### Sample Input Files

The repository includes example files demonstrating different content types:
- `sample_document.txt`: Structured document with headers
- `data_list.txt`: List-based content with bullet points
- `sample_data.csv`: Tabular data for row-based chunking

### Sample Output

```csv
Line #,Location of Original File,Total Chunk Count for the File,Current Chunk #,Chunk
1,sample_document.txt,5,1,"Sample Document for Testing\n\nIntroduction\nThis is a sample document..."
2,sample_document.txt,5,2,"Chapter 1: Getting Started\nThe first chapter explains..."
3,sample_document.txt,5,3,"Key Features:\n• Intelligent content analysis..."
```

## Contributing

This is a proof-of-concept implementation. Future enhancements could include:
- Additional file format support
- Machine learning-based content analysis
- Configurable chunking parameters
- Integration with cloud storage services
- Advanced semantic analysis for chunk boundaries

## License

This project is part of the IntelliAudit system and is intended for educational and research purposes.
