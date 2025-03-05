from datetime import datetime

class Logger:
    def __init__(self, filename="logs.txt"):
        self.filename = filename
        # Clear the file on startup
        with open(self.filename, 'w') as f:
            f.write(f"=== Log started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
    
    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_message = f"[{timestamp}] {message}\n"
        with open(self.filename, 'a') as f:
            f.write(log_message) 