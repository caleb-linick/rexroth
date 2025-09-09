import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import requests

# ctrlX CORE REST base; use https & skip verify if you're ok with controller cert
CORE_BASE = os.getenv("CORE_BASE", "https://localhost")
VERIFY_TLS = os.getenv("VERIFY_TLS", "false").lower() == "true"

# PLC symbol addresses
MOTOR_ENABLE = "plc/app/Application/sym/PLC_PRG/motorEnable"
MOTOR_SPEED  = "plc/app/Application/sym/PLC_PRG/motorSpeed"

app = FastAPI(title="Motor UI API")

static_dir = os.getenv("STATIC_DIR")
if static_dir and os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

class State(BaseModel):
    motorEnable: bool = Field(..., description="Enable/disable motor")
    motorSpeed: int   = Field(..., ge=0, le=10000, description="Motor speed (int)")

def _rest_headers(req: Request):
    auth = req.headers.get("authorization")
    if not auth:
        # When opened from the CORE Web UI, requests should include bearer/cookie auth.
        # If missing, the user probably browsed directly to the backend port.
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    return {"Authorization": auth, "Content-Type": "application/json"}

def _dl_node_url(node: str) -> str:
    # Data Layer REST write endpoint: /automation/api/v2/nodes/<path>
    return f"{CORE_BASE}/automation/api/v2/nodes/{node}"

@app.get("/api/state", response_model=State)
def get_state(request: Request):
    try:
        h = _rest_headers(request)
        # read enable
        r1 = requests.get(_dl_node_url(MOTOR_ENABLE), headers=h, verify=VERIFY_TLS)
        r1.raise_for_status()
        en = r1.json().get("value")
        # read speed
        r2 = requests.get(_dl_node_url(MOTOR_SPEED), headers=h, verify=VERIFY_TLS)
        r2.raise_for_status()
        sp = r2.json().get("value")
        return {"motorEnable": bool(en), "motorSpeed": int(sp)}
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"REST error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/state", response_model=State)
def set_state(body: State, request: Request):
    try:
        h = _rest_headers(request)
        # write enable
        w1 = requests.put(_dl_node_url(MOTOR_ENABLE), headers=h, json={"value": body.motorEnable}, verify=VERIFY_TLS)
        w1.raise_for_status()
        # write speed
        w2 = requests.put(_dl_node_url(MOTOR_SPEED), headers=h, json={"value": int(body.motorSpeed)}, verify=VERIFY_TLS)
        w2.raise_for_status()
        # read back
        return get_state(request)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"REST error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
