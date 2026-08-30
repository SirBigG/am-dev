import requests

from agromega_parser_studio.api import ParserApiClient, ParserApiError


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self.payload = payload
        self.ok = 200 <= status_code < 300
        self.text = str(payload)

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.headers = {}
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return next(self.responses)


def test_source_catalog_uses_all_scope_and_token_header():
    session = FakeSession([FakeResponse(payload=[{"id": 4}])])
    client = ParserApiClient("https://agromega.example", "secret", session=session)

    result = client.list_sources()

    assert result == [{"id": 4}]
    assert session.headers["Authorization"] == "Token secret"
    assert session.calls[0][2]["params"]["scope"] == "all"


def test_force_lease_payload_is_explicit():
    session = FakeSession([FakeResponse(payload={"lease_token": "lease-1"})])
    client = ParserApiClient("https://agromega.example", "secret", session=session)

    client.lease(4, force=True)

    assert session.calls[0][2]["json"] == {"duration_minutes": 30, "force": True}


def test_api_errors_retain_status_and_payload():
    session = FakeSession([FakeResponse(status_code=403, payload={"detail": "permission required"})])
    client = ParserApiClient("https://agromega.example", "secret", session=session)

    try:
        client.lease(4, force=True)
    except ParserApiError as exc:
        assert exc.status_code == 403
        assert exc.payload == {"detail": "permission required"}
    else:
        raise AssertionError("ParserApiError was not raised")


def test_result_submission_retries_uncertain_transport_with_same_payload():
    session = FakeSession(
        [
            requests.ConnectionError("response lost"),
            FakeResponse(payload={"count": 1, "replayed": True}),
        ]
    )

    def request(method, url, **kwargs):
        response = next(session.responses)
        session.calls.append((method, url, kwargs))
        if isinstance(response, Exception):
            raise response
        return response

    session.request = request
    client = ParserApiClient("https://agromega.example", "secret", session=session)
    source = {"id": 4, "parser_map": {"name": "//h2"}, "parser_config_version": "v1"}

    result = client.submit_results(4, "lease-1", [{"name": "Golden"}], source)

    assert result["replayed"] is True
    assert session.calls[0][2]["json"] == session.calls[1][2]["json"]
