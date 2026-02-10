try:
    import numpy
    print(f"Numpy: {numpy.__version__}")
    
    import torch
    print(f"Torch: {torch.__version__}")
    print(f"Torch C: {hasattr(torch._C, '_get_operation_overload')}") # Check for previous crash attribute
    
    # Check moviepy imports
    try:
        from moviepy.editor import VideoFileClip
        print("MoviePy: import from .editor WORKS (v1 style)")
    except ImportError:
        print("MoviePy: import from .editor FAILED")
        
    try:
        from moviepy import VideoFileClip
        print("MoviePy: import from root WORKS (v2 style)")
    except ImportError:
        print("MoviePy: import from root FAILED")

except Exception as e:
    print(f"Error: {e}")
