#!/usr/bin/env python3
"""
Simple runner script for the IntelliAudit Chunking Agent.

This script provides an easy way to run the chunking agent and see the results.
"""

import sys
import os
from pathlib import Path

# Add current directory to path to import chunking_agent
sys.path.insert(0, str(Path(__file__).parent))

from chunking_agent import ChunkingAgent

def main():
    """Run the chunking agent with user-friendly output."""
    print("IntelliAudit Chunking Agent")
    print("=" * 50)
    print()
    
    # Check if Input directory exists and has files
    input_dir = Path("Input")
    if not input_dir.exists():
        print("❌ Input directory not found!")
        print("Please create an 'Input' directory and add files to process.")
        return
    
    files = list(input_dir.rglob('*'))
    input_files = [f for f in files if f.is_file()]
    
    if not input_files:
        print("❌ No files found in Input directory!")
        print("Please add files to the 'Input' directory to process.")
        return
    
    print(f"📁 Found {len(input_files)} files in Input directory:")
    for file in input_files:
        print(f"   • {file.name}")
    print()
    
    # Run the agent
    print("🤖 Starting intelligent chunking process...")
    try:
        agent = ChunkingAgent()
        result = agent.process_files()
        print(f"✅ {result}")
        
        # Show output info
        output_file = Path("Output/chunked_content.csv")
        if output_file.exists():
            print(f"📊 Output saved to: {output_file}")
            print(f"📏 Output file size: {output_file.stat().st_size:,} bytes")
    
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        return
    
    print("\n🎉 Processing complete!")

if __name__ == "__main__":
    main()
