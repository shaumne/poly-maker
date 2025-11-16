"""
Settings API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pathlib import Path
from database import get_db, GlobalSettings
from schemas import SettingCreate, SettingUpdate, SettingResponse

router = APIRouter()

def update_env_file(key: str, value: str):
    """
    Update .env file with new key-value pair
    
    Args:
        key: Environment variable key
        value: Environment variable value
    """
    # Normalize key names
    env_key_map = {
        'pk': 'PK',
        'PK': 'PK',
        'browser_address': 'BROWSER_ADDRESS',
        'BROWSER_ADDRESS': 'BROWSER_ADDRESS'
    }
    
    env_key = env_key_map.get(key, key.upper())
    
    # Find .env file (check backend directory first, then root)
    env_paths = [
        Path('backend/.env'),
        Path('.env'),
        Path('../.env')
    ]
    
    env_file = None
    for path in env_paths:
        if path.exists():
            env_file = path
            break
    
    if not env_file:
        # Create .env file in backend directory if it doesn't exist
        env_file = Path('backend/.env')
        env_file.parent.mkdir(parents=True, exist_ok=True)
        env_file.touch()
    
    # Read existing .env file
    lines = []
    key_found = False
    
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    
    # Update or add the key
    new_lines = []
    for line in lines:
        # Skip comments and empty lines when checking
        stripped = line.strip()
        if stripped.startswith('#'):
            new_lines.append(line)
            continue
        
        # Check if this line contains our key
        if '=' in stripped:
            line_key = stripped.split('=')[0].strip()
            if line_key == env_key:
                # Update existing line
                new_lines.append(f"{env_key}={value}\n")
                key_found = True
                continue
        
        new_lines.append(line)
    
    # Add key if not found
    if not key_found:
        new_lines.append(f"{env_key}={value}\n")
    
    # Write back to file
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"Updated {env_key} in {env_file}")

@router.get("/", response_model=List[SettingResponse])
async def get_settings(db: Session = Depends(get_db)):
    """Get all global settings"""
    settings = db.query(GlobalSettings).all()
    return settings

@router.get("/{key}", response_model=SettingResponse)
async def get_setting(key: str, db: Session = Depends(get_db)):
    """Get a specific setting by key"""
    setting = db.query(GlobalSettings).filter(GlobalSettings.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    return setting

@router.post("/", response_model=SettingResponse)
async def create_setting(setting: SettingCreate, db: Session = Depends(get_db)):
    """
    Create a new setting
    
    Special handling for PK and BROWSER_ADDRESS:
    - Updates database
    - Updates .env file
    - Requires backend restart to take effect
    """
    existing = db.query(GlobalSettings).filter(GlobalSettings.key == setting.key).first()
    if existing:
        raise HTTPException(status_code=400, detail="Setting with this key already exists")
    
    db_setting = GlobalSettings(**setting.model_dump())
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    
    # Special handling for PK and BROWSER_ADDRESS - update .env file
    if setting.key in ['pk', 'PK', 'browser_address', 'BROWSER_ADDRESS']:
        try:
            update_env_file(setting.key, setting.value)
        except Exception as e:
            print(f"Warning: Failed to update .env file: {e}")
            # Don't fail the request, just log the warning
    
    return db_setting

@router.put("/{key}", response_model=SettingResponse)
async def update_setting(key: str, setting_update: SettingUpdate, db: Session = Depends(get_db)):
    """
    Update a setting
    
    Special handling for PK and BROWSER_ADDRESS:
    - Updates database
    - Updates .env file
    - Requires backend restart to take effect
    """
    db_setting = db.query(GlobalSettings).filter(GlobalSettings.key == key).first()
    if not db_setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    update_data = setting_update.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(db_setting, k, v)
    
    db.commit()
    db.refresh(db_setting)
    
    # Special handling for PK and BROWSER_ADDRESS - update .env file
    if key in ['pk', 'PK', 'browser_address', 'BROWSER_ADDRESS']:
        try:
            update_env_file(key, update_data.get('value', db_setting.value))
        except Exception as e:
            print(f"Warning: Failed to update .env file: {e}")
            # Don't fail the request, just log the warning
    
    return db_setting

@router.delete("/{key}")
async def delete_setting(key: str, db: Session = Depends(get_db)):
    """Delete a setting"""
    db_setting = db.query(GlobalSettings).filter(GlobalSettings.key == key).first()
    if not db_setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    db.delete(db_setting)
    db.commit()
    return {"message": "Setting deleted successfully"}

