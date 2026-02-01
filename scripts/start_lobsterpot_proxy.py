"""Start the LobsterPot guard proxy server."""

import os
import uvicorn


if __name__ == "__main__":
    port = int(os.getenv("LOBSTERPOT_PORT", "8070"))
    uvicorn.run(
        "lobsterpot.proxy_server:app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )
