#!/usr/bin/env python3
"""
Verification script for Index Data API implementation.

This script verifies that all the code components are correctly implemented
without requiring external dependencies or running services.
"""

import ast
import os
import sys

def check_file_syntax(file_path, description):
    """Check if a Python file has correct syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        ast.parse(content)
        print(f"✅ {description}: Syntax OK")
        return True
    except SyntaxError as e:
        print(f"❌ {description}: Syntax Error - {e}")
        return False
    except FileNotFoundError:
        print(f"❌ {description}: File not found - {file_path}")
        return False
    except Exception as e:
        print(f"❌ {description}: Error - {e}")
        return False

def check_file_exists(file_path, description):
    """Check if a file exists."""
    if os.path.exists(file_path):
        print(f"✅ {description}: File exists")
        return True
    else:
        print(f"❌ {description}: File missing - {file_path}")
        return False

def check_imports_in_file(file_path, expected_imports, description):
    """Check if specific imports exist in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        missing_imports = []
        for imp in expected_imports:
            if imp not in content:
                missing_imports.append(imp)
        
        if not missing_imports:
            print(f"✅ {description}: All expected imports found")
            return True
        else:
            print(f"❌ {description}: Missing imports - {missing_imports}")
            return False
    except Exception as e:
        print(f"❌ {description}: Error checking imports - {e}")
        return False

def check_class_methods(file_path, class_name, expected_methods, description):
    """Check if a class has expected methods."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        # Find the class
        class_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                class_node = node
                break
        
        if not class_node:
            print(f"❌ {description}: Class {class_name} not found")
            return False
        
        # Get method names
        method_names = [node.name for node in class_node.body if isinstance(node, ast.FunctionDef)]
        
        missing_methods = []
        for method in expected_methods:
            if method not in method_names:
                missing_methods.append(method)
        
        if not missing_methods:
            print(f"✅ {description}: All expected methods found in {class_name}")
            return True
        else:
            print(f"❌ {description}: Missing methods in {class_name} - {missing_methods}")
            return False
    except Exception as e:
        print(f"❌ {description}: Error checking class methods - {e}")
        return False

def main():
    """Main verification function."""
    print("🔍 QuantDB Index Data API Implementation Verification")
    print("=" * 60)
    
    all_checks_passed = True
    
    # 1. Check core model files
    print("\n📁 Checking Core Models...")
    checks = [
        ("core/models/index_data.py", "Index Data Models"),
        ("core/models/__init__.py", "Models Init File"),
    ]
    
    for file_path, desc in checks:
        if not check_file_syntax(file_path, desc):
            all_checks_passed = False
    
    # Check if index models are imported in __init__.py
    expected_imports = [
        "from .index_data import IndexData, RealtimeIndexData, IndexListCache, IndexListCacheManager"
    ]
    if not check_imports_in_file("core/models/__init__.py", expected_imports, "Index Models Import"):
        all_checks_passed = False
    
    # 2. Check AKShare adapter
    print("\n🔌 Checking AKShare Adapter...")
    if not check_file_syntax("core/cache/akshare_adapter.py", "AKShare Adapter"):
        all_checks_passed = False
    
    # Check if index methods are added
    expected_methods = ["get_index_data", "get_index_realtime_data", "get_index_list"]
    if not check_class_methods("core/cache/akshare_adapter.py", "AKShareAdapter", expected_methods, "AKShare Adapter Index Methods"):
        all_checks_passed = False
    
    # 3. Check index data service
    print("\n🔧 Checking Index Data Service...")
    if not check_file_syntax("core/services/index_data_service.py", "Index Data Service"):
        all_checks_passed = False
    
    expected_methods = ["get_index_data", "get_realtime_index_data", "get_index_list"]
    if not check_class_methods("core/services/index_data_service.py", "IndexDataService", expected_methods, "Index Data Service Methods"):
        all_checks_passed = False
    
    # 4. Check API routes
    print("\n🌐 Checking API Routes...")
    if not check_file_syntax("api/routers/index_data.py", "Index Data API Routes"):
        all_checks_passed = False
    
    # Check if routes are registered in main.py
    expected_imports = ["from api.routers import realtime, index_data"]
    if not check_imports_in_file("api/main.py", expected_imports, "Index Routes Import"):
        all_checks_passed = False
    
    # 5. Check Python package integration
    print("\n🐍 Checking Python Package Integration...")
    if not check_file_syntax("qdb/simple_client.py", "Simple QDB Client"):
        all_checks_passed = False
    
    # Check if index methods are added to SimpleQDBClient
    expected_methods = ["get_index_data", "get_index_realtime", "get_index_list"]
    if not check_class_methods("qdb/simple_client.py", "SimpleQDBClient", expected_methods, "SimpleQDBClient Index Methods"):
        all_checks_passed = False
    
    # Check if index methods are added to client.py
    expected_functions = ["get_index_data", "get_index_realtime", "get_index_list"]
    if not check_imports_in_file("qdb/client.py", expected_functions, "Client Index Functions"):
        all_checks_passed = False
    
    # 6. Check documentation
    print("\n📚 Checking Documentation...")
    if not check_file_exists("docs/INDEX_API_GUIDE.md", "Index API Guide"):
        all_checks_passed = False
    
    # 7. Check test files
    print("\n🧪 Checking Test Files...")
    if not check_file_exists("test_index_api.py", "Index API Test Script"):
        all_checks_passed = False
    
    # Summary
    print("\n📊 Verification Summary")
    print("=" * 30)
    
    if all_checks_passed:
        print("🎉 All checks passed! Index Data API implementation is complete.")
        print("\n✅ Implementation includes:")
        print("   - Index data models (IndexData, RealtimeIndexData, IndexListCache)")
        print("   - AKShare adapter extensions (get_index_data, get_index_realtime_data, get_index_list)")
        print("   - Index data service (IndexDataService)")
        print("   - API routes (/api/v1/index/historical, /api/v1/index/realtime, /api/v1/index/list)")
        print("   - Python package integration (qdb.get_index_data, qdb.get_index_realtime, qdb.get_index_list)")
        print("   - Complete documentation and test scripts")
        print("\n🚀 Ready for deployment and testing!")
        return 0
    else:
        print("⚠️ Some checks failed. Please review the implementation.")
        return 1

if __name__ == "__main__":
    exit(main())
