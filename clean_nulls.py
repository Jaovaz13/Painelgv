import os

def clean_file(path):
    print(f"Checking {path}...")
    with open(path, 'rb') as f:
        data = f.read()
    
    if b'\x00' in data:
        print(f"CLEANING: {path}")
        clean_data = data.replace(b'\x00', b'')
        with open(path, 'wb') as f:
            f.write(clean_data)
        return True
    return False

def main():
    cleaned_count = 0
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                if clean_file(path):
                    cleaned_count += 1
    
    print(f"Finished. Cleaned {cleaned_count} files.")

if __name__ == "__main__":
    main()
