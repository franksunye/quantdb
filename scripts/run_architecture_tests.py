#!/usr/bin/env python3
"""
Architecture Tests Runner

Run tests that validate the architecture refactor without requiring
external dependencies like pandas, akshare, etc.
"""

import sys
import subprocess
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_architecture_compliance_check():
    """Run architecture compliance check."""
    print("🔍 Running Architecture Compliance Check...")
    print("=" * 60)
    
    try:
        result = subprocess.run([
            sys.executable, "dev-tools/architecture_compliance_checker.py"
        ], cwd=project_root, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run architecture compliance check: {e}")
        return False

def run_structure_tests():
    """Run structure tests."""
    print("\n🏗️ Running Structure Tests...")
    print("=" * 60)
    
    try:
        result = subprocess.run([
            sys.executable, "scripts/test_architecture_structure.py"
        ], cwd=project_root, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run structure tests: {e}")
        return False

def run_syntax_checks():
    """Run Python syntax checks on key files."""
    print("\n🔍 Running Syntax Checks...")
    print("=" * 60)
    
    key_files = [
        "qdb/__init__.py",
        "qdb/client.py", 
        "qdb/exceptions.py",
        "core/services/service_manager.py",
        "core/services/__init__.py",
        "api/dependencies.py"
    ]
    
    all_passed = True
    
    for file_path in key_files:
        full_path = project_root / file_path
        if not full_path.exists():
            print(f"⚠️ File not found: {file_path}")
            continue
            
        try:
            result = subprocess.run([
                sys.executable, "-m", "py_compile", str(full_path)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {file_path} - Syntax OK")
            else:
                print(f"❌ {file_path} - Syntax Error:")
                print(result.stderr)
                all_passed = False
                
        except Exception as e:
            print(f"❌ {file_path} - Check failed: {e}")
            all_passed = False
    
    return all_passed

def run_import_tests():
    """Test that key modules can be imported."""
    print("\n📦 Running Import Tests...")
    print("=" * 60)
    
    import_tests = [
        ("qdb", "import qdb"),
        ("qdb.client", "from qdb.client import LightweightQDBClient"),
        ("qdb.exceptions", "from qdb.exceptions import QDBError"),
        ("core.services", "from core.services import ServiceManager, get_service_manager"),
        ("core.services.service_manager", "from core.services.service_manager import ServiceManager"),
    ]
    
    all_passed = True
    
    for test_name, import_statement in import_tests:
        try:
            # Create a new Python process to test import
            result = subprocess.run([
                sys.executable, "-c", import_statement
            ], cwd=project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {test_name} - Import OK")
            else:
                print(f"❌ {test_name} - Import Failed:")
                print(result.stderr)
                all_passed = False
                
        except Exception as e:
            print(f"❌ {test_name} - Import test failed: {e}")
            all_passed = False
    
    return all_passed

def run_basic_functionality_tests():
    """Test basic functionality without external dependencies."""
    print("\n⚡ Running Basic Functionality Tests...")
    print("=" * 60)
    
    test_script = '''
import sys
import tempfile
import os
from pathlib import Path

# Add project root to path
project_root = Path(os.getcwd())
sys.path.insert(0, str(project_root))

try:
    # Test ServiceManager can be created
    from core.services import get_service_manager, reset_service_manager
    
    # Reset for clean test
    reset_service_manager()
    
    # Test with temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        service_manager = get_service_manager(cache_dir=temp_dir)
        print("✅ ServiceManager creation - OK")
        
        # Test singleton pattern
        service_manager2 = get_service_manager()
        assert service_manager is service_manager2
        print("✅ ServiceManager singleton - OK")
        
    # Test qdb module structure
    import qdb
    
    # Test that functions exist (without calling them)
    required_functions = [
        'init', 'get_stock_data', 'get_multiple_stocks', 
        'get_asset_info', 'cache_stats', 'clear_cache'
    ]
    
    for func_name in required_functions:
        assert hasattr(qdb, func_name), f"Missing function: {func_name}"
        assert callable(getattr(qdb, func_name)), f"Not callable: {func_name}"
    
    print("✅ qdb API structure - OK")
    
    # Test qdb client can be created
    from qdb.client import LightweightQDBClient
    
    with tempfile.TemporaryDirectory() as temp_dir:
        client = LightweightQDBClient(cache_dir=temp_dir)
        print("✅ LightweightQDBClient creation - OK")
    
    print("🎉 All basic functionality tests passed!")
    
except Exception as e:
    print(f"❌ Basic functionality test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
'''
    
    try:
        result = subprocess.run([
            sys.executable, "-c", test_script
        ], cwd=project_root, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run basic functionality tests: {e}")
        return False

def run_unit_tests_subset():
    """Run a subset of unit tests that don't require external dependencies."""
    print("\n🧪 Running Unit Tests Subset...")
    print("=" * 60)
    
    # Try to run some basic unit tests
    test_files = [
        "tests/unit/test_qdb_exceptions.py",
        "tests/unit/test_helpers.py",
        "tests/unit/test_validators.py"
    ]
    
    all_passed = True
    
    for test_file in test_files:
        full_path = project_root / test_file
        if not full_path.exists():
            print(f"⚠️ Test file not found: {test_file}")
            continue
        
        try:
            # Try to run the test file directly as a Python script
            result = subprocess.run([
                sys.executable, str(full_path)
            ], cwd=project_root, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"✅ {test_file} - Tests passed")
            else:
                print(f"❌ {test_file} - Tests failed:")
                print(result.stdout)
                print(result.stderr)
                all_passed = False
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_file} - Test timeout")
            all_passed = False
        except Exception as e:
            print(f"❌ {test_file} - Test execution failed: {e}")
            all_passed = False
    
    return all_passed

def main():
    """Run all architecture tests."""
    print("🧪 QuantDB Architecture Refactor - Complete Test Suite")
    print("=" * 80)
    
    tests = [
        ("Architecture Compliance", run_architecture_compliance_check),
        ("Structure Tests", run_structure_tests),
        ("Syntax Checks", run_syntax_checks),
        ("Import Tests", run_import_tests),
        ("Basic Functionality", run_basic_functionality_tests),
        ("Unit Tests Subset", run_unit_tests_subset),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 COMPLETE TEST RESULTS SUMMARY")
    print("=" * 80)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
    
    print(f"\nOverall Score: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("Architecture refactor is successful and ready for production!")
        return True
    else:
        print(f"\n🔧 {total-passed} tests failed.")
        print("Please review and fix the issues before proceeding.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
