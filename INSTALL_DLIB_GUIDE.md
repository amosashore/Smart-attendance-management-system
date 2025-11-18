# Installing dlib and face_recognition for Python 3.12.5 on Windows

## Current Status
- Python Version: 3.12.5 ✅
- face-recognition-models: Installed ✅
- dlib: Not installed ❌
- face-recognition: Not installed ❌

## Problem
`dlib` requires compilation with C++ tools, which is complex on Windows.

---

## Solution Options

### Option 1: Download Pre-Built Wheel (RECOMMENDED) ⭐

1. **Find a compatible wheel:**
   
   Visit one of these sources:
   - https://github.com/z-mahmud22/Dlib_Windows_Python3.x (Latest wheels)
   - https://github.com/sachadee/Dlib (Alternative source)
   - Search Google for: "dlib cp312 win_amd64 wheel"

2. **Download the wheel for Python 3.12:**
   ```
   File pattern: dlib-*-cp312-cp312-win_amd64.whl
   ```

3. **Install the downloaded wheel:**
   ```powershell
   cd Downloads
   pip install dlib-19.24.2-cp312-cp312-win_amd64.whl
   ```

4. **Install face-recognition:**
   ```powershell
   pip install face-recognition
   ```

5. **Verify installation:**
   ```powershell
   python -c "import dlib; import face_recognition; print('Success!')"
   ```

---

### Option 2: Install Visual Studio Build Tools (Takes Time)

1. **Download Visual Studio Build Tools:**
   - URL: https://visualstudio.microsoft.com/downloads/
   - Select: "Build Tools for Visual Studio 2022" (Free)
   - Size: ~6 GB

2. **During installation:**
   - Check: "Desktop development with C++"
   - This includes CMake and MSVC compiler

3. **Restart your computer**

4. **Verify CMake is in PATH:**
   ```powershell
   cmake --version
   ```

5. **Install dlib and face-recognition:**
   ```powershell
   pip install dlib
   pip install face-recognition
   ```

---

### Option 3: Use Anaconda/Conda (If Available)

If you have Anaconda installed:

```powershell
conda install -c conda-forge dlib
pip install face-recognition
```

---

### Option 4: Quick Test with Alternative Library

For immediate testing, you can use `deepface` which is easier to install:

```powershell
pip install deepface
```

Then I can modify the code to support both libraries.

---

## Manual Installation Steps (Detailed)

### Step 1: Check Current State
```powershell
python -c "import sys; print(f'Python {sys.version}')"
# Should show: Python 3.12.5
```

### Step 2: Install Prerequisites
```powershell
pip install numpy
pip install cmake
pip install face-recognition-models
```

### Step 3: Download dlib Wheel

**For Python 3.12 (64-bit):**
1. Open browser
2. Go to: https://github.com/z-mahmud22/Dlib_Windows_Python3.x/releases
3. Download: `dlib-19.24.2-cp312-cp312-win_amd64.whl`
4. Save to Downloads folder

### Step 4: Install dlib
```powershell
cd $env:USERPROFILE\Downloads
pip install dlib-19.24.2-cp312-cp312-win_amd64.whl
```

### Step 5: Install face-recognition
```powershell
pip install face-recognition
```

### Step 6: Test Installation
```powershell
python -c "import face_recognition; print(face_recognition.__version__)"
```

---

## Quick Verification Script

Create a file `test_face_recognition.py`:

```python
import sys
print(f"Python: {sys.version}")

try:
    import dlib
    print(f"✅ dlib: {dlib.__version__}")
except ImportError as e:
    print(f"❌ dlib: Not installed - {e}")

try:
    import face_recognition
    print(f"✅ face_recognition: {face_recognition.__version__}")
except ImportError as e:
    print(f"❌ face_recognition: Not installed - {e}")

try:
    import cv2
    print(f"✅ opencv: {cv2.__version__}")
except ImportError as e:
    print(f"❌ opencv: Not installed - {e}")
```

Run it:
```powershell
python test_face_recognition.py
```

---

## Alternative: Use the App Without Face Recognition

The Smart Attendance System works perfectly without face recognition!

**Available features:**
- ✅ Manual attendance entry
- ✅ User management
- ✅ Reports and analytics
- ✅ Database management
- ✅ Export to Excel/CSV

Just run the app and use manual attendance marking.

---

## Need Help?

### Common Errors

**Error: "CMake not found"**
- Solution: Install Visual Studio Build Tools or download CMake from cmake.org

**Error: "Microsoft Visual C++ 14.0 is required"**
- Solution: Install Visual Studio Build Tools

**Error: "No matching distribution found"**
- Solution: Download the wheel file manually

**Error: "HTTP 404"**
- Solution: Check the wheel URL is correct and accessible

---

## After Successful Installation

1. **Restart the Streamlit app:**
   ```powershell
   streamlit run app.py
   ```

2. **Face recognition features will automatically activate**

3. **Test with Face Registration:**
   - Go to "Register Face" in the sidebar
   - Enter a name
   - Capture or upload a photo
   - System will detect and register the face

---

## Status Check Command

Run this to see what's installed:

```powershell
pip list | Select-String -Pattern "dlib|face-recognition|opencv|numpy|cmake"
```

---

**Last Updated:** November 12, 2025  
**Python Version:** 3.12.5  
**Platform:** Windows 64-bit
