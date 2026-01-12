# WebSocket Service (Dev Tool)

A development WebSocket service for local testing.

IMPORTANT: This is not a production grade WSS, you should only use it to run a WSS in localhost during development.
This WSS emulates the functionality of the AWS API Gateway WebSocket Service.

Let’s assume:

- WebSocket Dev Service runs at ws://localhost:8080
- Local backend API runs at http://localhost:5001
- The backend has an endpoint like: POST /ws-ingest
- The WS dev service exposes an endpoint: POST /send_to_client

Flow:

1. Client connects → WS service generates connection_id, stores it in a dict, and (optionally) sends it to the client.
2.	Client sends message → WS service:
	- Wraps it into a payload: { connection_id, body, ... }
	- POSTs it to http://localhost:5001/ws-ingest
3.	Backend processes that, then when it wants to reply:
	- POSTs to http://127.0.0.1:8080/send_to_client with:

```
{ "connection_id": "<id>", "payload": { ... } }
```

4.	WS service looks up that connection_id in the dict and send_text() back over the WebSocket.


## FE Implementation

Frontend (React, etc.) connects to WSS:

```
const ws = new WebSocket("ws://localhost:8080/ws");

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("WS message:", data);
};
```

## Setup

1. Create and activate the virtual environment:
```bash
# Run the setup script (creates wss-venv and installs dependencies)
./setup_venv.sh

# Or manually:
python3 -m venv wss-venv
source wss-venv/bin/activate
pip install -r requirements.txt
```

## Running

1. Activate the virtual environment:
```bash
source wss-venv/bin/activate
```

2. Run the service:
```bash
python dev_ws_service.py
```

The service will start on `http://0.0.0.0:8080`

## Deactivate

When done, deactivate the virtual environment:
```bash
deactivate
```


# Configuration

In order to use this server, you need to modify your configuration files


In console/.env.development

VITE_WEBSOCKET_URL='http://0.0.0.0:8080'



In system/env_config.py 

WEBSOCKET_CONNECTIONS='http://0.0.0.0:8080/send_to_client'



