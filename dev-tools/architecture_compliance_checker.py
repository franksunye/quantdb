#!/usr/bin/env python3
"""
Architecture Compliance Checker for QuantDB

This tool verifies that the qdb Python package follows the architecture principles:
1. 核心功能都在core里面
2. qdb只是前端的一个调用
3. 代码复用率90%+
4. 轻量级设计，最小依赖

Usage:
    python dev-tools/architecture_compliance_checker.py
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class ArchitectureComplianceChecker:
    """Check if qdb package follows architecture principles."""
    
    def __init__(self):
        self.project_root = project_root
        self.qdb_path = self.project_root / "qdb"
        self.core_path = self.project_root / "core"
        
        # Architecture violations
        self.violations = []
        self.warnings = []
        
    def check_all(self) -> Dict[str, any]:
        """Run all architecture compliance checks."""
        print("🔍 Running QuantDB Architecture Compliance Checks...")
        print("=" * 60)
        
        results = {
            "lightweight_design": self.check_lightweight_design(),
            "business_logic_separation": self.check_business_logic_separation(),
            "service_initialization": self.check_service_initialization(),
            "code_reuse": self.check_code_reuse(),
            "dependency_direction": self.check_dependency_direction(),
        }
        
        self.print_summary(results)
        return results
    
    def check_lightweight_design(self) -> bool:
        """Check if qdb follows lightweight design principles."""
        print("\n📦 Checking Lightweight Design...")
        
        violations = []
        
        # Check for complex business logic in qdb files
        for py_file in self.qdb_path.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
                
            content = py_file.read_text()
            
            # Check for complex date calculations
            if "timedelta" in content and "datetime" in content:
                violations.append(f"{py_file.name}: Contains date calculation logic")
            
            # Check for database initialization
            if "create_all" in content or "Base.metadata" in content:
                violations.append(f"{py_file.name}: Contains database initialization logic")
            
            # Check for service instantiation
            if "Service(" in content and "=" in content:
                violations.append(f"{py_file.name}: Contains service instantiation logic")
            
            # Check for complex parameter processing
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "if" in line and ("days" in line or "start_date" in line):
                    # Look for complex parameter processing logic
                    if i + 1 < len(lines) and ("timedelta" in lines[i+1] or "strftime" in lines[i+1]):
                        violations.append(f"{py_file.name}:{i+1}: Contains parameter processing logic")
        
        if violations:
            self.violations.extend(violations)
            print("❌ Lightweight design violations found:")
            for violation in violations:
                print(f"   - {violation}")
            return False
        else:
            print("✅ qdb follows lightweight design principles")
            return True
    
    def check_business_logic_separation(self) -> bool:
        """Check if business logic is properly separated to core layer."""
        print("\n🧠 Checking Business Logic Separation...")
        
        violations = []
        
        # Check qdb files for business logic
        for py_file in self.qdb_path.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
                
            try:
                with open(py_file, 'r') as f:
                    tree = ast.parse(f.read())
                
                # Look for complex methods (more than simple delegation)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Check if function has complex logic
                        if self._has_complex_logic(node):
                            violations.append(f"{py_file.name}:{node.lineno}: Function '{node.name}' contains business logic")
                            
            except Exception as e:
                self.warnings.append(f"Could not parse {py_file.name}: {e}")
        
        if violations:
            self.violations.extend(violations)
            print("❌ Business logic separation violations found:")
            for violation in violations:
                print(f"   - {violation}")
            return False
        else:
            print("✅ Business logic properly separated to core layer")
            return True
    
    def check_service_initialization(self) -> bool:
        """Check if service initialization is delegated to core."""
        print("\n🔧 Checking Service Initialization...")
        
        violations = []
        
        # Check for direct service initialization in qdb
        for py_file in self.qdb_path.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
                
            content = py_file.read_text()
            
            # Look for direct service imports and instantiation
            if "from core.services" in content and "Service(" in content:
                # Check if it's not using ServiceManager
                if "ServiceManager" not in content and "get_service_manager" not in content:
                    violations.append(f"{py_file.name}: Direct service instantiation without ServiceManager")
            
            # Check for database session management
            if "get_db()" in content or "SessionLocal()" in content:
                violations.append(f"{py_file.name}: Direct database session management")
        
        if violations:
            self.violations.extend(violations)
            print("❌ Service initialization violations found:")
            for violation in violations:
                print(f"   - {violation}")
            return False
        else:
            print("✅ Service initialization properly delegated to core")
            return True
    
    def check_code_reuse(self) -> bool:
        """Check for code duplication across products."""
        print("\n🔄 Checking Code Reuse...")
        
        # This is a simplified check - in practice, you'd want more sophisticated analysis
        duplications = []
        
        # Check for similar initialization patterns
        qdb_files = list(self.qdb_path.glob("*.py"))
        api_files = list((self.project_root / "api").glob("**/*.py"))
        cloud_files = list((self.project_root / "cloud").glob("**/*.py"))
        
        # Look for similar service initialization patterns
        init_patterns = []
        for file_group, name in [(qdb_files, "qdb"), (api_files, "api"), (cloud_files, "cloud")]:
            for py_file in file_group:
                if py_file.name.startswith("__"):
                    continue
                    
                content = py_file.read_text()
                if "StockDataService" in content and "AKShareAdapter" in content:
                    init_patterns.append((name, py_file.name))
        
        if len(init_patterns) > 1:
            # Check if they're using the same ServiceManager
            using_service_manager = 0
            not_using_service_manager = []

            for group, filename in init_patterns:
                file_path = self.project_root / group / filename
                if file_path.exists():
                    content = file_path.read_text()
                    if "ServiceManager" in content or "get_service_manager" in content:
                        using_service_manager += 1
                    else:
                        not_using_service_manager.append(f"{group}/{filename}")

            # Only flag as violation if there are files NOT using ServiceManager
            if not_using_service_manager:
                duplications.append(f"Service initialization patterns duplicated in: {', '.join(not_using_service_manager)} (should use ServiceManager)")
        
        if duplications:
            self.violations.extend(duplications)
            print("❌ Code reuse violations found:")
            for duplication in duplications:
                print(f"   - {duplication}")
            return False
        else:
            print("✅ Good code reuse patterns detected")
            return True
    
    def check_dependency_direction(self) -> bool:
        """Check if dependencies flow in the correct direction (qdb -> core, not core -> qdb)."""
        print("\n➡️ Checking Dependency Direction...")
        
        violations = []
        
        # Check core files for qdb imports
        for py_file in self.core_path.glob("**/*.py"):
            if py_file.name.startswith("__"):
                continue
                
            content = py_file.read_text()
            if "from qdb" in content or "import qdb" in content:
                violations.append(f"{py_file.relative_to(self.project_root)}: Core imports from qdb (wrong direction)")
        
        if violations:
            self.violations.extend(violations)
            print("❌ Dependency direction violations found:")
            for violation in violations:
                print(f"   - {violation}")
            return False
        else:
            print("✅ Dependencies flow in correct direction")
            return True
    
    def _has_complex_logic(self, func_node: ast.FunctionDef) -> bool:
        """Check if a function has complex business logic."""
        # Simple heuristic: if function has more than just return/call statements
        complex_nodes = 0
        
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
                complex_nodes += 1
            elif isinstance(node, ast.Call):
                # Check for date/time calculations
                if hasattr(node.func, 'attr') and node.func.attr in ['strftime', 'strptime']:
                    complex_nodes += 1
                elif hasattr(node.func, 'id') and node.func.id in ['timedelta', 'datetime']:
                    complex_nodes += 1
        
        # Allow some complexity for error handling, but flag excessive logic
        return complex_nodes > 2
    
    def print_summary(self, results: Dict[str, bool]):
        """Print compliance check summary."""
        print("\n" + "=" * 60)
        print("📊 ARCHITECTURE COMPLIANCE SUMMARY")
        print("=" * 60)
        
        passed = sum(results.values())
        total = len(results)
        
        for check, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{check.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall Score: {passed}/{total} ({passed/total*100:.1f}%)")
        
        if self.violations:
            print(f"\n🚨 {len(self.violations)} violations found:")
            for violation in self.violations:
                print(f"   - {violation}")
        
        if self.warnings:
            print(f"\n⚠️ {len(self.warnings)} warnings:")
            for warning in self.warnings:
                print(f"   - {warning}")
        
        if passed == total:
            print("\n🎉 qdb package is fully compliant with architecture principles!")
        else:
            print(f"\n🔧 Please fix {len(self.violations)} violations to achieve full compliance.")


def main():
    """Run architecture compliance checks."""
    checker = ArchitectureComplianceChecker()
    results = checker.check_all()
    
    # Exit with error code if violations found
    if checker.violations:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
