#!/usr/bin/env python3
"""
Streamlit compatibility checker for QuantDB Cloud Edition
"""
import streamlit as st
import sys

def check_streamlit_version():
    """Check Streamlit version and compatibility"""
    print("🔍 Checking Streamlit compatibility...")
    
    # Get Streamlit version
    streamlit_version = st.__version__
    print(f"📦 Streamlit version: {streamlit_version}")
    
    # Parse version
    try:
        major, minor, patch = map(int, streamlit_version.split('.'))
        version_tuple = (major, minor, patch)
    except:
        print("❌ Could not parse Streamlit version")
        return False
    
    # Check for deprecated methods
    deprecated_methods = []
    
    # Check st.experimental_rerun (deprecated in 1.18.0, removed in 1.27.0)
    if hasattr(st, 'experimental_rerun'):
        print("⚠️  st.experimental_rerun is available (deprecated)")
        deprecated_methods.append('experimental_rerun')
    else:
        print("✅ st.experimental_rerun not found (good - use st.rerun)")
    
    # Check st.rerun (available from 1.18.0+)
    if hasattr(st, 'rerun'):
        print("✅ st.rerun is available")
    else:
        print("❌ st.rerun not available - need Streamlit 1.18.0+")
        return False
    
    # Check st.cache_resource (available from 1.18.0+)
    if hasattr(st, 'cache_resource'):
        print("✅ st.cache_resource is available")
    else:
        print("❌ st.cache_resource not available - need Streamlit 1.18.0+")
        return False
    
    # Version-specific recommendations
    if version_tuple >= (1, 27, 0):
        print("🎉 Streamlit version is modern and fully supported")
    elif version_tuple >= (1, 18, 0):
        print("✅ Streamlit version is compatible")
        if deprecated_methods:
            print("⚠️  Consider updating deprecated methods")
    else:
        print("❌ Streamlit version is too old - need 1.18.0+")
        return False
    
    return True

def check_app_compatibility():
    """Check app files for compatibility issues"""
    print("\n🔍 Checking app files for compatibility...")
    
    import os
    import re
    from pathlib import Path
    
    current_dir = Path(__file__).parent
    
    # Files to check
    files_to_check = [
        current_dir / "app.py",
        current_dir / "pages" / "1_📈_股票数据查询.py",
        current_dir / "pages" / "2_📊_资产信息.py",
        current_dir / "pages" / "3_⚡_系统状态.py"
    ]
    
    issues_found = []
    
    for file_path in files_to_check:
        if not file_path.exists():
            continue
            
        print(f"📄 Checking {file_path.name}...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for deprecated methods
            if 'st.experimental_rerun' in content:
                issues_found.append(f"{file_path.name}: uses st.experimental_rerun")
                print(f"  ❌ Found st.experimental_rerun")
            else:
                print(f"  ✅ No st.experimental_rerun found")
            
            if 'st.experimental_' in content:
                experimental_matches = re.findall(r'st\.experimental_\w+', content)
                for match in experimental_matches:
                    if match != 'st.experimental_rerun':  # Already checked above
                        issues_found.append(f"{file_path.name}: uses {match}")
                        print(f"  ⚠️  Found {match}")
            
        except Exception as e:
            print(f"  ❌ Error reading file: {e}")
    
    if issues_found:
        print(f"\n⚠️  Found {len(issues_found)} compatibility issues:")
        for issue in issues_found:
            print(f"  - {issue}")
        return False
    else:
        print("\n✅ No compatibility issues found in app files")
        return True

def main():
    """Main compatibility check"""
    print("🚀 QuantDB Streamlit Compatibility Check")
    print("=" * 50)
    
    # Check Streamlit version
    version_ok = check_streamlit_version()
    
    # Check app files
    files_ok = check_app_compatibility()
    
    print("\n" + "=" * 50)
    if version_ok and files_ok:
        print("🎉 All compatibility checks passed!")
        print("✅ App is ready for deployment")
        return True
    else:
        print("❌ Compatibility issues found")
        print("🔧 Please fix issues before deployment")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
