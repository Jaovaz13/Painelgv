import os

def find_null_bytes():
    all_files = []
    for root, dirs, files in os.walk('.'):
        if '.git' in root or '.venv' in root or 'data' in root:
            continue
        for f_name in files:
            path = os.path.join(root, f_name)
            try:
                # Skip large binary files
                if os.path.getsize(path) > 1_000_000:
                    continue
                with open(path, 'rb') as f:
                    data = f.read()
                    if b'\x00' in data:
                        all_files.append(path)
            except Exception as e:
                pass
    
    for f in all_files:
        print(f"NULL BYTE IN: {f}")

if __name__ == "__main__":
    find_null_bytes()
