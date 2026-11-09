from app import create_app

def test_health():
    app=create_app()
    app.config["TESTING"]=True
    with app.test_client() as c:
        r=c.get("/api/health")
        assert r.status_code==200
        assert r.json["status"]=="ok"

def test_stats():
    app=create_app()
    app.config["TESTING"]=True
    with app.test_client() as c:
        r=c.get("/api/stats")
        assert r.status_code==200
        assert r.json["foods"] > 0
