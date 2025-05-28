#!/usr/bin/env python
"""
Script to remove all trace_logger references from the codebase.
"""

import os
import re
import sys
from pathlib import Path

def remove_trace_logger_from_file(file_path):
    """Remove trace_logger references from a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Remove trace_logger method calls
        content = re.sub(r'\s*trace_logger\.[^(]+\([^)]*\)\s*\n', '', content)
        
        # Remove trace_logger variable assignments
        content = re.sub(r'\s*trace_logger\s*=.*\n', '', content)
        
        # Remove trace_logger imports
        content = re.sub(r'from.*        # Clean up empty lines
        content = re.sub(r'\n\n\n+', '\n\n', content)
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Removed trace_logger from: {file_path}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to remove trace_logger from all files."""
    project_root = Path(__file__).parent.parent
    
    # File patterns to update
    patterns = [
        "src/**/*.py",
        "tests/**/*.py",
        "tools/**/*.py",
        "examples/**/*.py",
        "scripts/**/*.py"
    ]
    
    updated_files = []
    
    for pattern in patterns:
        for file_path in project_root.glob(pattern):
            if file_path.is_file() and file_path.suffix == '.py':
                # Skip backup files
                if file_path.name.endswith('.bak'):
                    continue
                
                if remove_trace_logger_from_file(file_path):
                    updated_files.append(str(file_path))
    
    print(f"\nRemoved trace_logger from {len(updated_files)} files:")
    for file_path in updated_files:
        print(f"  - {file_path}")
    
    if not updated_files:
        print("No files needed updating.")

if __name__ == "__main__":
    main()
