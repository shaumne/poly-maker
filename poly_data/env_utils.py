"""
Environment variable loading utilities with BOM and encoding handling.

This module provides robust environment variable loading that handles:
- BOM (Byte Order Mark) characters in .env files
- Various encoding issues on Windows
- Missing or malformed .env files
"""
import os
import codecs
from pathlib import Path
from typing import Optional, Dict


def find_env_file() -> Optional[Path]:
    """
    Find the .env file by searching in common locations.
    
    Returns:
        Path to .env file if found, None otherwise
    """
    # Start from current directory and work up
    current_dir = Path.cwd()
    
    # Also check the directory where this script is located
    script_dir = Path(__file__).parent.parent
    
    search_paths = [
        current_dir / '.env',
        current_dir.parent / '.env',
        script_dir / '.env',
        script_dir.parent / '.env',
        Path(__file__).parent.parent.parent / '.env',  # Project root
    ]
    
    for env_path in search_paths:
        if env_path.exists():
            return env_path.resolve()
    
    return None


def remove_bom(content: str) -> str:
    """
    Remove BOM (Byte Order Mark) characters from the beginning of content.
    
    Args:
        content: String content that may contain BOM
        
    Returns:
        Content with BOM removed
    """
    # UTF-8 BOM
    if content.startswith('\ufeff'):
        content = content[1:]
    # UTF-16 LE BOM (as string)
    if content.startswith('\xff\xfe'):
        content = content[2:]
    # UTF-16 BE BOM (as string)
    if content.startswith('\xfe\xff'):
        content = content[2:]
    return content


def parse_env_line(line: str) -> Optional[tuple]:
    """
    Parse a single line from .env file.
    
    Args:
        line: A single line from .env file
        
    Returns:
        Tuple of (key, value) if valid, None otherwise
    """
    # Remove BOM from line (in case it appears mid-file)
    line = remove_bom(line)
    
    # Strip whitespace
    line = line.strip()
    
    # Skip empty lines and comments
    if not line or line.startswith('#'):
        return None
    
    # Find the first = sign
    if '=' not in line:
        return None
    
    key, _, value = line.partition('=')
    
    # Clean up key
    key = key.strip()
    
    # Skip if key is empty
    if not key:
        return None
    
    # Clean up value
    value = value.strip()
    
    # Remove quotes if present
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]
    
    return (key, value)


def load_env_file(env_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load environment variables from .env file with robust encoding handling.
    
    Args:
        env_path: Optional path to .env file. If None, will search for it.
        
    Returns:
        Dictionary of environment variables loaded from file
    """
    if env_path is None:
        env_path = find_env_file()
    
    if env_path is None or not env_path.exists():
        print("⚠️  No .env file found")
        return {}
    
    env_vars = {}
    
    # Try different encodings
    encodings_to_try = ['utf-8-sig', 'utf-8', 'utf-16', 'latin-1', 'cp1252']
    
    content = None
    used_encoding = None
    
    for encoding in encodings_to_try:
        try:
            with open(env_path, 'r', encoding=encoding) as f:
                content = f.read()
            used_encoding = encoding
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    if content is None:
        print(f"❌ Could not read .env file with any supported encoding")
        return {}
    
    # Remove BOM from content
    content = remove_bom(content)
    
    # Parse each line
    for line_num, line in enumerate(content.splitlines(), 1):
        try:
            result = parse_env_line(line)
            if result:
                key, value = result
                env_vars[key] = value
        except Exception as e:
            print(f"⚠️  Error parsing line {line_num} in .env: {e}")
            continue
    
    return env_vars


def load_dotenv_safe(env_path: Optional[str] = None, override: bool = False) -> bool:
    """
    Safely load environment variables from .env file.
    
    This function handles BOM characters and encoding issues that can occur
    on Windows systems when the .env file is created with certain text editors.
    
    Args:
        env_path: Optional path to .env file
        override: If True, override existing environment variables
        
    Returns:
        True if .env file was loaded successfully, False otherwise
    """
    try:
        # First, try the standard dotenv library with utf-8-sig encoding
        # (utf-8-sig automatically handles BOM)
        from dotenv import load_dotenv
        
        path = Path(env_path) if env_path else find_env_file()
        
        if path and path.exists():
            # Try with utf-8-sig first (handles BOM automatically)
            try:
                load_dotenv(dotenv_path=str(path), encoding='utf-8-sig', override=override)
                
                # Verify critical variables were loaded
                pk = os.getenv('PK')
                browser_address = os.getenv('BROWSER_ADDRESS')
                
                if pk and browser_address:
                    return True
            except Exception:
                pass
            
            # If standard loading didn't work, use our custom parser
            env_vars = load_env_file(path)
            
            if env_vars:
                for key, value in env_vars.items():
                    if override or key not in os.environ:
                        os.environ[key] = value
                
                return True
        
        return False
        
    except ImportError:
        # If dotenv is not installed, use our custom parser
        path = Path(env_path) if env_path else find_env_file()
        if path:
            env_vars = load_env_file(path)
            for key, value in env_vars.items():
                if override or key not in os.environ:
                    os.environ[key] = value
            return bool(env_vars)
        return False
    except Exception as e:
        print(f"❌ Error loading .env file: {e}")
        return False


def validate_env_variables() -> Dict[str, bool]:
    """
    Validate that required environment variables are set.
    
    Returns:
        Dictionary with variable names as keys and validation status as values
    """
    required_vars = {
        'PK': 'Private key for wallet',
        'BROWSER_ADDRESS': 'Polymarket proxy wallet address'
    }
    
    results = {}
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        is_valid = bool(value and value.strip() and 
                       value not in ['your_private_key_here', 'your_wallet_address_here', 
                                    'your_actual_wallet_address'])
        results[var] = is_valid
        
        if not is_valid:
            if not value:
                print(f"❌ {var} is not set. {description}")
            else:
                print(f"❌ {var} appears to have a placeholder value. {description}")
    
    return results

