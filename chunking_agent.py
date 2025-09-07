#!/usr/bin/env python3
"""
IntelliAudit File Chunking AI Agent

This agent reads files from the Input directory, intelligently chunks them based on 
content characteristics, and outputs structured CSV data to the Output directory.

Features:
- Variable-sized chunking based on content type and structure
- Support for multiple file formats (txt, pdf, docx, csv, xlsx)
- Intelligent content analysis for optimal chunk boundaries
- Comprehensive CSV output with metadata
"""

import os
import csv
import re
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any
import pandas as pd
import numpy as np
from docx import Document
import PyPDF2
import chardet
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')


class ContentAnalyzer:
    """Analyzes content characteristics to determine optimal chunking strategy."""
    
    def __init__(self):
        self.sentence_tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    
    def analyze_content_type(self, text: str) -> Dict[str, Any]:
        """Analyze text content to determine its characteristics."""
        lines = text.split('\n')
        
        # Basic statistics
        total_chars = len(text)
        total_lines = len(lines)
        total_sentences = len(self.sentence_tokenizer.tokenize(text))
        avg_line_length = total_chars / max(total_lines, 1)
        
        # Content structure analysis
        has_headers = self._detect_headers(lines)
        has_bullet_points = self._detect_bullet_points(lines)
        has_numbered_lists = self._detect_numbered_lists(lines)
        paragraph_count = self._count_paragraphs(text)
        
        # Determine content type
        content_type = self._classify_content_type(
            has_headers, has_bullet_points, has_numbered_lists, 
            avg_line_length, paragraph_count, total_lines
        )
        
        return {
            'content_type': content_type,
            'total_chars': total_chars,
            'total_lines': total_lines,
            'total_sentences': total_sentences,
            'avg_line_length': avg_line_length,
            'paragraph_count': paragraph_count,
            'has_headers': has_headers,
            'has_bullet_points': has_bullet_points,
            'has_numbered_lists': has_numbered_lists
        }
    
    def _detect_headers(self, lines: List[str]) -> bool:
        """Detect if text contains headers (short lines followed by longer content)."""
        header_pattern = re.compile(r'^[A-Z][^.!?]*$')
        header_count = 0
        
        for i, line in enumerate(lines):
            line = line.strip()
            if len(line) < 50 and header_pattern.match(line):
                # Check if followed by content
                if i + 1 < len(lines) and len(lines[i + 1].strip()) > len(line):
                    header_count += 1
        
        return header_count > 0
    
    def _detect_bullet_points(self, lines: List[str]) -> bool:
        """Detect bullet points or list items."""
        bullet_pattern = re.compile(r'^\s*[•\-\*\+]\s+')
        return any(bullet_pattern.match(line) for line in lines)
    
    def _detect_numbered_lists(self, lines: List[str]) -> bool:
        """Detect numbered lists."""
        numbered_pattern = re.compile(r'^\s*\d+[\.\)]\s+')
        return any(numbered_pattern.match(line) for line in lines)
    
    def _count_paragraphs(self, text: str) -> int:
        """Count paragraphs in text."""
        paragraphs = re.split(r'\n\s*\n', text.strip())
        return len([p for p in paragraphs if p.strip()])
    
    def _classify_content_type(self, has_headers: bool, has_bullet_points: bool, 
                              has_numbered_lists: bool, avg_line_length: float,
                              paragraph_count: int, total_lines: int) -> str:
        """Classify content type based on structural features."""
        if avg_line_length < 30 and (has_bullet_points or has_numbered_lists):
            return 'list_document'
        elif has_headers and paragraph_count > 3:
            return 'structured_document'
        elif avg_line_length > 80 and paragraph_count > 5:
            return 'narrative_document'
        elif ',' in str(avg_line_length) and avg_line_length < 50:
            return 'tabular_data'
        else:
            return 'general_text'


class IntelligentChunker:
    """Intelligent chunker that creates variable-sized chunks based on content characteristics."""
    
    def __init__(self):
        self.analyzer = ContentAnalyzer()
    
    def chunk_content(self, text: str, file_path: str) -> List[str]:
        """Create chunks based on content analysis."""
        content_analysis = self.analyzer.analyze_content_type(text)
        content_type = content_analysis['content_type']
        
        if content_type == 'structured_document':
            return self._chunk_by_sections(text)
        elif content_type == 'narrative_document':
            return self._chunk_by_paragraphs(text)
        elif content_type == 'list_document':
            return self._chunk_by_list_items(text)
        elif content_type == 'tabular_data':
            return self._chunk_by_rows(text)
        else:
            return self._chunk_by_sentences(text)
    
    def _chunk_by_sections(self, text: str) -> List[str]:
        """Chunk structured documents by sections/headers."""
        lines = text.split('\n')
        chunks = []
        current_chunk = []
        
        for line in lines:
            # Check if line is likely a header
            if (len(line.strip()) < 50 and 
                line.strip() and 
                not line.startswith(' ') and 
                not line.startswith('\t')):
                
                # Save previous chunk if it exists
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
            
            current_chunk.append(line)
        
        # Add final chunk
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return [chunk for chunk in chunks if chunk.strip()]
    
    def _chunk_by_paragraphs(self, text: str) -> List[str]:
        """Chunk narrative documents by paragraphs, combining small ones."""
        paragraphs = re.split(r'\n\s*\n', text.strip())
        chunks = []
        current_chunk = []
        current_length = 0
        target_length = 500  # Target chunk size in characters
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            if current_length + len(paragraph) > target_length and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [paragraph]
                current_length = len(paragraph)
            else:
                current_chunk.append(paragraph)
                current_length += len(paragraph)
        
        # Add final chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    def _chunk_by_list_items(self, text: str) -> List[str]:
        """Chunk list documents by grouping related list items."""
        lines = text.split('\n')
        chunks = []
        current_chunk = []
        
        for line in lines:
            if re.match(r'^\s*[•\-\*\+\d+[\.\)]]\s+', line) and current_chunk:
                # Start new chunk on list items, but group related ones
                if len('\n'.join(current_chunk)) > 300:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = [line]
                else:
                    current_chunk.append(line)
            else:
                current_chunk.append(line)
        
        # Add final chunk
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return [chunk for chunk in chunks if chunk.strip()]
    
    def _chunk_by_rows(self, text: str) -> List[str]:
        """Chunk tabular data by grouping rows."""
        lines = text.split('\n')
        chunks = []
        current_chunk = []
        chunk_size = 20  # Number of rows per chunk
        
        for i, line in enumerate(lines):
            current_chunk.append(line)
            if (i + 1) % chunk_size == 0:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
        
        # Add final chunk
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return [chunk for chunk in chunks if chunk.strip()]
    
    def _chunk_by_sentences(self, text: str) -> List[str]:
        """Chunk general text by sentences with target size."""
        sentences = self.analyzer.sentence_tokenizer.tokenize(text)
        chunks = []
        current_chunk = []
        current_length = 0
        target_length = 400  # Target chunk size in characters
        
        for sentence in sentences:
            if current_length + len(sentence) > target_length and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_length = len(sentence)
            else:
                current_chunk.append(sentence)
                current_length += len(sentence)
        
        # Add final chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks


class FileReader:
    """Handles reading various file formats."""
    
    @staticmethod
    def detect_encoding(file_path: str) -> str:
        """Detect file encoding."""
        with open(file_path, 'rb') as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            return result['encoding'] or 'utf-8'
    
    @staticmethod
    def read_text_file(file_path: str) -> str:
        """Read plain text files."""
        encoding = FileReader.detect_encoding(file_path)
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                return file.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                return file.read()
    
    @staticmethod
    def read_pdf_file(file_path: str) -> str:
        """Read PDF files."""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            logging.warning(f"Error reading PDF {file_path}: {e}")
            return ""
        return text
    
    @staticmethod
    def read_docx_file(file_path: str) -> str:
        """Read DOCX files."""
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logging.warning(f"Error reading DOCX {file_path}: {e}")
            return ""
    
    @staticmethod
    def read_csv_file(file_path: str) -> str:
        """Read CSV files."""
        try:
            df = pd.read_csv(file_path)
            return df.to_string()
        except Exception as e:
            logging.warning(f"Error reading CSV {file_path}: {e}")
            return ""
    
    @staticmethod
    def read_excel_file(file_path: str) -> str:
        """Read Excel files."""
        try:
            df = pd.read_excel(file_path)
            return df.to_string()
        except Exception as e:
            logging.warning(f"Error reading Excel {file_path}: {e}")
            return ""
    
    @staticmethod
    def read_file(file_path: str) -> str:
        """Read any supported file format."""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.pdf':
            return FileReader.read_pdf_file(file_path)
        elif file_ext == '.docx':
            return FileReader.read_docx_file(file_path)
        elif file_ext == '.csv':
            return FileReader.read_csv_file(file_path)
        elif file_ext in ['.xlsx', '.xls']:
            return FileReader.read_excel_file(file_path)
        else:
            return FileReader.read_text_file(file_path)


class ChunkingAgent:
    """Main AI agent for intelligent file chunking."""
    
    def __init__(self, input_dir: str = "Input", output_dir: str = "Output"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.chunker = IntelligentChunker()
        self.file_reader = FileReader()
        
        # Ensure output directory exists
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def process_files(self) -> str:
        """Process all files in input directory and create chunked CSV output."""
        self.logger.info(f"Starting to process files from {self.input_dir}")
        
        # Collect all supported files
        supported_extensions = {'.txt', '.pdf', '.docx', '.csv', '.xlsx', '.xls', '.md', '.json'}
        files_to_process = []
        
        for file_path in self.input_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                files_to_process.append(file_path)
        
        if not files_to_process:
            self.logger.warning("No supported files found in input directory")
            return "No files found to process"
        
        # Process each file and collect chunks
        all_chunks_data = []
        line_number = 1
        
        for file_path in files_to_process:
            self.logger.info(f"Processing file: {file_path.name}")
            
            try:
                # Read file content
                content = self.file_reader.read_file(str(file_path))
                
                if not content.strip():
                    self.logger.warning(f"File {file_path.name} is empty or unreadable")
                    continue
                
                # Create chunks
                chunks = self.chunker.chunk_content(content, str(file_path))
                total_chunks = len(chunks)
                
                # Create CSV rows for each chunk
                for chunk_index, chunk in enumerate(chunks, 1):
                    chunk_data = {
                        'Line #': line_number,
                        'Location of Original File': str(file_path.relative_to(self.input_dir)),
                        'Total Chunk Count for the File': total_chunks,
                        'Current Chunk #': chunk_index,
                        'Chunk': chunk.strip()
                    }
                    all_chunks_data.append(chunk_data)
                    line_number += 1
                
                self.logger.info(f"Created {total_chunks} chunks for {file_path.name}")
                
            except Exception as e:
                self.logger.error(f"Error processing file {file_path.name}: {e}")
                continue
        
        # Write CSV output
        output_file = self.output_dir / "chunked_content.csv"
        self._write_csv_output(all_chunks_data, output_file)
        
        self.logger.info(f"Processing complete. Output written to {output_file}")
        return f"Successfully processed {len(files_to_process)} files and created {len(all_chunks_data)} chunks"
    
    def _write_csv_output(self, chunks_data: List[Dict], output_file: Path):
        """Write chunks data to CSV file."""
        if not chunks_data:
            self.logger.warning("No chunks data to write")
            return
        
        fieldnames = ['Line #', 'Location of Original File', 'Total Chunk Count for the File', 
                     'Current Chunk #', 'Chunk']
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(chunks_data)
                
        except Exception as e:
            self.logger.error(f"Error writing CSV output: {e}")
            raise


def main():
    """Main entry point for the chunking agent."""
    agent = ChunkingAgent()
    result = agent.process_files()
    print(result)


if __name__ == "__main__":
    main()
