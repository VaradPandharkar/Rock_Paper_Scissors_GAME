import mediapipe as mp
import os
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

print("Testing path")
task_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hand_landmarker.task')

try:
    base_options = mp_python.BaseOptions(model_asset_path='hand_landmarker.task')
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        num_hands=2,
        running_mode=vision.RunningMode.IMAGE
    )
    detector = vision.HandLandmarker.create_from_options(options)
    print("Success with relative path")
except Exception as e:
    print("Relative path failed:", repr(e))

try:
    base_options = mp_python.BaseOptions(model_asset_path=task_path)
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        num_hands=2,
        running_mode=vision.RunningMode.IMAGE
    )
    detector = vision.HandLandmarker.create_from_options(options)
    print("Success with absolute path")
except Exception as e:
    print("Absolute path failed:", repr(e))

try:
    with open(task_path, 'rb') as f:
        model_buffer = f.read()
    base_options = mp_python.BaseOptions(model_asset_buffer=model_buffer)
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        num_hands=2,
        running_mode=vision.RunningMode.IMAGE
    )
    detector = vision.HandLandmarker.create_from_options(options)
    print("Success with buffer")
except Exception as e:
    print("Buffer failed:", repr(e))
