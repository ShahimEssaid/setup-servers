from filelock import Timeout, FileLock
import time

file_path = "high_ground.txt"
lock_path = "high_ground.txt.lock"

lock = FileLock(lock_path, timeout=1)

with lock:
    time.sleep(100)

print("Done with lock")
