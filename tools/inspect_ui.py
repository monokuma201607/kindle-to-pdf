import uiautomation as auto
import time

def main():
    print("Searching for Kindle window with uiautomation...")
    
    # Try to find the window
    # Note: Name might vary, using ClassName or Regex might be safer if Name matches partly
    kindle_window = auto.WindowControl(searchDepth=1, ClassName='Qt5QWindowIcon')
    
    if not kindle_window.Exists(maxSearchSeconds=3):
        # Retry with partial name match
        kindle_window = auto.WindowControl(searchDepth=1, Name='Kindle for PC')
        
    if not kindle_window.Exists(maxSearchSeconds=1):
        print("Kindle window not found (uiautomation).")
        # List all top windows just to see
        print("Top level windows:")
        for win in auto.GetRootControl().GetChildren():
            print(f"  Name: '{win.Name}', Class: '{win.ClassName}'")
        return

    print(f"Found Kindle Window: {kindle_window.Name}")
    
    # Dump tree
    # We want to find the Table of Contents.
    # It's usually a ListControl or TreeControl, or just TextControls inside a pane.
    # Walking the whole tree might be huge, so let's limit depth.
    
    print("\n--- Inspecting UI Structure (Depth 5) ---")
    
    def walk(control, depth):
        if depth > 5:
            return
        
        indent = "  " * depth
        try:
            print(f"{indent}{control.ControlTypeName}: '{control.Name}' (Rect: {control.BoundingRectangle})")
        except:
            pass
            
        for child in control.GetChildren():
            walk(child, depth + 1)

    walk(kindle_window, 0)

if __name__ == "__main__":
    main()
