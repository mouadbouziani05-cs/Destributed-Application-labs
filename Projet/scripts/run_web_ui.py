from __future__ import annotations

import bootstrap  # noqa: F401

from src.web_ui.app import app


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8501, debug=False)
