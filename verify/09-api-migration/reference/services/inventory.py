import api


def _get(path: str, **kwargs):
    return api.get_json(path, **kwargs)


def stock_level(sku: str) -> int:
    data = _get(f"/stock/{sku}")
    return 0 if data is None else data["available"]


def reserved(sku: str) -> int:
    return _get(f"/stock/{sku}/reserved", timeout=2)["count"]


def warehouses() -> list[dict]:
    return _get("/warehouses")["items"]


def low_stock(threshold: int = 5) -> list[dict]:
    return _get("/stock", params={"below": threshold})["items"]
