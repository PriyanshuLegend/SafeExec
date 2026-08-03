import os
import posixpath
import shlex

def get_cwd() -> str:
    return os.getcwd()

def get_user_context(mock_root: bool = False) -> dict:
    if mock_root:
        return {"username": "root", "is_root": True}
    
    if hasattr(os, 'geteuid'):
        is_root = os.geteuid() == 0
    else:
        try:
            import ctypes
            is_root = ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            is_root = False
            
    try:
        import getpass
        username = getpass.getuser()
    except Exception:
        username = os.environ.get('USER', os.environ.get('USERNAME', 'unknown'))
        
    return {"username": username, "is_root": is_root}

def get_recent_history(n: int = 3) -> list:
    history_file = os.environ.get('HISTFILE', os.path.expanduser('~/.bash_history'))
    if not os.path.exists(history_file):
        return []
        
    try:
        with open(history_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = [line.strip() for line in f if line.strip()]
            return lines[-n:] if lines else []
    except Exception:
        return []

def is_protected_path(path: str) -> bool:
    if not path:
        return False
        
    protected_dirs = {'/', '/etc', '/var', '/usr', '/boot', '/bin', '/sbin', '/lib', '/root'}
    
    path = path.replace('\\', '/')
    
    if not posixpath.isabs(path):
        cwd = get_cwd().replace('\\', '/')
        if not cwd.startswith('/'):
            cwd = '/' + cwd
        norm_path = posixpath.normpath(posixpath.join(cwd, path))
    else:
        norm_path = posixpath.normpath(path)
        
    if norm_path in protected_dirs:
        return True
        
    if norm_path == '/':
        return True
        
    for pdir in protected_dirs:
        if pdir == '/':
            continue
        if norm_path.startswith(pdir + '/'):
            return True
            
    return False

def extract_target_path(command: str) -> str:
    try:
        parts = shlex.split(command)
    except Exception:
        parts = command.split()
        
    for part in reversed(parts):
        if not part.startswith('-') and '/' in part.replace('\\', '/'):
            return part
            
    if parts and not parts[-1].startswith('-'):
        return parts[-1]
        
    return ""

def gather_context(command: str, mock_root: bool = False) -> dict:
    target_path = extract_target_path(command)
    return {
        "cwd": get_cwd(),
        "username": get_user_context(mock_root)["username"],
        "is_root": get_user_context(mock_root)["is_root"],
        "recent_history": get_recent_history(),
        "target_path": target_path,
        "target_is_protected": is_protected_path(target_path)
    }
