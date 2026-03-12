const form = document.getElementById("upload-form");
const statusText = document.getElementById("status");
const resultCard = document.getElementById("result-card");
const resultList = document.getElementById("result-list");
const historyBody = document.getElementById("history");

async function refreshHistory() {
  try {
    const resp = await fetch("/api/results?limit=10");
    const rows = await resp.json();

    historyBody.innerHTML = "";
    rows.forEach((item) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${item.id}</td>
        <td>${item.filename}</td>
        <td>${item.score}</td>
        <td>${item.confidence}</td>
        <td>${item.engine}</td>
        <td>${item.created_at}</td>
      `;
      historyBody.appendChild(tr);
    });
  } catch (e) {
    console.error("刷新历史失败", e);
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const fileInput = document.getElementById("video");
  if (!fileInput.files.length) {
    statusText.textContent = "请先选择视频文件。";
    return;
  }

  statusText.textContent = "正在评估，请稍候...";
  resultCard.hidden = true;

  const formData = new FormData();
  formData.append("video", fileInput.files[0]);

  try {
    const resp = await fetch("/api/evaluate", {
      method: "POST",
      body: formData,
      signal: AbortSignal.timeout(60000)
    });

    const payload = await resp.json();

    if (!resp.ok) {
      statusText.textContent = payload.error || "评估失败。";
      return;
    }

    resultCard.hidden = false;
    resultList.innerHTML = `
      <li>文件名：${payload.filename}</li>
      <li>评分（1-5）：${payload.score}</li>
      <li>置信度：${payload.confidence}</li>
      <li>抽帧数量：${payload.frame_count}</li>
      <li>视频时长（秒）：${payload.duration_sec}</li>
      <li>推理引擎：${payload.engine}</li>
    `;

    statusText.textContent = "评估完成！";
    refreshHistory();
  } catch (err) {
    if (err.name === 'TimeoutError') {
      statusText.textContent = "评估超时，请重试或更换较短视频";
    } else {
      statusText.textContent = `评估失败: ${err.message}`;
    }
    console.error(err);
  }
});

refreshHistory();