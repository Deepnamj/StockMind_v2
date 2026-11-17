def test_health_endpoint_import():
    # Basic import smoke test; full integration tests require API keys and MCP dependencies.
    from src.hitl.api import app
    assert app.title == "StockMind API"
