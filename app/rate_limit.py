
import time
from collections import defaultdict, deque
from threading import Lock

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

        # 每個 Client 對應自己的請求時間紀錄
        self.requests = defaultdict(deque)
        self.lock = Lock()

    def allow_request(self, client_id: str) -> bool:
        now = time.monotonic()

        with self.lock:
            timestamps = self.requests[client_id]

            # 移除超過時間窗口的舊紀錄
            while timestamps and now - timestamps[0] >= self.window_seconds:
                timestamps.popleft()

            # 已達到請求上限
            if len(timestamps) >= self.max_requests:
                return False

            # 記錄這一次被允許的請求
            timestamps.append(now)
            return True
