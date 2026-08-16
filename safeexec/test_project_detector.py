import os
import tempfile
import shutil
from project_detector import detect_project_type
import json

def setup_fake_dir(files: list, dirs: list = None, file_contents: dict = None) -> str:
    tmpdir = tempfile.mkdtemp()
    file_contents = file_contents or {}
    for f in files:
        filepath = os.path.join(tmpdir, f)
        with open(filepath, 'w') as f_out:
            f_out.write(file_contents.get(f, ''))
    if dirs:
        for d in dirs:
            os.mkdir(os.path.join(tmpdir, d))
    return tmpdir

def main():
    print("--- Testing Project Detector ---")
    
    # 1. Fake Node project
    pkg_content = json.dumps({"scripts": {"dev": "vite", "build": "vite build", "test": "jest"}})
    d1 = setup_fake_dir(["package.json"], file_contents={"package.json": pkg_content})
    print("\n[Node Project]")
    print(json.dumps(detect_project_type(d1), indent=2))
    shutil.rmtree(d1)
    
    # 2. Fake Python project
    d2 = setup_fake_dir(["requirements.txt"])
    print("\n[Python Project]")
    print(json.dumps(detect_project_type(d2), indent=2))
    shutil.rmtree(d2)
    
    # 3. Fake Rust project
    d3 = setup_fake_dir(["Cargo.toml"])
    print("\n[Rust Project]")
    print(json.dumps(detect_project_type(d3), indent=2))
    shutil.rmtree(d3)
    
    # 4. Empty directory
    d4 = setup_fake_dir([])
    print("\n[Empty Directory]")
    print(json.dumps(detect_project_type(d4), indent=2))
    shutil.rmtree(d4)
    
    # 5. Node + Git
    d5 = setup_fake_dir(["package.json"], dirs=[".git"], file_contents={"package.json": pkg_content})
    print("\n[Node + Git Directory]")
    print(json.dumps(detect_project_type(d5), indent=2))
    shutil.rmtree(d5)

if __name__ == "__main__":
    main()
