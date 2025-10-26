const btn = document.getElementById("toggle-btn");
const statusText = document.getElementById("light-status");

let isOn = false;

btn.addEventListener("click", async () => {
  isOn = !isOn;
  const command = isOn ? "on" : "off";

  // Gửi lệnh đến FastAPI
  const res = await fetch(`/api/light?state=${command}`, { method: "POST" });
  if (res.ok) {
    statusText.innerHTML = `Trạng thái: <b>${isOn ? "Đang bật" : "Đang tắt"}</b>`;
    btn.textContent = isOn ? "Tắt đèn" : "Bật đèn";
  } else {
    alert("Không gửi được lệnh!");
  }
});
