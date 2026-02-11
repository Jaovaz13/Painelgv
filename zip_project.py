import zipfile
import os
from pathlib import Path

def zip_project(source_dir, output_filename):
    source_path = Path(source_dir)
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_path):
            # Exclude venv and git and pycache
            dirs[:] = [d for d in dirs if d not in ['.venv', '.git', '__pycache__', '.gemini']]
            
            for file in files:
                if file.endswith('.pyc') or file == os.path.basename(output_filename):
                    continue
                
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_path)
                print(f"Adding {arcname}")
                zipf.write(file_path, arcname)

if __name__ == "__main__":
    zip_project(r"c:\painel_gv", r"c:\painel_gv\painel_gv_completo.zip")
    print("Project zipped successfully!")
