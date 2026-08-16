import os
import json

def detect_project_type(cwd: str) -> dict:
    result = {
        "project_type": "unknown",
        "markers_found": [],
        "package_manager": None,
        "scripts": []
    }
    
    if not os.path.isdir(cwd):
        return result
        
    try:
        entries = set(os.listdir(cwd))
    except Exception:
        return result
        
    # Check for marker files
    if "package.json" in entries:
        result["project_type"] = "node"
        result["markers_found"].append("package.json")
        if "yarn.lock" in entries:
            result["package_manager"] = "yarn"
            result["markers_found"].append("yarn.lock")
        else:
            result["package_manager"] = "npm"
            if "package-lock.json" in entries:
                result["markers_found"].append("package-lock.json")
        
        # Extract scripts from package.json
        try:
            with open(os.path.join(cwd, "package.json"), "r", encoding="utf-8") as f:
                pkg_data = json.load(f)
                if "scripts" in pkg_data and isinstance(pkg_data["scripts"], dict):
                    result["scripts"] = list(pkg_data["scripts"].keys())
        except Exception:
            pass
                
    elif "requirements.txt" in entries or "pyproject.toml" in entries:
        result["project_type"] = "python"
        result["package_manager"] = "pip"
        if "requirements.txt" in entries:
            result["markers_found"].append("requirements.txt")
        if "pyproject.toml" in entries:
            result["markers_found"].append("pyproject.toml")
            
    elif "Cargo.toml" in entries:
        result["project_type"] = "rust"
        result["package_manager"] = "cargo"
        result["markers_found"].append("Cargo.toml")
        
    elif "Dockerfile" in entries:
        result["project_type"] = "docker"
        result["markers_found"].append("Dockerfile")
        
    elif ".git" in entries:
        # Check if it's a directory
        git_path = os.path.join(cwd, ".git")
        if os.path.isdir(git_path):
            result["project_type"] = "git"
            result["markers_found"].append(".git")
            
    # Check for .git even if we already found something else
    if ".git" in entries and result["project_type"] != "git":
        git_path = os.path.join(cwd, ".git")
        if os.path.isdir(git_path) and ".git" not in result["markers_found"]:
            result["markers_found"].append(".git")
            
    return result
