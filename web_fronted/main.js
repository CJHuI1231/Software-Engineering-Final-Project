let pdfDoc = null;
let currentPage = 1;
let totalPages = 1;
let scale = 1.0;
let extractedText = "";
let fileId = null;

// API基础URL - 根据环境自动检测
// 如果通过nginx代理访问，使用相对路径；否则使用绝对路径
const API_BASE_URL = window.location.port === '8080' || window.location.port === ''
    ? "/api"  // Docker环境或生产环境，通过nginx代理
    : "http://localhost:8000/api";  // 本地开发环境

const canvas = document.getElementById("pdfCanvas");
const ctx = canvas.getContext("2d");
const fileInput = document.getElementById("pdfFile");
const fileName = document.getElementById("fileName");

// 文件上传处理
fileInput.addEventListener("change", async () => {
    if (fileInput.files.length > 0) {
        fileName.textContent = fileInput.files[0].name;
    }
    
    const file = fileInput.files[0];
    if (!file) return;

    // 显示加载状态
    showLoading("正在处理PDF文件...");
    
    try {
        // 上传PDF到后端
        const response = await uploadPdfToBackend(file);
        
        if (response.status === "success") {
            extractedText = response.text;
            fileId = response.file_id;
            
            // 显示PDF
            await displayPdf(file);
            
            // 隐藏加载状态
            hideLoading();
            
            // 显示提示信息
            showMessage(`PDF处理完成，共${response.pages_processed}页，耗时${response.processing_time}秒`, "success");
        } else {
            throw new Error("PDF处理失败");
        }
    } catch (error) {
        console.error("PDF处理错误:", error);
        hideLoading();
        showMessage(`PDF处理失败: ${error.message}`, "error");
    }
});

// 上传PDF到后端
async function uploadPdfToBackend(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE_URL}/pdf/upload`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            // 尝试解析错误响应
            const contentType = response.headers.get('content-type');
            let errorMessage = `文件上传失败 (状态码: ${response.status})`;

            if (contentType && contentType.includes('application/json')) {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
            } else {
                // 如果不是JSON，获取文本响应
                const text = await response.text();
                if (text && !text.startsWith('<')) {
                    errorMessage = text;
                }
            }

            throw new Error(errorMessage);
        }

        return await response.json();
    } catch (error) {
        console.error("上传错误:", error);
        throw error;
    }
}

// 显示PDF
async function displayPdf(file) {
    const fileReader = new FileReader();
    
    return new Promise((resolve, reject) => {
        fileReader.onload = function() {
            const typedarray = new Uint8Array(this.result);
            
            pdfjsLib.getDocument(typedarray).promise.then(pdf => {
                pdfDoc = pdf;
                totalPages = pdf.numPages;
                currentPage = 1;
                renderPage();
                resolve();
            }).catch(reject);
        };
        
        fileReader.onerror = reject;
        fileReader.readAsArrayBuffer(file);
    });
}

// Tab 切换
const tabs = document.querySelectorAll(".tab");
const panels = document.querySelectorAll(".tab-panel");

tabs.forEach(tab => {
  tab.addEventListener("click", () => {
    const target = tab.dataset.tab;

    tabs.forEach(t => t.classList.remove("active"));
    tab.classList.add("active");

    panels.forEach(panel => {
      panel.classList.toggle("active", panel.id === target);
    });
  });
});

function renderPage() {
  pdfDoc.getPage(currentPage).then(page => {

    const dpr = window.devicePixelRatio || 1;

    const viewport = page.getViewport({ scale: 1 });

    canvas.style.width = `${viewport.width}px`;
    canvas.style.height = `${viewport.height}px`;

    canvas.width = Math.floor(viewport.width * dpr);
    canvas.height = Math.floor(viewport.height * dpr);

    // 把 context 放大到对应 DPR
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    page.render({
      canvasContext: ctx,
      viewport
    });

    document.getElementById("pageInfo").textContent =
      `${currentPage} / ${totalPages}`;
  });
}

document.getElementById("prevPage").onclick = () => {
  if (currentPage > 1) {
    currentPage--;
    renderPage();
  }
};

document.getElementById("nextPage").onclick = () => {
  if (currentPage < totalPages) {
    currentPage++;
    renderPage();
  }
};

document.getElementById("zoomIn").onclick = () => {
  scale = Math.min(scale + 0.1, 3);
  applyZoom();
};

document.getElementById("zoomOut").onclick = () => {
  scale = Math.max(scale - 0.1, 0.5);
  applyZoom();
};

function applyZoom() {
  document.getElementById("pdfInner").style.transform =`scale(${scale})`;
  canvas.style.transformOrigin = "top center";

  document.getElementById("zoomLevel").textContent =
    `${Math.round(scale * 100)}%`;
}

// 生成摘要按钮点击事件
document.getElementById("actionBtn").addEventListener("click", async () => {
    if (!extractedText) {
        showMessage("请先上传PDF文件", "warning");
        return;
    }
    
    showLoading("正在生成摘要...");
    
    try {
        const response = await generateSummary(extractedText);
        
        if (response.status === "success") {
            const outputPanel = document.getElementById("output");
            
            // 清除原有内容
            outputPanel.innerHTML = `
                <div class="result-container">
                    <h3>摘要结果</h3>
                    <div class="result-info">
                        <p>生成方法: ${response.method_used}</p>
                        <p>处理时间: ${response.processing_time}秒</p>
                        <p>质量评分: F1=${response.quality_metrics.f1_score.toFixed(2)}</p>
                    </div>
                    <div class="result-content">
                        <p>${response.summary}</p>
                    </div>
                </div>
            `;
            
            showMessage("摘要生成成功", "success");
        } else {
            throw new Error("摘要生成失败");
        }
    } catch (error) {
        console.error("摘要生成错误:", error);
        showMessage(`摘要生成失败: ${error.message}`, "error");
    } finally {
        hideLoading();
    }
});

// 生成摘要API调用
async function generateSummary(text) {
    try {
        const response = await fetch(`${API_BASE_URL}/pdf/summary`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: text,
                method: "auto",
                max_length: 150,
                min_length: 30
            }),
        });

        if (!response.ok) {
            // 尝试解析错误响应
            const contentType = response.headers.get('content-type');
            let errorMessage = `摘要生成失败 (状态码: ${response.status})`;

            if (contentType && contentType.includes('application/json')) {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
            } else {
                // 如果不是JSON，获取文本响应
                const text = await response.text();
                if (text && !text.startsWith('<')) {
                    errorMessage = text;
                }
            }

            throw new Error(errorMessage);
        }

        return await response.json();
    } catch (error) {
        console.error("摘要生成错误:", error);
        throw error;
    }
}

// 生成知识图谱按钮点击事件
document.getElementById("actionBtnGraph").addEventListener("click", async () => {
    if (!extractedText) {
        showMessage("请先上传PDF文件", "warning");
        return;
    }
    
    showLoading("正在生成知识图谱...");
    
    try {
        const response = await generateKnowledgeGraph(extractedText);
        
        if (response.status === "success") {
            const graphPanel = document.getElementById("graph");
            
            // 清除原有内容
            graphPanel.innerHTML = `
                <div class="result-container">
                    <h3>知识图谱</h3>
                    <div class="result-info">
                        <p>实体数量: ${response.entity_count}</p>
                        <p>关系数量: ${response.relation_count}</p>
                        <p>处理时间: ${response.processing_time}秒</p>
                    </div>
                    <div class="graph-container" id="graphContainer">
                        <canvas id="graphCanvas" width="800" height="600"></canvas>
                    </div>
                </div>
            `;
            
            // 绘制知识图谱
            drawKnowledgeGraph(response.nodes, response.edges);
            
            showMessage("知识图谱生成成功", "success");
        } else {
            throw new Error("知识图谱生成失败");
        }
    } catch (error) {
        console.error("知识图谱生成错误:", error);
        showMessage(`知识图谱生成失败: ${error.message}`, "error");
    } finally {
        hideLoading();
    }
});

// 生成知识图谱API调用
async function generateKnowledgeGraph(text) {
    try {
        const response = await fetch(`${API_BASE_URL}/pdf/knowledge_graph`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: text,
                entity_types: ["PERSON", "ORG", "DATE", "LOCATION"],
                relation_extraction: true
            }),
        });

        if (!response.ok) {
            // 尝试解析错误响应
            const contentType = response.headers.get('content-type');
            let errorMessage = `知识图谱生成失败 (状态码: ${response.status})`;

            if (contentType && contentType.includes('application/json')) {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
            } else {
                // 如果不是JSON，获取文本响应
                const text = await response.text();
                if (text && !text.startsWith('<')) {
                    errorMessage = text;
                }
            }

            throw new Error(errorMessage);
        }

        return await response.json();
    } catch (error) {
        console.error("知识图谱生成错误:", error);
        throw error;
    }
}

// 绘制知识图谱
function drawKnowledgeGraph(nodes, edges) {
    const canvas = document.getElementById("graphCanvas");
    if (!canvas) return;
    
    const ctx = canvas.getContext("2d");
    const width = canvas.width;
    const height = canvas.height;
    
    // 清空画布
    ctx.clearRect(0, 0, width, height);
    
    // 设置节点位置（简单的圆形布局）
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) * 0.4;
    
    // 为节点分配位置
    nodes.forEach((node, i) => {
        const angle = (i / nodes.length) * Math.PI * 2;
        node.x = centerX + Math.cos(angle) * radius;
        node.y = centerY + Math.sin(angle) * radius;
    });
    
    // 绘制边
    ctx.strokeStyle = "#ccc";
    ctx.lineWidth = 1;
    
    edges.forEach(edge => {
        const sourceNode = nodes.find(n => n.id === edge.source);
        const targetNode = nodes.find(n => n.id === edge.target);
        
        if (sourceNode && targetNode) {
            ctx.beginPath();
            ctx.moveTo(sourceNode.x, sourceNode.y);
            ctx.lineTo(targetNode.x, targetNode.y);
            ctx.stroke();
        }
    });
    
    // 绘制节点
    nodes.forEach(node => {
        ctx.beginPath();
        ctx.arc(node.x, node.y, 20, 0, Math.PI * 2);
        ctx.fillStyle = getNodeColor(node.type);
        ctx.fill();
        ctx.strokeStyle = "#333";
        ctx.lineWidth = 2;
        ctx.stroke();
        
        // 绘制节点标签
        ctx.fillStyle = "#000";
        ctx.font = "12px Arial";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        
        // 如果标签太长，截断并添加省略号
        let label = node.label;
        if (label.length > 8) {
            label = label.substring(0, 7) + "...";
        }
        
        ctx.fillText(label, node.x, node.y);
    });
}

// 获取节点颜色
function getNodeColor(type) {
    const colors = {
        "PERSON": "#FF9999",
        "ORG": "#99CCFF",
        "DATE": "#99FF99",
        "LOCATION": "#FFFF99",
        "default": "#DDDDDD"
    };
    
    return colors[type] || colors.default;
}

// 显示加载状态
function showLoading(message) {
    // 创建加载遮罩
    const loadingOverlay = document.createElement('div');
    loadingOverlay.id = 'loadingOverlay';
    loadingOverlay.className = 'loading-overlay';
    
    // 创建加载消息
    const loadingMessage = document.createElement('div');
    loadingMessage.className = 'loading-message';
    loadingMessage.textContent = message;
    
    loadingOverlay.appendChild(loadingMessage);
    document.body.appendChild(loadingOverlay);
}

// 隐藏加载状态
function hideLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.remove();
    }
}

// 显示消息
function showMessage(message, type = "info") {
    // 创建消息元素
    const messageElement = document.createElement('div');
    messageElement.className = `message message-${type}`;
    messageElement.textContent = message;
    
    // 添加到页面
    document.body.appendChild(messageElement);
    
    // 3秒后自动移除
    setTimeout(() => {
        if (messageElement.parentNode) {
            messageElement.parentNode.removeChild(messageElement);
        }
    }, 3000);
}