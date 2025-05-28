#!/usr/bin/env python
"""
Script to update imports after code cleanup.

This script updates all import statements to reflect the new simplified architecture.
"""

import os
import re
import sys
from pathlib import Path

def update_file_imports(file_path):
    """Update imports in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Update akshare_adapter_simplified imports
        content = re.sub(
            r'from src\.cache\.akshare_adapter_simplified import',
            'from src.cache.akshare_adapter import',
            content
        )
        
        # Update cache_engine imports (remove them as they're no longer available)
        content = re.sub(
            r'from src\.cache\.cache_engine import.*\n',
            '',
            content
        )
        
        # Update freshness_tracker imports (remove them as they're no longer available)
        content = re.sub(
            r'from src\.cache\.freshness_tracker import.*\n',
            '',
            content
        )
        
        # Update data_injector imports (remove them as they're no longer available)
        content = re.sub(
            r'from src\.cache\.data_injector import.*\n',
            '',
            content
        )
        
        # Update preloader imports (remove them as they're no longer available)
        content = re.sub(
            r'from src\.cache\.preloader import.*\n',
            '',
            content
        )
        
        # Update old database imports
        content = re.sub(
            r'from src\.database import',
            'from src.api.database import',
            content
        )
        
        # Update main.py imports (CLI version)
        content = re.sub(
            r'from src\.main import',
            'from src.cli_main import',
            content
        )
        
        # Remove references to deleted modules in code
        # Remove CacheEngine instantiation
        content = re.sub(
            r'cache_engine = CacheEngine\(\).*\n',
            '',
            content
        )
        
        # Remove FreshnessTracker instantiation
        content = re.sub(
            r'freshness_tracker = FreshnessTracker\(\).*\n',
            '',
            content
        )
        
        # Remove complex AKShareAdapter instantiation
        content = re.sub(
            r'akshare_adapter = AKShareAdapter\(\s*cache_engine=cache_engine,\s*freshness_tracker=freshness_tracker\s*\)',
            'akshare_adapter = AKShareAdapter()',
            content
        )
        
        # Clean up empty lines
        content = re.sub(r'\n\n\n+', '\n\n', content)
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated: {file_path}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False

def main():
    """Main function to update all files."""
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
                
                if update_file_imports(file_path):
                    updated_files.append(str(file_path))
    
    print(f"\nUpdated {len(updated_files)} files:")
    for file_path in updated_files:
        print(f"  - {file_path}")
    
    if not updated_files:
        print("No files needed updating.")

if __name__ == "__main__":
    main()
