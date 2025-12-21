pdfjsLib.GlobalWorkerOptions.workerSrc =
  "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";

const fileInput = document.getElementById("pdf-upload");
const fileName = document.getElementById("file-name");

const searchTerm = document.getElementById("search-term");
const caseSensitive = document.getElementById("case-sensitive");
const debugModeCheckbox = document.getElementById("debug-mode");

const searchBtn = document.getElementById("search-btn");
const clearBtn = document.getElementById("clear-btn");
const downloadBtn = document.getElementById("download-btn");

const originalContainer = document.getElementById("original-pdf-container");
const highlightedContainer = document.getElementById("highlighted-pdf-container");

const prevPageOriginal = document.getElementById("prev-page-original");
const nextPageOriginal = document.getElementById("next-page-original");
const pageNumOriginal = document.getElementById("page-num-original");

const prevPageHighlighted = document.getElementById("prev-page-highlighted");
const nextPageHighlighted = document.getElementById("next-page-highlighted");
const pageNumHighlighted = document.getElementById("page-num-highlighted");

const searchNavigation = document.getElementById("search-navigation");
const prevResultBtn = document.getElementById("prev-result");
const nextResultBtn = document.getElementById("next-result");
const resultCountSpan = document.getElementById("result-count");

const loadingOverlay = document.getElementById("loading");

let originalPdfDoc = null;          // pdf.js doc
let highlightedPdfDoc = null;       // pdf.js doc（高亮后，生成的 PDF 字节重新 load）
let originalPdfBytes = null;        // ArrayBuffer，生成高亮 PDF 时用

let originalPageNum = 1;
let highlightedPageNum = 1;

let scale = 1.35;                   // 你可以调整，但建议保持一致
let pageRendering = false;

let searchResults = [];             // [{ pageNum, matches:[{text,bboxPdf,bboxView?}] }]
let totalResults = 0;
let currentResultIndex = 0;

let lastSearchTerm = "";
let lastCaseSensitive = false;


searchBtn.disabled = true;
clearBtn.disabled = true;
downloadBtn.disabled = true;
prevPageOriginal.disabled = true;
nextPageOriginal.disabled = true;
prevPageHighlighted.disabled = true;
nextPageHighlighted.disabled = true;
searchNavigation.style.display = "none";
pageNumOriginal.textContent = "0/0";
pageNumHighlighted.textContent = "0/0";


fileInput.addEventListener("change", handleFileSelect);
searchBtn.addEventListener("click", searchAndHighlight);
clearBtn.addEventListener("click", clearHighlights);
downloadBtn.addEventListener("click", downloadHighlightedPdf);

prevPageOriginal.addEventListener("click", () => showPage(originalPageNum - 1, "original"));
nextPageOriginal.addEventListener("click", () => showPage(originalPageNum + 1, "original"));
prevPageHighlighted.addEventListener("click", () => showPage(highlightedPageNum - 1, "highlighted"));
nextPageHighlighted.addEventListener("click", () => showPage(highlightedPageNum + 1, "highlighted"));

prevResultBtn.addEventListener("click", navigateToPreviousResult);
nextResultBtn.addEventListener("click", navigateToNextResult);

document.querySelectorAll('input[name="highlight-mode"]').forEach(radio => {
  radio.addEventListener("change", async () => {
    // overlay：回到原始页并叠加高亮
    if (radio.value === "overlay" && searchResults.length > 0) {
      await showPage(originalPageNum, "original");
      applyHighlights(originalPageNum, getMatchIndexOnPage(originalPageNum, currentResultIndex));
      downloadBtn.disabled = true;
    }
    // new-pdf：如果已有高亮 PDF，展示之
    if (radio.value === "new-pdf" && highlightedPdfDoc) {
      await showPage(highlightedPageNum, "highlighted");
      downloadBtn.disabled = false;
    }
  });
});


function showLoading(show) {
    if (!loadingOverlay) return;
    loadingOverlay.style.display = show ? "flex" : "none";
}

function setPlaceholder(container, text) {
    container.innerHTML = `<div class="placeholder">${text}</div>`;
}

function clearContainer(container) {
    container.innerHTML = "";
}


async function handleFileSelect(e) {
    const file = e.target.files?.[0];
    if (!file || file.type !== "application/pdf") {
        alert("请选择有效的PDF文件");
        return;
  }

    fileName.textContent = file.name;
    showLoading(true);

    try {
        const buffer = await file.arrayBuffer();
        const pdfjsBytes = buffer.slice(0);
        originalPdfBytes = buffer.slice(0);

        const loadingTask = pdfjsLib.getDocument({ data: pdfjsBytes });
        originalPdfDoc = await loadingTask.promise;
        originalPdfDoc = await loadingTask.promise;

        // 重置状态
        highlightedPdfDoc = null;
        originalPageNum = 1;
        highlightedPageNum = 1;

        searchResults = [];
        totalResults = 0;
        currentResultIndex = 0;
        lastSearchTerm = "";
        lastCaseSensitive = false;

        // UI
        searchBtn.disabled = false;
        clearBtn.disabled = true;
        downloadBtn.disabled = true;
        searchNavigation.style.display = "none";
        resultCountSpan.textContent = "0/0";

        // 渲染第一页（原始）
        await renderPage(originalPageNum, "original");
        updatePageInfo("original");

        // 高亮窗口占位
        setPlaceholder(highlightedContainer, "请先检索并高亮文本");
        updatePageInfo("highlighted");
    } catch (err) {
        console.error("加载PDF时出错:", err);
        alert("加载PDF文件时出错，请重试");
    } finally {
        showLoading(false);
    }
}


async function renderPage(num, type) {
    const pdfDoc = type === "original" ? originalPdfDoc : highlightedPdfDoc;
    const container = type === "original" ? originalContainer : highlightedContainer;

    if (!pdfDoc) return;

    pageRendering = true;

    try {
        const page = await pdfDoc.getPage(num);
        const viewport = page.getViewport({ scale });

        // 清空容器
        clearContainer(container);

        // 容器尺寸与定位（关键：overlay 必须相对它定位）
        container.style.position = "relative";
        container.style.width = `${viewport.width}px`;
        container.style.height = `${viewport.height}px`;

        // canvas
        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d", { alpha: false });

        const dpr = window.devicePixelRatio || 1;
        canvas.width = Math.floor(viewport.width * dpr);
        canvas.height = Math.floor(viewport.height * dpr);
        canvas.style.width = `${viewport.width}px`;
        canvas.style.height = `${viewport.height}px`;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

        container.appendChild(canvas);

        await page.render({
        canvasContext: ctx,
        viewport,
        }).promise;

        // overlay 模式下：在原始窗口可叠加高亮层
        if (type === "original") {
        ensureOverlayLayer(container, viewport.width, viewport.height);
        }
    } finally {
        pageRendering = false;
    }
    
}

function ensureOverlayLayer(container, w, h) {
    let layer = container.querySelector(".overlay-layer");
    if (!layer) {
        layer = document.createElement("div");
        layer.className = "overlay-layer";
        layer.style.position = "absolute";
        layer.style.left = "0";
        layer.style.top = "0";
        layer.style.width = `${w}px`;
        layer.style.height = `${h}px`;
        layer.style.pointerEvents = "none";
        layer.style.zIndex = "20";
        container.appendChild(layer);
    } else {
        layer.style.width = `${w}px`;
        layer.style.height = `${h}px`;
        layer.innerHTML = "";
    }
}


async function showPage(num, type) {
    const pdfDoc = type === "original" ? originalPdfDoc : highlightedPdfDoc;
    if (!pdfDoc) return;

    const total = pdfDoc.numPages;
    if (num < 1 || num > total) return;

    if (type === "original") originalPageNum = num;
    else highlightedPageNum = num;

    await renderPage(num, type);
    updatePageInfo(type);

    // overlay 高亮：只在原始窗口叠加
    const highlightMode = getHighlightMode();
    if (type === "original" && highlightMode === "overlay" && searchResults.length > 0) {
        const activeIndexOnThisPage = getMatchIndexOnPage(num, currentResultIndex);
        applyHighlights(num, activeIndexOnThisPage);
    }
}


function updatePageInfo(type) {
    if (type === "original") {
        if (!originalPdfDoc) {
        pageNumOriginal.textContent = "0/0";
        prevPageOriginal.disabled = true;
        nextPageOriginal.disabled = true;
        return;
        }
        pageNumOriginal.textContent = `${originalPageNum}/${originalPdfDoc.numPages}`;
        prevPageOriginal.disabled = originalPageNum <= 1;
        nextPageOriginal.disabled = originalPageNum >= originalPdfDoc.numPages;
    } else {
        if (!highlightedPdfDoc) {
        pageNumHighlighted.textContent = "0/0";
        prevPageHighlighted.disabled = true;
        nextPageHighlighted.disabled = true;
        return;
        }
        pageNumHighlighted.textContent = `${highlightedPageNum}/${highlightedPdfDoc.numPages}`;
        prevPageHighlighted.disabled = highlightedPageNum <= 1;
        nextPageHighlighted.disabled = highlightedPageNum >= highlightedPdfDoc.numPages;
    }
}


async function searchAndHighlight() {
    if (!originalPdfDoc) {
        alert("请先上传PDF文件");
        return;
    }

    const term = (searchTerm.value || "").trim();
    if (!term) {
        alert("请输入要检索的词语");
        return;
    }

    showLoading(true);

    try {
        // 保存本次搜索参数
        lastSearchTerm = term;
        lastCaseSensitive = !!caseSensitive.checked;

        // 重置结果
        searchResults = [];
        totalResults = 0;
        currentResultIndex = 0;

        const cs = !!caseSensitive.checked;

        // 逐页提取并匹配
        for (let pageNum = 1; pageNum <= originalPdfDoc.numPages; pageNum++) {
        const page = await originalPdfDoc.getPage(pageNum);
        const textContent = await page.getTextContent();

        const matches = findMatchesOnPage(textContent, term, cs, page);
        if (matches.length > 0) {
            searchResults.push({ pageNum, matches });
            totalResults += matches.length;
        }
        }

        if (searchResults.length === 0) {
        alert("未找到匹配的文本。提示：某些PDF可能包含扫描图像而非可搜索文本。");
        searchNavigation.style.display = "none";
        clearBtn.disabled = true;
        downloadBtn.disabled = true;
        return;
        }

        // 显示搜索结果导航
        searchNavigation.style.display = "flex";
        resultCountSpan.textContent = `1/${totalResults}`;
        prevResultBtn.disabled = totalResults <= 1;
        nextResultBtn.disabled = totalResults <= 1;

        // 启用清除按钮
        clearBtn.disabled = false;

        // 根据模式执行
        const highlightMode = getHighlightMode();

        if (highlightMode === "overlay") {
        // 直接在原始PDF上高亮显示
        downloadBtn.disabled = true; // overlay 模式不下载
        await showPage(originalPageNum, "original");
        applyHighlights(originalPageNum, getMatchIndexOnPage(originalPageNum, currentResultIndex));
        } else {
        // 生成高亮PDF
        await createHighlightedPdf();
        highlightedPageNum = 1;
        await showPage(1, "highlighted");
        downloadBtn.disabled = false;
        }
    } catch (err) {
        console.error("搜索和高亮文本时出错:", err);
        alert("处理文本时出错，请重试。错误详情: " + err.message);
    } finally {
        showLoading(false);
    }
}


function findMatchesOnPage(textContent, term, caseSensitiveFlag, page) {
    const items = textContent.items || [];
    const matches = [];

    const needle = caseSensitiveFlag ? term : term.toLowerCase();

    for (const item of items) {
        const raw = item.str ?? "";
        if (!raw) continue;

        const hay = caseSensitiveFlag ? raw : raw.toLowerCase();
        let idx = hay.indexOf(needle);
        while (idx !== -1) {
        // 估算 bbox：把匹配范围在 item 内按比例切分宽度
        const x = item.transform[4];
        const y = item.transform[5];

        const fullWidth = item.width;
        const fullHeight = item.height || Math.abs(item.transform[3]) || 10;

        // 字符比例（仍然是近似，但稳定）
        const startRatio = idx / raw.length;
        const endRatio = (idx + needle.length) / raw.length;

        // X：只用 width，不再乘 a
        const x0 = x + fullWidth * startRatio;
        const x1 = x + fullWidth * endRatio;

        // Y：baseline → 矩形（最保守）
        const y0 = y - fullHeight;
        const y1 = y;

        // 统一成 bboxPdf
        matches.push({
        text: raw.substring(idx, idx + needle.length),
        bboxPdf: {
            x: Math.min(x0, x1),
            y: Math.min(y0, y1),
            width: Math.abs(x1 - x0),
            height: Math.abs(y1 - y0)
        }
        });

        idx = hay.indexOf(needle, idx + needle.length);
        }
    }

    return matches;
}

async function applyHighlights(pageNum, activeMatchIndex = -1) {
    if (!originalPdfDoc) return;

    // 找到该页匹配
    const pageResult = searchResults.find(r => r.pageNum === pageNum);
    if (!pageResult) return;

    // overlay layer
    const overlayLayer = originalContainer.querySelector(".overlay-layer");
    if (!overlayLayer) return;
    overlayLayer.innerHTML = "";

    // 当前页 viewport（必须和 renderPage 同 scale）
    const page = await originalPdfDoc.getPage(pageNum);
    const viewport = page.getViewport({ scale });

    const colorHex = document.getElementById("highlight-color")?.value || "#ffff00";
    const { r, g, b } = hexToRgb(colorHex);
    const debugMode = !!debugModeCheckbox.checked;

    pageResult.matches.forEach((match, idx) => {
        const { x, y, width, height } = match.bboxPdf;
        const rect = viewport.convertToViewportRectangle([x, y, x + width, y + height]);

        const left = Math.min(rect[0], rect[2]);
        const top = Math.min(rect[1], rect[3]);
        const w = Math.abs(rect[2] - rect[0]);
        const h = Math.abs(rect[3] - rect[1]);

        const hl = document.createElement("div");
        hl.className = "highlight-overlay";
        hl.style.position = "absolute";
        hl.style.left = `${left}px`;
        hl.style.top = `${top}px`;
        hl.style.width = `${w}px`;
        hl.style.height = `${h}px`;
        hl.style.zIndex = "30";
        hl.style.backgroundColor =
        idx === activeMatchIndex
            ? "rgba(255, 0, 0, 0.30)"
            : `rgba(${r}, ${g}, ${b}, 0.30)`;

        overlayLayer.appendChild(hl);

        if (debugMode) {
        const dbg = document.createElement("div");
        dbg.className = "debug-info";
        dbg.style.position = "absolute";
        dbg.style.left = `${left}px`;
        dbg.style.top = `${top + h + 2}px`;
        dbg.style.fontSize = "10px";
        dbg.style.color = "red";
        dbg.style.backgroundColor = "rgba(255,255,255,0.9)";
        dbg.style.padding = "2px";
        dbg.style.border = "1px solid red";
        dbg.style.zIndex = "40";
        dbg.style.whiteSpace = "nowrap";
        dbg.textContent =
            `"${match.text}" PDF:(${x.toFixed(1)},${y.toFixed(1)}) View:(${left.toFixed(1)},${top.toFixed(1)})`;
        overlayLayer.appendChild(dbg);
        }
    });
}


async function createHighlightedPdf() {
    if (!originalPdfBytes) return;

    // 颜色
    const colorHex = document.getElementById("highlight-color")?.value || "#ffff00";
    const { r, g, b } = hexToRgb01(colorHex);
    const highlightColor = PDFLib.rgb(r, g, b);

    // pdf-lib load
    const pdfDoc = await PDFLib.PDFDocument.load(originalPdfBytes);

    for (const result of searchResults) {
        const pageIndex = result.pageNum - 1;
        const page = pdfDoc.getPage(pageIndex);

        for (const match of result.matches) {
        const { x, y, width, height } = match.bboxPdf;

        // pdf-lib：原点左下角
        page.drawRectangle({
            x,
            y,
            width,
            height,
            color: highlightColor,
            opacity: 0.35,
            borderWidth: 0
        });
        }
    }

    const highlightedBytes = await pdfDoc.save();

    // 用 pdf.js 重新 load，供右侧窗口显示
    const task = pdfjsLib.getDocument({ data: highlightedBytes });
    highlightedPdfDoc = await task.promise;

    // 更新右侧分页状态
    highlightedPageNum = 1;
    updatePageInfo("highlighted");
    }


async function downloadHighlightedPdf() {
  if (!originalPdfBytes || !highlightedPdfDoc) return;

  showLoading(true);
  try {
    // 重新生成一次，保证下载的是“当前颜色+当前搜索结果”的版本
    // （也可以缓存字节，但为保持功能一致，这里直接重建）
    const colorHex = document.getElementById("highlight-color")?.value || "#ffff00";
    const { r, g, b } = hexToRgb01(colorHex);
    const highlightColor = PDFLib.rgb(r, g, b);

    const pdfDoc = await PDFLib.PDFDocument.load(originalPdfBytes);

    for (const result of searchResults) {
      const pageIndex = result.pageNum - 1;
      const page = pdfDoc.getPage(pageIndex);
      for (const match of result.matches) {
        const { x, y, width, height } = match.bboxPdf;
        page.drawRectangle({
          x, y, width, height,
          color: highlightColor,
          opacity: 0.35,
          borderWidth: 0
        });
      }
    }

    const bytes = await pdfDoc.save();
    const blob = new Blob([bytes], { type: "application/pdf" });

    const a = document.createElement("a");
    const baseName = (fileName?.textContent || "highlighted").replace(/\.pdf$/i, "");
    a.download = `${baseName}_highlighted.pdf`;
    a.href = URL.createObjectURL(blob);
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(a.href);
  } catch (err) {
    console.error("下载高亮PDF出错:", err);
    alert("下载失败：" + err.message);
  } finally {
    showLoading(false);
  }
}

/* -----------------------------
 * 15) 清除高亮（恢复 UI + 清理 overlay / 右侧窗口）
 * ----------------------------- */
async function clearHighlights() {
    searchResults = [];
    totalResults = 0;
    currentResultIndex = 0;

    // 清空 overlay
    const overlayLayer = originalContainer.querySelector(".overlay-layer");
    if (overlayLayer) overlayLayer.innerHTML = "";

    // 右侧清空
    highlightedPdfDoc = null;
    setPlaceholder(highlightedContainer, "请先检索并高亮文本");
    updatePageInfo("highlighted");

    // 结果导航隐藏
    searchNavigation.style.display = "none";
    resultCountSpan.textContent = "0/0";
    prevResultBtn.disabled = true;
    nextResultBtn.disabled = true;

    clearBtn.disabled = true;
    downloadBtn.disabled = true;

    // 重新渲染当前原始页（去掉任何遗留）
    if (originalPdfDoc) {
        await renderPage(originalPageNum, "original");
        updatePageInfo("original");
    }
}

/* -----------------------------
 * 16) 结果导航：上一个/下一个
 * ----------------------------- */
function navigateToPreviousResult() {
    if (totalResults === 0) return;
    currentResultIndex = (currentResultIndex - 1 + totalResults) % totalResults;
    navigateToResult(currentResultIndex);
}

function navigateToNextResult() {
    if (totalResults === 0) return;
    currentResultIndex = (currentResultIndex + 1) % totalResults;
    navigateToResult(currentResultIndex);
}

async function navigateToResult(index) {
    if (totalResults === 0) return;

    // 找到目标页与页内 index
    let count = 0;
    let targetPage = -1;
    let idxOnPage = -1;

    for (const pageResult of searchResults) {
        if (count + pageResult.matches.length > index) {
        targetPage = pageResult.pageNum;
        idxOnPage = index - count;
        break;
        }
        count += pageResult.matches.length;
    }
    if (targetPage === -1) return;

    // 更新 UI 计数
    resultCountSpan.textContent = `${index + 1}/${totalResults}`;

    const highlightMode = getHighlightMode();

    if (highlightMode === "overlay") {
        await showPage(targetPage, "original");
        applyHighlights(targetPage, idxOnPage);
    } else {
        // new-pdf 模式：直接跳到右侧对应页（高亮 PDF）
        if (!highlightedPdfDoc) {
        await createHighlightedPdf();
        }
        await showPage(targetPage, "highlighted");
    }
}

/* -----------------------------
 * 17) 工具：计算“全局索引 -> 页内索引”
 * ----------------------------- */
function getMatchIndexOnPage(pageNum, globalIndex) {
    let count = 0;
    for (const pageResult of searchResults) {
        if (pageResult.pageNum === pageNum) {
        const idx = globalIndex - count;
        return (idx >= 0 && idx < pageResult.matches.length) ? idx : -1;
        }
        count += pageResult.matches.length;
    }
    return -1;
}

/* -----------------------------
 * 18) 读取高亮模式
 * ----------------------------- */
function getHighlightMode() {
    const radio = document.querySelector('input[name="highlight-mode"]:checked');
    return radio ? radio.value : "overlay";
}

/* -----------------------------
 * 19) 颜色工具
 * ----------------------------- */
function hexToRgb(hex) {
  // 返回 0-255
    const h = (hex || "#ffff00").replace("#", "");
    const r = parseInt(h.slice(0, 2), 16);
    const g = parseInt(h.slice(2, 4), 16);
    const b = parseInt(h.slice(4, 6), 16);
    return { r, g, b };
}

function hexToRgb01(hex) {
  // 返回 0-1
    const { r, g, b } = hexToRgb(hex);
    return { r: r / 255, g: g / 255, b: b / 255 };
}
