from agromega_parser_studio.parser import StaticSourceRunner, extract_price, parse_html


def test_item_scoped_parser_preserves_missing_optional_price():
    products = parse_html(
        ("<section><article><h2>Golden</h2><span>42,50 грн</span></article><article><h2>Gala</h2></article></section>"),
        {"item": "//article", "name": ".//h2/text()", "price": ".//span/text()"},
    )

    assert products == [{"name": "Golden", "price": 42.5}, {"name": "Gala", "price": None}]


def test_price_normalization_supports_ukrainian_format():
    assert extract_price("1 234,56 грн") == 1234.56


def test_static_runner_uses_source_friendly_request_headers():
    runner = StaticSourceRunner()

    assert "AgroMegaParser" in runner.session.headers["User-Agent"]
    assert runner.session.headers["Accept-Language"].startswith("uk-UA")


class FakeResponse:
    content = b'<article><h2>Golden</h2><a href="/golden">Open</a></article>'

    @staticmethod
    def raise_for_status():
        return None


class FakeSession:
    def get(self, url, timeout):
        assert url == "https://shop.example/apples"
        assert timeout == 30
        return FakeResponse()


def test_static_runner_normalizes_relative_product_url():
    source = {
        "url": "https://shop.example/apples",
        "source_type": "static",
        "parser_map": {"item": "//article", "name": ".//h2/text()", "link": ".//a/@href"},
    }

    products = StaticSourceRunner(session=FakeSession()).preview(source)

    assert products[0]["name"] == "Golden"
    assert products[0]["product_url"] == "https://shop.example/golden"


class PaginatedResponse:
    def __init__(self, content):
        self.content = content

    @staticmethod
    def raise_for_status():
        return None


class PaginatedSession:
    def __init__(self):
        self.urls = []

    def get(self, url, timeout):
        self.urls.append(url)
        pages = {
            "https://shop.example/apples": (
                b'<article><h2>Golden</h2><a class="product" href="/golden">Open</a></article>'
                b'<a class="next" href="/apples/page/2">Next</a>'
            ),
            "https://shop.example/apples/page/2": (
                b'<article><h2>Gala</h2><a class="product" href="/gala">Open</a></article>'
            ),
        }
        return PaginatedResponse(pages[url])


def test_static_runner_follows_configured_next_page():
    session = PaginatedSession()
    source = {
        "url": "https://shop.example/apples",
        "source_type": "static",
        "parser_map": {
            "item": "//article",
            "name": ".//h2/text()",
            "link": ".//a[contains(@class, 'product')]/@href",
            "next_page": "//a[contains(@class, 'next')]/@href",
            "max_pages": 3,
        },
    }

    products = StaticSourceRunner(session=session).preview(source)

    assert [product["name"] for product in products] == ["Golden", "Gala"]
    assert session.urls == ["https://shop.example/apples", "https://shop.example/apples/page/2"]
