from waitress import serve
from app import app

if __name__ == "__main__":
    print("Starting Waitress Server on port 8080...")
    # هذا سيشغل التطبيق داخلياً على المنفذ 8080
    serve(app, host='0.0.0.0', port=8080)