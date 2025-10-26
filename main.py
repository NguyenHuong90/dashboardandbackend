from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="templates/static"), name="static")

@app.get("/lightcontrol", response_class=HTMLResponse)
async def lightcontrol(request: Request):
    return templates.TemplateResponse("lightcontrol.html", {"request": request, "title": "Light Control"})

@app.post("/api/light")
async def control_light(state: str):
    print(f"[API] Đèn: {state.upper()}")
    # ở đây bạn có thể gửi lệnh MQTT hoặc điều khiển thiết bị thật
    return {"status": "ok", "state": state}
