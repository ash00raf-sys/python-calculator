from python_calculator.web import create_app


def test_home_page_loads_calculator():
    client = create_app({"TESTING": True}).test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Calm Calculator" in response.data
    assert b"calculator.js" in response.data


def test_calculate_api_returns_result():
    client = create_app({"TESTING": True}).test_client()

    response = client.post("/api/calculate", json={"expression": "(8 + 4) / 3"})

    assert response.status_code == 200
    assert response.get_json() == {"result": "4"}


def test_calculate_api_returns_safe_error():
    client = create_app({"TESTING": True}).test_client()

    response = client.post("/api/calculate", json={"expression": "open('secret')"})

    assert response.status_code == 400
    assert response.get_json() == {"error": "Function calls are not supported."}


def test_calculate_api_requires_an_expression():
    client = create_app({"TESTING": True}).test_client()

    response = client.post("/api/calculate", json={})

    assert response.status_code == 400
    assert response.get_json() == {"error": "Send an expression to calculate."}


def test_health_check():
    client = create_app({"TESTING": True}).test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
