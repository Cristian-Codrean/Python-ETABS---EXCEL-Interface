import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Also add the gui folder specifically
gui_dir = os.path.join(current_dir, 'gui')
sys.path.insert(0, gui_dir)

print(f"Python path: {sys.path}")

try:
    from gui.main_window import DesignApp
    print("Successfully imported DesignApp")
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

if __name__ == "__main__":
    app = DesignApp()
    app.run()
