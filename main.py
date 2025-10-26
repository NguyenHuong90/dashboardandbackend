"""
DATN Smart Light Control System - Mock API Server
==================================================

FastAPI server để giao tiếp với Gateway ESP32
Hỗ trợ 3 endpoints chính:
1. POST /devices/register - Đăng ký gateway
2. POST /devices/report - Nhận dữ liệu từ nodes
3. GET /devices/{mac}/next-command - Gửi lệnh điều khiển

Version: 3.0
Date: October 2025
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles # cho phục vụ file tĩnh nếu cần
from typing import Dict, List
import time

app = FastAPI(title="DATN Smart Light Mock API")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="templates/static"), name="static")


# ============================================================
# DATABASE (In-memory storage)
# ============================================================

# Lưu thông tin gateway đã đăng ký
registered_gateways: Dict[str, dict] = {}

# Lưu dữ liệu mới nhất từ các nodes
# Format: {"ND_01": {"brightness": 80, "lux": 543, "current": 0.52, "timestamp": ...}}
node_status: Dict[str, dict] = {}

# Queue lệnh chờ gửi xuống gateway
# Format: {"GW_MAC": [{"deviceId": "ND_01", "brightness": 70}, ...]}
command_queue: Dict[str, List[dict]] = {}

# ============================================================
# 1. REGISTER DEVICE (POST /devices/register)
# ============================================================
@app.post("/devices/register")
async def register_device(request: Request):
    """
    Đăng ký gateway mới
    
    Request body:
    {
        "mac": "xx:xx:xx:xx:xx:xx"
    }
    
    Response:
    {
        "ok": true,
        "deviceId": "xx:xx:xx:xx:xx:xx"
    }
    """
    data = await request.json()
    mac = data.get("mac", "UNKNOWN")
    
    # Lưu thông tin gateway
    registered_gateways[mac] = {
        "mac": mac,
        "registered_at": time.time(),
        "last_seen": time.time()
    }
    
    # Khởi tạo command queue cho gateway này
    if mac not in command_queue:
        command_queue[mac] = []
    
    print("=" * 60)
    print(f"✅ GATEWAY REGISTERED: {mac}")
    print(f"   Total Gateways: {len(registered_gateways)}")
    print("=" * 60)
    
    return {
        "ok": True,
        "deviceId": mac
    }


# ============================================================
# 2. REPORT STATUS (POST /devices/report)
# ============================================================
@app.post("/devices/report")
async def report_status(request: Request):
    """
    Nhận dữ liệu status từ các nodes qua gateway
    
    Request body:
    {
        "gw_id": "GW_01",
        "devices": [
            {
                "deviceId": "ND_01",
                "brightness": 80,
                "lux": 543,
                "current": 0.52
            },
            {
                "deviceId": "ND_02",
                "brightness": 50,
                "lux": 612,
                "current": 0.47
            }
        ]
    }
    
    Response:
    {
        "ok": true
    }
    """
    data = await request.json()
    gw_id = data.get("gw_id", "UNKNOWN")
    devices = data.get("devices", [])
    
    print("\n" + "=" * 60)
    print(f"📊 STATUS REPORT from {gw_id}")
    print("=" * 60)
    
    # Lưu status của từng node
    for device in devices:
        device_id = device.get("deviceId", "UNKNOWN")
        node_status[device_id] = {
            "brightness": device.get("brightness", 0),
            "lux": device.get("lux", 0),
            "current": device.get("current", 0.0),
            "timestamp": time.time(),
            "gateway": gw_id
        }
        
        print(f"  📡 {device_id}:")
        print(f"     └─ Brightness: {device.get('brightness')}%")
        print(f"     └─ Light: {device.get('lux')} lux")
        print(f"     └─ Current: {device.get('current')} A")
    
    print("=" * 60 + "\n")
    
    return {
        "ok": True
    }


# ============================================================
# 3. GET NEXT COMMAND (GET /devices/{mac}/next-command)
# ============================================================
@app.get("/devices/{device_mac}/next-command")
async def get_command(device_mac: str):
    """
    Gateway lấy lệnh điều khiển từ server
    
    Response:
    {
        "ok": true,
        "devices": [
            {
                "deviceId": "ND_01",
                "brightness": 70
            }
        ]
    }
    """
    print("\n" + "-" * 60)
    print(f"🔍 GET COMMAND request from: {device_mac}")
    
    # Kiểm tra command queue
    if device_mac in command_queue and len(command_queue[device_mac]) > 0:
        # Có lệnh trong queue -> gửi xuống
        commands = command_queue[device_mac]
        command_queue[device_mac] = []  # Clear queue sau khi gửi
        
        print(f"   ✅ Sending {len(commands)} command(s) from queue")
        for cmd in commands:
            print(f"      └─ {cmd['deviceId']}: brightness={cmd['brightness']}%")
        print("-" * 60 + "\n")
        
        return {
            "ok": True,
            "devices": commands
        }
    else:
        # Không có lệnh -> trả về empty
        print("   ℹ️  No commands in queue")
        print("-" * 60 + "\n")
        
        return {
            "ok": True,
            "devices": []
        }


# ============================================================
# 🛠️ HELPER API (Dành cho testing/debugging)
# ============================================================

@app.post("/test/send-command")
async def test_send_command(request: Request):
    """
    Test endpoint để thêm lệnh vào queue
    
    Request body:
    {
        "gateway_mac": "xx:xx:xx:xx:xx:xx",
        "commands": [
            {"deviceId": "ND_01", "brightness": 80},
            {"deviceId": "ND_02", "brightness": 60}
        ]
    }
    """
    data = await request.json()
    gateway_mac = data.get("gateway_mac")
    commands = data.get("commands", [])
    
    if gateway_mac not in command_queue:
        command_queue[gateway_mac] = []
    
    command_queue[gateway_mac].extend(commands)
    
    print("\n" + "🎯" * 30)
    print(f"TEST COMMAND ADDED for {gateway_mac}:")
    for cmd in commands:
        print(f"  └─ {cmd['deviceId']}: {cmd['brightness']}%")
    print("🎯" * 30 + "\n")
    
    return {
        "ok": True,
        "message": f"Added {len(commands)} command(s) to queue"
    }


@app.get("/test/status")
async def test_status():
    """
    Xem toàn bộ trạng thái hệ thống
    """
    return {
        "ok": True,
        "registered_gateways": list(registered_gateways.keys()),
        "node_status": node_status,
        "command_queues": {k: len(v) for k, v in command_queue.items()}
    }

# ============================================================
# 🌐 DASHBOARD WEB UI
# ============================================================
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Trang web mini điều khiển brightness và hiển thị status
    """
    return templates.TemplateResponse("dashboard.html", {"request": request})

# ============================================================
# 🚀 STARTUP INFO
# ============================================================
@app.on_event("startup")
async def startup_event():
    print("\n" + "=" * 60)
    print("🚀 DATN Smart Light Mock API Server")
    print("=" * 60)
    print("📡 Endpoints:")
    print("   POST   /devices/register")
    print("   POST   /devices/report")
    print("   GET    /devices/{mac}/next-command")
    print("\n🛠️  Test Endpoints:")
    print("   POST   /test/send-command")
    print("   GET    /test/status")
    print("=" * 60 + "\n")
