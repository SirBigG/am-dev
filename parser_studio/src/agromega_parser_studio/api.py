from urllib.parse import urljoin

import requests


class ParserApiError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None, payload=None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class ParserApiClient:
    def __init__(self, base_url: str, token: str, timeout: int = 30, session=None):
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update({"Authorization": f"Token {token}"})

    def request(self, method: str, path: str, *, params=None, json=None, retries=0):
        url = urljoin(self.base_url, path.lstrip("/"))
        for attempt in range(retries + 1):
            try:
                response = self.session.request(
                    method,
                    url,
                    params=params,
                    json=json,
                    timeout=self.timeout,
                )
            except requests.RequestException as exc:
                if attempt < retries:
                    continue
                raise ParserApiError(f"Network error: {exc}") from exc
            if response.status_code >= 500 and attempt < retries:
                continue
            if not response.ok:
                try:
                    payload = response.json()
                except ValueError:
                    payload = response.text
                raise ParserApiError(
                    f"API returned HTTP {response.status_code}: {payload}",
                    status_code=response.status_code,
                    payload=payload,
                )
            if response.status_code == 204:
                return None
            return response.json()
        raise ParserApiError("API request did not produce a response.")

    def health_check(self):
        return self.list_sources(scope="all", limit=1)

    def list_sources(self, *, scope="all", limit=100, company=None, category=None, active=None):
        params = {"scope": scope, "limit": limit}
        if company is not None:
            params["company"] = company
        if category:
            params["category"] = category
        if active is not None:
            params["active"] = str(active).lower()
        return self.request("GET", "api/parser/sources/", params=params)

    def source_detail(self, source_id: int):
        return self.request("GET", f"api/parser/sources/{source_id}/")

    def list_companies(self, page_size=200):
        return self.request("GET", "api/parser/companies/", params={"page_size": page_size})

    def list_attempts(self, source_id=None, page_size=100):
        params = {"page_size": page_size}
        if source_id is not None:
            params["source"] = source_id
        return self.request("GET", "api/parser/attempts/", params=params)

    def list_products(self, source_id=None, page_size=200):
        params = {"page_size": page_size}
        if source_id is not None:
            params["source"] = source_id
        return self.request("GET", "api/parser/products/", params=params)

    def list_price_history(self, source_id=None, page_size=200):
        params = {"page_size": page_size}
        if source_id is not None:
            params["source"] = source_id
        return self.request("GET", "api/parser/price-history/", params=params)

    def lease(self, source_id: int, *, duration_minutes=30, force=False):
        return self.request(
            "POST",
            f"api/parser/sources/{source_id}/lease/",
            json={"duration_minutes": duration_minutes, "force": force},
        )

    def submit_results(self, source_id: int, lease_token: str, products: list[dict], source: dict):
        parser_map = source.get("parser_map") or {}
        return self.request(
            "POST",
            f"api/parser/sources/{source_id}/results/",
            json={
                "lease_token": lease_token,
                "products": products,
                "snapshot_complete": bool(parser_map.get("snapshot_complete", False)),
                "parser_config_version": source.get("parser_config_version") or "",
                "parser_config": parser_map,
            },
            retries=2,
        )

    def submit_failure(self, source_id: int, lease_token: str, error: str, source: dict, status=None):
        return self.request(
            "POST",
            f"api/parser/sources/{source_id}/failure/",
            json={
                "lease_token": lease_token,
                "status": status,
                "error": str(error)[:2000],
                "parser_config_version": source.get("parser_config_version") or "",
                "parser_config": source.get("parser_map") or {},
            },
            retries=2,
        )
