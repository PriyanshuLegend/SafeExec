import os
import tempfile
import json
from context import get_cwd, get_user_context, get_recent_history, is_protected_path, gather_context

def main():
    print("--- 1. get_cwd() Output ---")
    print(f"Current Directory: {get_cwd()}")
    original_cwd = get_cwd()
    os.chdir(tempfile.gettempdir())
    print(f"Temp Directory: {get_cwd()}")
    os.chdir(original_cwd)
    
    print("\n--- 2. get_user_context() Output ---")
    normal_ctx = get_user_context()
    root_ctx = get_user_context(mock_root=True)
    print(f"Normal: {normal_ctx} | Mock Root: {root_ctx}")
    
    print("\n--- 3. get_recent_history(3) Output ---")
    with tempfile.NamedTemporaryFile('w', delete=False) as f:
        f.write("echo hello\ncd /\nls -la\nrm -rf /var/log\nsudo systemctl restart sshd\n")
        fake_hist_path = f.name
    
    os.environ['HISTFILE'] = fake_hist_path
    recent_hist = get_recent_history(3)
    print(f"Last 3 commands: {recent_hist}")
    os.remove(fake_hist_path)
    
    print("\n--- 4. is_protected_path() Output ---")
    paths_to_test = [
        "/etc/passwd", 
        "./node_modules", 
        "/home/user/project", 
        "/", 
        "/var/log/syslog", 
        "/tmp/build", 
        "", 
        "/etcsomething"
    ]
    for p in paths_to_test:
        res = is_protected_path(p)
        print(f"Path: {p!r:25} -> {res}")
        
    print("\n--- 5. gather_context() Output ---")
    cmd = "rm -rf /etc/nginx"
    ctx = gather_context(cmd, mock_root=False)
    print(json.dumps(ctx, indent=2))

if __name__ == "__main__":
    main()
