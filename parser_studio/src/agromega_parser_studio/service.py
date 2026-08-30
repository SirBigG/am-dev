from dataclasses import dataclass

from .api import ParserApiClient, ParserApiError
from .parser import StaticSourceRunner


@dataclass(slots=True)
class RunResult:
    source: dict
    products: list[dict]
    receipt: dict | None = None


class ParserRunService:
    def __init__(self, api: ParserApiClient, runner=None):
        self.api = api
        self.runner = runner or StaticSourceRunner()

    def preview(self, source: dict) -> RunResult:
        return RunResult(source=source, products=self.runner.preview(source))

    def run(self, source: dict, *, force=True) -> RunResult:
        lease = self.api.lease(source["id"], force=force)
        try:
            products = self.runner.preview(source)
            receipt = self.api.submit_results(source["id"], lease["lease_token"], products, source)
            return RunResult(source=source, products=products, receipt=receipt)
        except Exception as exc:
            try:
                self.api.submit_failure(source["id"], lease["lease_token"], str(exc), source)
            except ParserApiError:
                pass
            raise
