from __future__ import annotations

import Pyro5.api

from src.analysis_service.engine import AnalysisEngine
from src.common.config import SETTINGS
from src.common.logging_utils import configure_service_logging


logger = configure_service_logging("analysis_service")


@Pyro5.api.expose
class AnalysisRPCService:
    def __init__(self) -> None:
        self.engine = AnalysisEngine()

    def analyze_email(self, payload: dict) -> dict:
        return self.engine.analyze_email(payload)


def serve(host: str = SETTINGS.analysis_service_host, port: int = SETTINGS.analysis_service_port) -> None:
    daemon = Pyro5.api.Daemon(host=host, port=port)
    uri = daemon.register(AnalysisRPCService(), objectId="phishing.analysis")
    logger.info("Analysis RPC service ready", extra={"event": "analysis_started", "details": {"uri": str(uri)}})
    daemon.requestLoop()


if __name__ == "__main__":
    serve()
