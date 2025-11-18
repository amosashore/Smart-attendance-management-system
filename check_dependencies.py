"""
Dependency checker and installer helper
Run this before starting the application
"""
import sys
import subprocess

def check_package(package_name, import_name=None):
    """Check if a package is installed"""
    if import_name is None:
        import_name = package_name.replace('-', '_')
    
    try:
        __import__(import_name)
        print(f"✓ {package_name}")
        return True
    except ImportError:
        print(f"✗ {package_name} - NOT INSTALLED")
        return False

def main():
    print("=" * 60)
    print("  Smart Attendance System - Dependency Check")
    print("=" * 60)
    print()
    
    packages = [
        ('streamlit', 'streamlit'),
        ('opencv-python', 'cv2'),
        ('numpy', 'numpy'),
        ('pandas', 'pandas'),
        ('pillow', 'PIL'),
        ('python-dotenv', 'dotenv'),
        ('bcrypt', 'bcrypt'),
        ('openpyxl', 'openpyxl'),
        ('plotly', 'plotly'),
        ('pyttsx3', 'pyttsx3'),
        ('pygame', 'pygame'),
        ('face-recognition', 'face_recognition'),
    ]
    
    missing = []
    
    print("Checking installed packages:\n")
    for package, import_name in packages:
        if not check_package(package, import_name):
            missing.append(package)
    
    print()
    
    if missing:
        print("=" * 60)
        print(f"  Missing {len(missing)} package(s)")
        print("=" * 60)
        print()
        print("To install missing packages, run:")
        print()
        
        if 'face-recognition' in missing:
            print("NOTE: face-recognition requires dlib which needs C++ compiler")
            print("For Windows users, you have two options:")
            print()
            print("Option 1 - Install from wheel (RECOMMENDED):")
            print("  1. Download dlib wheel from:")
            print("     https://github.com/sachadee/Dlib/blob/master/dlib-19.22.99-cp313-cp313-win_amd64.whl")
            print("  2. Install it:")
            print(f"     {sys.executable} -m pip install path/to/dlib-*.whl")
            print("  3. Then install face-recognition:")
            print(f"     {sys.executable} -m pip install face-recognition")
            print()
            print("Option 2 - Install Visual Studio Build Tools:")
            print("  1. Download from: https://visualstudio.microsoft.com/downloads/")
            print("  2. Install 'Desktop development with C++'")
            print("  3. Then run:")
            print(f"     {sys.executable} -m pip install dlib face-recognition")
            print()
            missing.remove('face-recognition')
        
        if missing:
            print("For other packages:")
            print(f"  {sys.executable} -m pip install {' '.join(missing)}")
        
        print()
        print("=" * 60)
        return False
    else:
        print("=" * 60)
        print("  ✓ All dependencies installed!")
        print("=" * 60)
        print()
        print("You can now run the application:")
        print(f"  streamlit run app.py")
        print()
        return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
