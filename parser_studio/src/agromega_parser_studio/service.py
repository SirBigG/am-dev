from dataclasses import dataclass

from .api import ParserApiClient, ParserApiError
from .parser import StaticSourceRunner


@dataclass(slots=True)
class RunResult:
    source: dict
    products: list[dict]
    receipt: dict | None = None
    duplicates_removed: int = 0


class ParserRunService:
    def __init__(self, api: ParserApiClient, runner=None):
        self.api = api
        self.runner = runner or StaticSourceRunner()

    def preview(self, source: dict) -> RunResult:
        products = self.runner.preview(source)
        return RunResult(
            source=source, products=products, duplicates_removed=getattr(self.runner, "duplicates_removed", 0)
        )

    def run(self, source: dict, *, force=True) -> RunResult:
        lease = self.api.lease(source["id"], force=force)
        try:
            products = self.runner.preview(source)
            receipt = self.api.submit_results(source["id"], lease["lease_token"], products, source)
            return RunResult(
                source=source,
                products=products,
                receipt=receipt,
                duplicates_removed=getattr(self.runner, "duplicates_removed", 0),
            )
        except Exception as exc:
            try:
                self.api.submit_failure(source["id"], lease["lease_token"], str(exc), source)
            except ParserApiError:
                pass
            raise
