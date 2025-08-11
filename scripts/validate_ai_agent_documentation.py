#!/usr/bin/env python3
"""
Documentation Validation Script for AI Agent Compatibility

This script validates that the QDB package documentation meets AI agent
requirements by checking docstring format, parameter specifications,
and example code validity.
"""

import ast
import inspect
import re
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import qdb
except ImportError as e:
    print(f"❌ Cannot import qdb: {e}")
    sys.exit(1)


class DocstringValidator:
    """Validates docstrings for AI agent compatibility."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed = []
    
    def validate_function(self, func_name: str, func_obj: Any) -> Dict[str, Any]:
        """Validate a single function's docstring."""
        result = {
            'function': func_name,
            'has_docstring': False,
            'has_args_section': False,
            'has_returns_section': False,
            'has_raises_section': False,
            'has_examples_section': False,
            'has_type_hints': False,
            'parameter_count': 0,
            'documented_params': 0,
            'issues': []
        }
        
        # Check if function has docstring
        docstring = inspect.getdoc(func_obj)
        if not docstring:
            result['issues'].append("Missing docstring")
            return result
        
        result['has_docstring'] = True
        
        # Check for required sections
        if 'Args:' in docstring or 'Arguments:' in docstring:
            result['has_args_section'] = True
        else:
            result['issues'].append("Missing Args section")
        
        if 'Returns:' in docstring:
            result['has_returns_section'] = True
        else:
            result['issues'].append("Missing Returns section")
        
        if 'Raises:' in docstring:
            result['has_raises_section'] = True
        else:
            result['issues'].append("Missing Raises section")
        
        if 'Examples:' in docstring or 'Example:' in docstring:
            result['has_examples_section'] = True
        else:
            result['issues'].append("Missing Examples section")
        
        # Check type hints
        try:
            sig = inspect.signature(func_obj)
            result['parameter_count'] = len(sig.parameters)
            
            has_type_hints = True
            for param_name, param in sig.parameters.items():
                if param.annotation == inspect.Parameter.empty and param_name != 'self':
                    has_type_hints = False
                    break
            
            if sig.return_annotation != inspect.Signature.empty:
                result['has_type_hints'] = has_type_hints
            else:
                result['has_type_hints'] = False
                result['issues'].append("Missing return type annotation")
                
        except Exception as e:
            result['issues'].append(f"Cannot inspect signature: {e}")
        
        # Count documented parameters
        if result['has_args_section']:
            # Simple heuristic: count lines that look like parameter documentation
            args_section = self._extract_args_section(docstring)
            param_lines = [line for line in args_section.split('\n') 
                          if ':' in line and not line.strip().startswith('-')]
            result['documented_params'] = len(param_lines)
        
        return result
    
    def _extract_args_section(self, docstring: str) -> str:
        """Extract the Args section from docstring."""
        lines = docstring.split('\n')
        in_args = False
        args_lines = []
        
        for line in lines:
            if line.strip().startswith('Args:') or line.strip().startswith('Arguments:'):
                in_args = True
                continue
            elif in_args and line.strip().endswith(':') and not line.startswith('    '):
                # Hit another section
                break
            elif in_args:
                args_lines.append(line)
        
        return '\n'.join(args_lines)
    
    def validate_core_functions(self) -> Dict[str, Any]:
        """Validate the core QDB functions."""
        core_functions = [
            'get_stock_data',
            'get_realtime_data',
            'get_stock_list',
            'cache_stats',
            'get_financial_summary',
            'get_financial_indicators',
            'get_index_data',
            'get_index_realtime',
            'get_index_list'
        ]
        
        results = {}
        
        for func_name in core_functions:
            try:
                func_obj = getattr(qdb, func_name)
                results[func_name] = self.validate_function(func_name, func_obj)
            except AttributeError:
                results[func_name] = {
                    'function': func_name,
                    'issues': [f"Function {func_name} not found in qdb module"]
                }
        
        return results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a validation report."""
        report = []
        report.append("🤖 AI Agent Documentation Validation Report")
        report.append("=" * 50)
        
        total_functions = len(results)
        passed_functions = 0
        
        for func_name, result in results.items():
            report.append(f"\n📋 Function: {func_name}")
            
            if not result.get('issues'):
                report.append("   ✅ All checks passed")
                passed_functions += 1
            else:
                report.append("   ❌ Issues found:")
                for issue in result['issues']:
                    report.append(f"      - {issue}")
            
            # Detailed metrics
            if result.get('has_docstring'):
                report.append(f"   📝 Docstring: ✅")
                report.append(f"   📋 Args section: {'✅' if result.get('has_args_section') else '❌'}")
                report.append(f"   📤 Returns section: {'✅' if result.get('has_returns_section') else '❌'}")
                report.append(f"   ⚠️  Raises section: {'✅' if result.get('has_raises_section') else '❌'}")
                report.append(f"   💡 Examples section: {'✅' if result.get('has_examples_section') else '❌'}")
                report.append(f"   🏷️  Type hints: {'✅' if result.get('has_type_hints') else '❌'}")
                
                param_count = result.get('parameter_count', 0)
                documented_params = result.get('documented_params', 0)
                if param_count > 0:
                    coverage = (documented_params / param_count) * 100
                    report.append(f"   📊 Parameter coverage: {documented_params}/{param_count} ({coverage:.0f}%)")
            else:
                report.append("   📝 Docstring: ❌ Missing")
        
        # Summary
        report.append(f"\n📊 Summary:")
        report.append(f"   Total functions validated: {total_functions}")
        report.append(f"   Functions passed: {passed_functions}")
        report.append(f"   Functions with issues: {total_functions - passed_functions}")
        report.append(f"   Success rate: {(passed_functions/total_functions)*100:.1f}%")
        
        if passed_functions == total_functions:
            report.append("\n🎉 All functions meet AI agent documentation standards!")
        else:
            report.append(f"\n⚠️  {total_functions - passed_functions} functions need improvement")
        
        return '\n'.join(report)


def validate_example_code():
    """Validate that example code in docstrings is syntactically correct."""
    print("\n🧪 Validating Example Code Syntax...")
    
    functions_to_check = ['get_stock_data', 'get_realtime_data', 'get_stock_list', 'cache_stats',
                          'get_financial_summary', 'get_financial_indicators', 'get_index_data',
                          'get_index_realtime', 'get_index_list']
    issues = []
    
    for func_name in functions_to_check:
        try:
            func_obj = getattr(qdb, func_name)
            docstring = inspect.getdoc(func_obj)
            
            if docstring and 'Examples:' in docstring:
                # Extract code examples (simple heuristic)
                lines = docstring.split('\n')
                in_examples = False
                code_lines = []
                
                for line in lines:
                    if 'Examples:' in line:
                        in_examples = True
                        continue
                    elif in_examples and line.strip().endswith(':') and not line.startswith('    '):
                        break
                    elif in_examples and line.strip().startswith('>>>'):
                        # Extract code after >>>
                        code = line.strip()[3:].strip()
                        if code:
                            code_lines.append(code)
                
                # Validate syntax
                for i, code in enumerate(code_lines):
                    try:
                        ast.parse(code)
                        print(f"   ✅ {func_name} example {i+1}: Valid syntax")
                    except SyntaxError as e:
                        issues.append(f"{func_name} example {i+1}: {e}")
                        print(f"   ❌ {func_name} example {i+1}: Syntax error")
            
        except Exception as e:
            issues.append(f"Error checking {func_name}: {e}")
    
    if not issues:
        print("🎉 All example code has valid syntax!")
    else:
        print(f"⚠️  Found {len(issues)} syntax issues in examples")
        for issue in issues:
            print(f"   - {issue}")
    
    return len(issues) == 0


def check_ai_agent_schema():
    """Check if AI agent schema file exists and is valid."""
    print("\n📋 Checking AI Agent Schema...")
    
    schema_path = project_root / "docs" / "qdb-ai-agent-schema.json"
    
    if not schema_path.exists():
        print("❌ AI agent schema file not found")
        return False
    
    try:
        import json
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        
        required_keys = ['package_info', 'functions', 'usage_patterns']
        missing_keys = [key for key in required_keys if key not in schema]
        
        if missing_keys:
            print(f"❌ Schema missing required keys: {missing_keys}")
            return False
        
        print(f"✅ Schema file valid with {len(schema['functions'])} functions documented")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Schema file has invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading schema: {e}")
        return False


def main():
    """Run all validation checks."""
    print("🚀 Starting QDB AI Agent Documentation Validation")
    
    # Validate core function documentation
    validator = DocstringValidator()
    results = validator.validate_core_functions()
    report = validator.generate_report(results)
    print(report)
    
    # Validate example code syntax
    examples_valid = validate_example_code()
    
    # Check AI agent schema
    schema_valid = check_ai_agent_schema()
    
    # Final assessment
    print("\n" + "=" * 50)
    print("🎯 Final Assessment:")
    
    passed_functions = sum(1 for r in results.values() if not r.get('issues'))
    total_functions = len(results)
    
    if passed_functions == total_functions and examples_valid and schema_valid:
        print("🟢 EXCELLENT: QDB is fully AI agent ready!")
        print("   - All functions have complete documentation")
        print("   - All examples have valid syntax") 
        print("   - AI agent schema is available")
        return 0
    elif passed_functions >= total_functions * 0.75:
        print("🟡 GOOD: QDB is mostly AI agent ready")
        print(f"   - {passed_functions}/{total_functions} functions documented")
        print(f"   - Examples valid: {examples_valid}")
        print(f"   - Schema available: {schema_valid}")
        return 1
    else:
        print("🔴 NEEDS WORK: QDB needs more documentation improvements")
        print(f"   - Only {passed_functions}/{total_functions} functions properly documented")
        return 2


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
