"""
Script to fix common deprecation warnings in the codebase
"""
import os
import re
import sys
from pathlib import Path

def fix_sqlalchemy_declarative_base():
    """
    Fix the SQLAlchemy declarative_base deprecation warning
    
    Warning: The ``declarative_base()`` function is now available as sqlalchemy.orm.declarative_base()
    """
    database_file = "src/api/database.py"
    
    if not os.path.exists(database_file):
        print(f"Error: {database_file} not found")
        return False
    
    with open(database_file, "r") as f:
        content = f.read()
    
    # Replace the import
    new_content = re.sub(
        r"from sqlalchemy\.ext\.declarative import declarative_base",
        "from sqlalchemy.orm import declarative_base",
        content
    )
    
    if new_content != content:
        with open(database_file, "w") as f:
            f.write(new_content)
        print(f"Fixed SQLAlchemy declarative_base deprecation in {database_file}")
        return True
    else:
        print(f"No SQLAlchemy declarative_base deprecation found in {database_file}")
        return False

def fix_fastapi_on_event():
    """
    Fix the FastAPI on_event deprecation warning
    
    Warning: on_event is deprecated, use lifespan event handlers instead
    """
    main_file = "src/api/main.py"
    
    if not os.path.exists(main_file):
        print(f"Error: {main_file} not found")
        return False
    
    with open(main_file, "r") as f:
        content = f.read()
    
    # Check if we already have a lifespan context manager
    if "def lifespan" in content:
        print(f"Lifespan context manager already exists in {main_file}")
        return False
    
    # Extract startup and shutdown event handlers
    startup_match = re.search(r"@app\.on_event\(\"startup\"\)\s*def startup\(\):\s*(.*?)(?=@|\Z)", content, re.DOTALL)
    shutdown_match = re.search(r"@app\.on_event\(\"shutdown\"\)\s*def shutdown\(\):\s*(.*?)(?=@|\Z)", content, re.DOTALL)
    
    if not startup_match:
        print(f"No startup event handler found in {main_file}")
        return False
    
    startup_code = startup_match.group(1).strip()
    shutdown_code = shutdown_match.group(1).strip() if shutdown_match else ""
    
    # Create the lifespan context manager
    lifespan_code = f"""
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
{startup_code.replace('\n', '\n    ')}
    yield
    # Shutdown code
{shutdown_code.replace('\n', '\n    ')}
"""
    
    # Add the import for asynccontextmanager
    new_content = re.sub(
        r"from fastapi import (.*)",
        r"from fastapi import \1\nfrom contextlib import asynccontextmanager",
        content
    )
    
    # Add the lifespan context manager
    new_content = re.sub(
        r"app = FastAPI\((.*?)\)",
        f"app = FastAPI(\\1, lifespan=lifespan)",
        new_content
    )
    
    # Remove the old event handlers
    new_content = re.sub(
        r"@app\.on_event\(\"startup\"\)\s*def startup\(\):\s*(.*?)(?=@|\Z)",
        "",
        new_content,
        flags=re.DOTALL
    )
    
    new_content = re.sub(
        r"@app\.on_event\(\"shutdown\"\)\s*def shutdown\(\):\s*(.*?)(?=@|\Z)",
        "",
        new_content,
        flags=re.DOTALL
    )
    
    # Add the lifespan context manager
    new_content = re.sub(
        r"app = FastAPI\((.*?)\)",
        lifespan_code + "\n\napp = FastAPI(\\1, lifespan=lifespan)",
        new_content
    )
    
    if new_content != content:
        with open(main_file, "w") as f:
            f.write(new_content)
        print(f"Fixed FastAPI on_event deprecation in {main_file}")
        return True
    else:
        print(f"No FastAPI on_event deprecation found in {main_file}")
        return False

def fix_pydantic_config():
    """
    Fix the Pydantic config deprecation warning
    
    Warning: Support for class-based `config` is deprecated, use ConfigDict instead
    """
    schemas_files = [
        "src/api/schemas.py",
        "src/mcp/schemas.py",
        "src/cache/models.py"
    ]
    
    fixed_files = []
    
    for schemas_file in schemas_files:
        if not os.path.exists(schemas_file):
            print(f"Error: {schemas_file} not found")
            continue
        
        with open(schemas_file, "r") as f:
            content = f.read()
        
        # Add ConfigDict import if needed
        if "from pydantic import ConfigDict" not in content:
            new_content = re.sub(
                r"from pydantic import (.*)",
                r"from pydantic import \1, ConfigDict",
                content
            )
            if new_content == content:  # If no pydantic import found
                new_content = "from pydantic import ConfigDict\n" + content
        else:
            new_content = content
        
        # Replace class Config with model_config
        new_content = re.sub(
            r"class Config:\s*orm_mode = True",
            "model_config = ConfigDict(from_attributes=True)",
            new_content
        )
        
        # Replace other Config classes
        new_content = re.sub(
            r"class Config:\s*(.*?)(?=class|\Z)",
            lambda m: "model_config = ConfigDict(" + 
                      ", ".join([f"{k.strip()} = {v.strip()}" for k, v in 
                                re.findall(r"(\w+)\s*=\s*([^=\n]+)", m.group(1))]) + 
                      ")\n\n",
            new_content,
            flags=re.DOTALL
        )
        
        if new_content != content:
            with open(schemas_file, "w") as f:
                f.write(new_content)
            print(f"Fixed Pydantic config deprecation in {schemas_file}")
            fixed_files.append(schemas_file)
    
    return len(fixed_files) > 0

def main():
    """Main function to fix deprecation warnings"""
    print("Fixing deprecation warnings...")
    
    # Fix SQLAlchemy declarative_base deprecation
    fixed_sqlalchemy = fix_sqlalchemy_declarative_base()
    
    # Fix FastAPI on_event deprecation
    fixed_fastapi = fix_fastapi_on_event()
    
    # Fix Pydantic config deprecation
    fixed_pydantic = fix_pydantic_config()
    
    if fixed_sqlalchemy or fixed_fastapi or fixed_pydantic:
        print("\nSuccessfully fixed deprecation warnings!")
    else:
        print("\nNo deprecation warnings fixed.")

if __name__ == "__main__":
    main()
