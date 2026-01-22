# dev_ws_service.py
# IMPORTANT: Monkey patching must be called before importing Flask
# This patches standard library modules to work with green threads
import sys
import platform

# Detect Windows and use appropriate server
IS_WINDOWS = platform.system() == 'Windows'

if IS_WINDOWS:
    # On Windows, use gevent instead of eventlet (better Windows support)
    try:
        import gevent
        from gevent import monkey
        monkey.patch_all()
        USE_GEVENT = True
    except ImportError:
        print("Warning: gevent not installed. Install it with: pip install gevent")
        print("Attempting to use eventlet (may have issues on Windows)...")
        import eventlet
        try:
            eventlet.monkey_patch()
            USE_GEVENT = False
        except Exception as e:
            print(f"Error: eventlet monkey patching failed on Windows: {e}")
            print("Please install gevent: pip install gevent")
            sys.exit(1)
else:
    # On Unix-like systems, use eventlet (simpler and more compatible)
    import eventlet
    eventlet.monkey_patch()
    USE_GEVENT = False

import uuid
import json
from typing import Dict

import requests
from flask import Flask, request, jsonify
from flask_sock import Sock

app = Flask(__name__)
sock = Sock(app)

# connection_id -> WebSocket
connections: Dict[str, 'WebSocket'] = {}

# Where to send incoming messages from WS to your backend
BACKEND_WS_INGEST_URL = "http://127.0.0.1:5001/_chat/message"


def handle_websocket(ws):
    """Handle WebSocket connection logic."""
    # Create a connection_id similar to API Gateway
    connection_id = str(uuid.uuid4())
    connections[connection_id] = ws

    # Optionally tell the client its connection_id
    try:
        ws.send(json.dumps({"type": "connection_ack", "connection_id": connection_id}))
    except Exception as e:
        print(f"Error sending connection_ack: {e}")
        return

    print(f"Connected: {connection_id}")

    try:
        while True:
            # Receive message from client
            raw = ws.receive()
            if raw is None:
                break

            # Parse the message
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                print(f"Invalid JSON received: {raw}")
                continue

            # Data is an object, add connectionId to it
            if not isinstance(data, dict):
                print('Payload must be an object')
                continue

            # Add connectionId to the data object
            data['connectionId'] = connection_id

            # Forward to backend as an HTTP POST
            try:
                requests.post(BACKEND_WS_INGEST_URL, json=data, timeout=5)
            except Exception as e:
                # In dev this is fine; log error
                print("Error posting to backend:", e)

    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Cleanup on disconnect
        connections.pop(connection_id, None)
        print(f"Disconnected: {connection_id}")


@sock.route("/")
def websocket_root(ws):
    """Handle WebSocket connection at root path."""
    handle_websocket(ws)


@sock.route("/ws")
def websocket_endpoint(ws):
    """Handle WebSocket connection at /ws path."""
    handle_websocket(ws)


@app.route("/send_to_client", methods=["POST"])
def send_to_client():
    """
    HTTP endpoint your backend can call to push a message to a specific WebSocket client.
    """
    data = request.get_json()
    connection_id = data.get("connection_id")
    payload = data.get("payload")

    if not connection_id or not payload:
        return jsonify({"ok": False, "error": "missing_connection_id_or_payload"}), 400

    ws = connections.get(connection_id)
    if not ws:
        return jsonify({"ok": False, "error": "connection_not_found"}), 404

    # Send JSON back to the client via WebSocket
    try:
        ws.send(json.dumps(payload))
        return jsonify({"ok": True})
    except Exception as e:
        print(f"Error sending to client: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    # flask-sock works with eventlet or gevent
    if USE_GEVENT:
        # Use gevent for Windows compatibility
        from gevent import pywsgi
        
        print("WebSocket service running on ws://0.0.0.0:8080 (using gevent)")
        print("Connect from browser using: ws://127.0.0.1:8080/ws")
        server = pywsgi.WSGIServer(('0.0.0.0', 8080), app)
        server.serve_forever()
    else:
        # Use eventlet for Unix-like systems
        from eventlet import wsgi
        
        print("WebSocket service running on ws://0.0.0.0:8080 (using eventlet)")
        print("Connect from browser using: ws://127.0.0.1:8080/ws")
        wsgi.server(eventlet.listen(('0.0.0.0', 8080)), app)