"""Unit and integration tests for advanced tools API endpoints."""
import io
import pytest


class TestAdvancedToolsAPI:
    def test_execute_code_success(self, client, auth_headers):
        payload = {
            "code": "result = len([1, 2, 3])"
        }
        r = client.post("/api/v1/tools/execute-code", headers=auth_headers, json=payload)
        assert r.status_code == 200
        resp = r.json()
        assert resp["success"] is True
        assert resp["result"] == 3

    def test_execute_code_syntax_error(self, client, auth_headers):
        payload = {
            "code": "result = len([1, 2"
        }
        r = client.post("/api/v1/tools/execute-code", headers=auth_headers, json=payload)
        assert r.status_code == 200
        resp = r.json()
        assert resp["success"] is False
        assert "Syntax" in resp["error"]

    def test_execute_code_dangerous_blocked(self, client, auth_headers):
        payload = {
            "code": "import os; os.system('ls')"
        }
        r = client.post("/api/v1/tools/execute-code", headers=auth_headers, json=payload)
        assert r.status_code == 200
        resp = r.json()
        assert resp["success"] is False
        assert "restricted" in resp["error"]

    def test_calculate_success(self, client, auth_headers):
        payload = {"expression": "cos(0) + sin(0)"}
        r = client.post("/api/v1/tools/calculate", headers=auth_headers, json=payload)
        assert r.status_code == 200
        resp = r.json()
        assert resp["success"] is True
        assert resp["result"] == 1.0

    def test_calculate_division_by_zero(self, client, auth_headers):
        payload = {"expression": "1 / 0"}
        r = client.post("/api/v1/tools/calculate", headers=auth_headers, json=payload)
        assert r.status_code == 200
        resp = r.json()
        assert resp["success"] is False
        assert "Division by zero" in resp["error"]

    def test_calculate_restricted_word(self, client, auth_headers):
        payload = {"expression": "open('test.txt')"}
        r = client.post("/api/v1/tools/calculate", headers=auth_headers, json=payload)
        assert r.status_code == 200
        resp = r.json()
        assert resp["success"] is False
        assert "not allowed" in resp["error"]

    def test_analyze_file_text_endpoint(self, client, auth_headers):
        payload = {
            "filename": "notes.txt",
            "content": "Line 1\nLine 2\nLine 3 with words"
        }
        r = client.post("/api/v1/tools/analyze-file-text", headers=auth_headers, json=payload)
        assert r.status_code == 200
        resp = r.json()
        assert resp["success"] is True
        assert resp["result"]["lines"] == 3
        assert resp["result"]["words"] == 8

    def test_analyze_file_json_endpoint(self, client, auth_headers):
        payload = {
            "filename": "data.json",
            "content": '{"key1": "val1", "key2": 100}'
        }
        r = client.post("/api/v1/tools/analyze-file-text", headers=auth_headers, json=payload)
        assert r.status_code == 200
        resp = r.json()
        assert resp["success"] is True
        assert resp["result"]["type"] == "json"
        assert resp["result"]["valid"] is True
        assert "key1" in resp["result"]["keys"]

    def test_analyze_file_upload(self, client, auth_headers):
        content = b"header1,header2\nval1,10\nval2,20"
        files = {"file": ("data.csv", io.BytesIO(content), "text/csv")}
        r = client.post("/api/v1/tools/analyze-file", headers=auth_headers, files=files)
        assert r.status_code == 200
        resp = r.json()
        assert resp["success"] is True
        assert resp["result"]["type"] == "csv"
        assert resp["result"]["rows"] == 2
        assert resp["result"]["headers"] == ["header1", "header2"]

    def test_generate_chart(self, client, auth_headers):
        payload = {
            "data": [
                {"label": "A", "value": 10},
                {"label": "B", "value": 20}
            ],
            "chart_type": "bar"
        }
        r = client.post("/api/v1/tools/generate-chart", headers=auth_headers, json=payload)
        assert r.status_code == 200
        resp = r.json()
        assert resp["success"] is True
        assert resp["result"]["chart"]["type"] == "bar"
        assert resp["result"]["stats"]["sum"] == 30

    def test_generate_chart_from_csv(self, client, auth_headers):
        payload = [
            ["Label", "Value"],
            ["Item A", 100],
            ["Item B", 200]
        ]
        r = client.post("/api/v1/tools/generate-chart-from-csv", headers=auth_headers, json=payload)
        assert r.status_code == 200
        resp = r.json()
        assert resp["success"] is True
        assert resp["result"]["stats"]["sum"] == 300

    def test_get_available_tools(self, client, auth_headers):
        r = client.get("/api/v1/tools/tools/available", headers=auth_headers)
        assert r.status_code == 200
        resp = r.json()
        assert "tools" in resp
        assert len(resp["tools"]) >= 3
