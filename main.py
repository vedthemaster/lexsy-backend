import os

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
            app="server:app",
            host="0.0.0.0",  # Listen on all interfaces
            port=int(os.getenv("PORT", 8000)),
            workers=4,  # Multiple workers for better performance
            reload=False,  # Disable auto-reload in production
            log_level="info",
            access_log=True,
    )