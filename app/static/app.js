// app/static/app.js

// ==================== DOM 元素 ====================
const form = document.getElementById("upload-form");
const fileInput = document.getElementById("video");
const submitBtn = document.getElementById("submitBtn");
const statusText = document.getElementById("status");
const resultCard = document.getElementById("result-card");
const resultList = document.getElementById("result-list");
const historyBody = document.getElementById("history");
const dropZone = document.getElementById("dropZone");
const fileNameSpan = document.getElementById("fileName");
const uploadProgress = document.getElementById("uploadProgress");
const progressFill = document.getElementById("progressFill");
const progressText = document.getElementById("progressText");
const historyLimit = document.getElementById("historyLimit");
const historyInfo = document.getElementById("historyInfo");
const engineType = document.getElementById("engineType");
const modelStatus = document.getElementById("modelStatus");

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', () => {
    initializeDragAndDrop();
    updateModelStatus();
    refreshHistory();
    setupEventListeners();
});

// ==================== 拖拽上传功能 ====================
function initializeDragAndDrop() {
    if (!dropZone) return;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    function highlight() {
        dropZone.classList.add('dragover');
    }

    function unhighlight() {
        dropZone.classList.remove('dragover');
    }

    dropZone.addEventListener('drop', handleDrop, false);
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) {
        fileInput.files = files;
        updateFileName(files[0]);
    }
}

// ==================== 事件监听设置 ====================
function setupEventListeners() {
    // 文件选择变化
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            updateFileName(this.files[0]);
        });
    }

    // 历史记录数量变化
    if (historyLimit) {
        historyLimit.addEventListener('change', function() {
            refreshHistory(parseInt(this.value));
        });
    }

    // 导航栏激活状态
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // 滚动监听
    window.addEventListener('scroll', throttle(updateActiveNavLink, 100));
}

// ==================== 工具函数 ====================
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

function updateActiveNavLink() {
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.nav-link');

    let currentSection = '';
    sections.forEach(section => {
        const sectionTop = section.offsetTop - 100;
        const sectionHeight = section.clientHeight;
        if (scrollY >= sectionTop && scrollY < sectionTop + sectionHeight) {
            currentSection = section.getAttribute('id');
        }
    });

    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === `#${currentSection}`) {
            link.classList.add('active');
        }
    });
}

function updateFileName(file) {
    if (!fileNameSpan) return;

    if (file) {
        const size = (file.size / 1024 / 1024).toFixed(2);
        fileNameSpan.innerHTML = `<i class="fas fa-check-circle"></i> ${file.name} (${size} MB)`;
        fileNameSpan.style.display = 'inline-block';
    } else {
        fileNameSpan.innerHTML = '';
        fileNameSpan.style.display = 'none';
    }
}

function showStatus(message, type = 'info') {
    if (!statusText) return;

    statusText.textContent = message;
    statusText.className = `status-message ${type}`;
    statusText.style.display = 'block';

    // 3秒后自动隐藏成功消息
    if (type === 'success') {
        setTimeout(() => {
            statusText.style.display = 'none';
        }, 3000);
    }
}

function showProgress(show = true) {
    if (!uploadProgress) return;
    uploadProgress.style.display = show ? 'block' : 'none';
}

function updateProgress(percent, text) {
    if (progressFill) {
        progressFill.style.width = `${percent}%`;
    }
    if (progressText) {
        progressText.textContent = text || `正在上传... ${percent}%`;
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;

    // 今天
    if (diff < 24 * 60 * 60 * 1000 && date.getDate() === now.getDate()) {
        return `今天 ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
    }
    // 昨天
    if (diff < 48 * 60 * 60 * 1000 && date.getDate() === now.getDate() - 1) {
        return `昨天 ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
    }
    // 其他
    return `${date.getFullYear()}-${(date.getMonth()+1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`;
}

function getScoreBadgeClass(score) {
    if (score >= 4.5) return 'score-high';
    if (score >= 3.5) return 'score-medium';
    return 'score-low';
}

function getConfidenceColor(confidence) {
    if (confidence >= 0.8) return '#10b981';
    if (confidence >= 0.6) return '#f59e0b';
    return '#ef4444';
}

// ==================== 评分仪表盘 ====================
function updateScoreGauge(score) {
    const gaugeFill = document.getElementById('gaugeFill');
    const scoreDisplay = document.getElementById('scoreDisplay');

    if (!gaugeFill || !scoreDisplay) return;

    // 计算百分比 (1-5分映射到0-100%)
    const percentage = (score / 5) * 100;
    const circumference = 2 * Math.PI * 54; // 半径54
    const dashOffset = circumference * (1 - percentage / 100);

    gaugeFill.style.strokeDasharray = circumference;
    gaugeFill.style.strokeDashoffset = dashOffset;

    // 显示评分，保留3位小数
    scoreDisplay.textContent = score.toFixed(3);

    // 根据分数改变颜色
    if (score >= 4) {
        gaugeFill.style.stroke = '#10b981';
    } else if (score >= 3) {
        gaugeFill.style.stroke = '#f59e0b';
    } else {
        gaugeFill.style.stroke = '#ef4444';
    }
}

// ==================== 模型状态 ====================
async function updateModelStatus() {
    try {
        const response = await fetch('/api/health');
        if (!response.ok) throw new Error('获取模型状态失败');

        const data = await response.json();

        if (engineType) {
            engineType.textContent = data.engine === 'vit_fusion' ? 'ViT深度学习模型' : '启发式算法';
        }

        if (modelStatus) {
            modelStatus.className = `status-indicator ${data.model_exists ? 'active' : 'inactive'}`;
            modelStatus.title = data.model_exists ? '模型已加载' : '使用备用引擎';
        }
    } catch (error) {
        console.error('获取模型状态失败:', error);
        if (engineType) engineType.textContent = '未知';
    }
}

// ==================== 结果显示 ====================
function displayResult(payload) {
    if (!resultCard || !resultList) return;

    updateScoreGauge(payload.score);

    resultList.innerHTML = `
        <div class="detail-item">
            <i class="fas fa-file-video"></i>
            <div class="detail-content">
                <span class="detail-label">文件名</span>
                <span class="detail-value">${escapeHtml(payload.filename)}</span>
            </div>
        </div>
        <div class="detail-item">
            <i class="fas fa-star"></i>
            <div class="detail-content">
                <span class="detail-label">综合评分</span>
                <span class="detail-value">${payload.score.toFixed(3)} / 5.0</span>
            </div>
        </div>
        <div class="detail-item">
            <i class="fas fa-chart-bar"></i>
            <div class="detail-content">
                <span class="detail-label">置信度</span>
                <span class="detail-value" style="color: ${getConfidenceColor(payload.confidence)}">
                    ${(payload.confidence * 100).toFixed(1)}%
                </span>
            </div>
        </div>
        <div class="detail-item">
            <i class="fas fa-film"></i>
            <div class="detail-content">
                <span class="detail-label">抽帧数量</span>
                <span class="detail-value">${payload.frame_count} 帧</span>
            </div>
        </div>
        <div class="detail-item">
            <i class="fas fa-clock"></i>
            <div class="detail-content">
                <span class="detail-label">视频时长</span>
                <span class="detail-value">${payload.duration_sec.toFixed(3)} 秒</span>
            </div>
        </div>
        <div class="detail-item">
            <i class="fas fa-microchip"></i>
            <div class="detail-content">
                <span class="detail-label">推理引擎</span>
                <span class="detail-value">${payload.engine === 'vit_fusion' ? 'ViT深度学习模型' : '启发式算法'}</span>
            </div>
        </div>
    `;

    resultCard.hidden = false;
    resultCard.scrollIntoView({ behavior: 'smooth' });
}

// HTML转义防止XSS
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// ==================== 历史记录 ====================
async function refreshHistory(limit = 10) {
    if (!historyBody) return;

    try {
        // 显示加载状态
        historyBody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 2rem;">
                    <div class="loading"></div>
                    <p style="margin-top: 1rem; color: var(--text-secondary);">加载中...</p>
                </td>
            </tr>
        `;

        const response = await fetch(`/api/results?limit=${limit}`);
        if (!response.ok) throw new Error('获取历史记录失败');

        const rows = await response.json();

        if (rows.length === 0) {
            historyBody.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align: center; padding: 2rem; color: var(--text-secondary);">
                        <i class="fas fa-inbox" style="font-size: 3rem; opacity: 0.5; margin-bottom: 1rem;"></i>
                        <p>暂无评估记录</p>
                    </td>
                </tr>
            `;
            if (historyInfo) historyInfo.textContent = '共 0 条记录';
            return;
        }

        historyBody.innerHTML = '';
        rows.forEach((item) => {
            const tr = document.createElement('tr');
            const scoreClass = getScoreBadgeClass(item.score);
            const confidencePercent = (item.confidence * 100).toFixed(1);
            const formattedDate = formatDate(item.created_at);

            tr.innerHTML = `
                <td><span class="id-badge">#${item.id}</span></td>
                <td class="filename-cell" title="${escapeHtml(item.filename)}">
                    <i class="fas fa-file-video"></i>
                    ${escapeHtml(truncateFilename(item.filename, 20))}
                </td>
                <td>
                    <span class="score-badge ${scoreClass}">
                        ${item.score.toFixed(3)}
                    </span>
                </td>
                <td>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: ${confidencePercent}%; background-color: ${getConfidenceColor(item.confidence)}"></div>
                        <span>${confidencePercent}%</span>
                    </div>
                </td>
                <td>
                    <span class="engine-badge ${item.engine}">
                        ${item.engine === 'vit_fusion' ? 'ViT' : '启发式'}
                    </span>
                </td>
                <td class="date-cell">
                    <i class="far fa-calendar-alt"></i>
                    ${formattedDate}
                </td>
                <td>
                    <button class="action-btn" onclick="viewResult(${item.id})" title="查看详情">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="action-btn" onclick="downloadResult(${item.id})" title="下载报告">
                        <i class="fas fa-download"></i>
                    </button>
                </td>
            `;
            historyBody.appendChild(tr);
        });

        if (historyInfo) {
            historyInfo.textContent = `共 ${rows.length} 条记录`;
        }

    } catch (e) {
        console.error("刷新历史失败", e);
        historyBody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 2rem; color: var(--danger-color);">
                    <i class="fas fa-exclamation-triangle" style="font-size: 2rem; margin-bottom: 1rem;"></i>
                    <p>加载失败: ${e.message}</p>
                    <button onclick="refreshHistory()" class="btn-secondary" style="margin-top: 1rem;">
                        <i class="fas fa-sync-alt"></i> 重试
                    </button>
                </td>
            </tr>
        `;
    }
}

function truncateFilename(filename, maxLength) {
    if (filename.length <= maxLength) return filename;
    const ext = filename.split('.').pop();
    const name = filename.substring(0, filename.lastIndexOf('.'));
    const truncatedName = name.substring(0, maxLength - 3 - ext.length);
    return `${truncatedName}...${ext}`;
}

// ==================== 表单提交 ====================
form.addEventListener("submit", async (e) => {
    e.preventDefault();

    if (!fileInput.files.length) {
        showStatus("请先选择视频文件。", "error");
        return;
    }

    const file = fileInput.files[0];

    // 检查文件大小 (300MB)
    if (file.size > 300 * 1024 * 1024) {
        showStatus("文件大小不能超过300MB", "error");
        return;
    }

    // 检查文件类型
    const validTypes = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-matroska'];
    if (!validTypes.includes(file.type) && !file.name.match(/\.(mp4|avi|mov|mkv)$/i)) {
        showStatus("只支持 MP4、AVI、MOV、MKV 格式", "error");
        return;
    }

    showStatus("正在准备上传...", "info");
    resultCard.hidden = true;
    submitBtn.disabled = true;
    showProgress(true);
    updateProgress(0, "准备上传...");

    const formData = new FormData();
    formData.append("video", file);

    try {
        // 使用 XMLHttpRequest 来监控上传进度
        const xhr = new XMLHttpRequest();

        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percent = (e.loaded / e.total) * 100;
                updateProgress(percent, `上传中... ${Math.round(percent)}%`);
            }
        });

        const response = await new Promise((resolve, reject) => {
            xhr.open('POST', '/api/evaluate');
            xhr.timeout = 60000; // 60秒超时

            xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve(new Response(xhr.response, {
                        status: xhr.status,
                        statusText: xhr.statusText,
                        headers: new Headers({
                            'Content-Type': xhr.getResponseHeader('Content-Type') || 'application/json'
                        })
                    }));
                } else {
                    reject(new Error(`HTTP ${xhr.status}: ${xhr.statusText}`));
                }
            };

            xhr.onerror = () => reject(new Error('网络错误'));
            xhr.ontimeout = () => reject(new Error('上传超时'));

            xhr.send(formData);
        });

        showProgress(false);
        updateProgress(100, "上传完成，处理中...");

        const payload = await parseJsonResponse(response);

        if (!response.ok) {
            showStatus(payload.error || "评估失败。", "error");
            return;
        }

        displayResult(payload);
        showStatus("评估完成！", "success");
        refreshHistory(historyLimit ? parseInt(historyLimit.value) : 10);

        // 清空文件选择
        fileInput.value = '';
        updateFileName(null);

    } catch (err) {
        showProgress(false);

        let errorMessage = "评估失败";
        if (err.name === 'TimeoutError' || err.message.includes('超时')) {
            errorMessage = "评估超时，请重试或更换较短视频";
        } else if (err.message.includes('网络错误')) {
            errorMessage = "网络连接失败，请检查网络";
        } else {
            errorMessage = `评估失败: ${err.message}`;
        }

        showStatus(errorMessage, "error");
        console.error(err);
    } finally {
        submitBtn.disabled = false;
    }
});

// ==================== 响应解析 ====================
async function parseJsonResponse(resp) {
    const contentType = resp.headers.get("content-type") || "";

    if (contentType.includes("application/json")) {
        return await resp.json();
    }

    const text = await resp.text();
    const compactText = text.replace(/\s+/g, " ").trim();
    const errorText = compactText.slice(0, 120) || "未知错误";
    throw new Error(`服务返回了非 JSON 响应: ${errorText}`);
}

// ==================== 操作函数 ====================
async function viewResult(id) {
    try {
        const response = await fetch(`/api/results/${id}`);
        if (!response.ok) throw new Error('获取详情失败');

        const result = await response.json();
        displayResult(result);

        // 高亮对应的行
        const rows = document.querySelectorAll('#history tr');
        rows.forEach(row => {
            row.style.backgroundColor = '';
            if (row.querySelector(`.id-badge`)?.textContent === `#${id}`) {
                row.style.backgroundColor = 'rgba(79, 70, 229, 0.1)';
                setTimeout(() => {
                    row.style.backgroundColor = '';
                }, 2000);
            }
        });

    } catch (error) {
        showStatus(`查看详情失败: ${error.message}`, "error");
    }
}

async function downloadResult(id) {
    try {
        const response = await fetch(`/api/results/${id}`);
        if (!response.ok) throw new Error('获取数据失败');

        const result = await response.json();

        // 创建下载内容，使用3位小数
        const content = `视频质量评估报告
==============================
评估ID: #${result.id}
文件名: ${result.filename}
评分: ${result.score.toFixed(3)}/5
置信度: ${(result.confidence * 100).toFixed(1)}%
视频时长: ${result.duration_sec.toFixed(3)}秒
抽帧数量: ${result.frame_count}帧
推理引擎: ${result.engine === 'vit_fusion' ? 'ViT深度学习模型' : '启发式算法'}
评估时间: ${new Date(result.created_at).toLocaleString('zh-CN')}
==============================
报告生成时间: ${new Date().toLocaleString('zh-CN')}`;

        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `评估报告_${result.filename}_${result.id}.txt`;
        a.click();
        URL.revokeObjectURL(url);

        showStatus('报告下载成功', 'success');

    } catch (error) {
        showStatus(`下载失败: ${error.message}`, "error");
    }
}

function shareResult() {
    const result = document.getElementById('result-list')?.innerText;
    if (!result) {
        showStatus('没有可分享的结果', 'error');
        return;
    }

    // 复制到剪贴板
    navigator.clipboard.writeText(result).then(() => {
        showStatus('结果已复制到剪贴板', 'success');
    }).catch(() => {
        showStatus('复制失败', 'error');
    });
}

function downloadReport() {
    const resultItems = document.querySelectorAll('.detail-item');
    if (resultItems.length === 0) {
        showStatus('没有可下载的报告', 'error');
        return;
    }

    let content = '视频质量评估报告\n';
    content += '='.repeat(30) + '\n';

    resultItems.forEach(item => {
        const label = item.querySelector('.detail-label')?.textContent || '';
        const value = item.querySelector('.detail-value')?.textContent || '';
        content += `${label}: ${value}\n`;
    });

    content += '='.repeat(30) + '\n';
    content += `生成时间: ${new Date().toLocaleString('zh-CN')}`;

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `评估报告_${new Date().getTime()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
}

// ==================== 初始化历史记录 ====================
refreshHistory();