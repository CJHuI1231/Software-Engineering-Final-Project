// 设置PDF.js的worker
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

// 全局变量
let originalPdfDoc = null;
let highlightedPdfDoc = null;
let originalPageNum = 1;
let highlightedPageNum = 1;
let pageRendering = false;
let pageNumPending = null;
let scale = 1.5;
let searchTerm = '';
let searchResults = [];
let highlightedPdfBytes = null;
let currentResultIndex = 0;
let totalResults = 0;

// DOM元素
const fileInput = document.getElementById('pdf-upload');
const fileName = document.getElementById('file-name');
const searchInput = document.getElementById('search-term');
const searchBtn = document.getElementById('search-btn');
const clearBtn = document.getElementById('clear-btn');
const downloadBtn = document.getElementById('download-btn');
const loading = document.getElementById('loading');
const searchNavigation = document.getElementById('search-navigation');
const prevResultBtn = document.getElementById('prev-result');
const nextResultBtn = document.getElementById('next-result');
const resultCount = document.getElementById('result-count');

// 原始PDF相关元素
const originalContainer = document.getElementById('original-pdf-container');
const prevPageOriginal = document.getElementById('prev-page-original');
const nextPageOriginal = document.getElementById('next-page-original');
const pageNumOriginal = document.getElementById('page-num-original');

// 高亮PDF相关元素
const highlightedContainer = document.getElementById('highlighted-pdf-container');
const prevPageHighlighted = document.getElementById('prev-page-highlighted');
const nextPageHighlighted = document.getElementById('next-page-highlighted');
const pageNumHighlighted = document.getElementById('page-num-highlighted');

// 事件监听器
fileInput.addEventListener('change', handleFileSelect);
searchBtn.addEventListener('click', searchAndHighlight);
clearBtn.addEventListener('click', clearHighlights);
downloadBtn.addEventListener('click', downloadHighlightedPdf);
prevPageOriginal.addEventListener('click', () => showPage(originalPageNum - 1, 'original'));
nextPageOriginal.addEventListener('click', () => showPage(originalPageNum + 1, 'original'));
prevPageHighlighted.addEventListener('click', () => showPage(highlightedPageNum - 1, 'highlighted'));
nextPageHighlighted.addEventListener('click', () => showPage(highlightedPageNum + 1, 'highlighted'));
prevResultBtn.addEventListener('click', navigateToPreviousResult);
nextResultBtn.addEventListener('click', navigateToNextResult);

// 监听高亮模式变化
document.querySelectorAll('input[name="highlight-mode"]').forEach(radio => {
    radio.addEventListener('change', () => {
        // 如果切换到直接高亮模式，显示原始PDF并应用高亮
        if (radio.value === 'overlay' && searchResults.length > 0) {
            showPage(originalPageNum, 'original');
            applyHighlights(originalPageNum);
        }
        // 如果切换到生成PDF模式，显示高亮PDF
        else if (radio.value === 'new-pdf' && highlightedPdfDoc) {
            showPage(highlightedPageNum, 'highlighted');
        }
    });
});

// 处理文件选择
async function handleFileSelect(e) {
    const file = e.target.files[0];
    if (!file || file.type !== 'application/pdf') {
        alert('请选择有效的PDF文件');
        return;
    }
    
    fileName.textContent = file.name;
    showLoading(true);
    
    try {
        const arrayBuffer = await file.arrayBuffer();
        const loadingTask = pdfjsLib.getDocument({data: arrayBuffer});
        originalPdfDoc = await loadingTask.promise;
        
        // 重置页码
        originalPageNum = 1;
        highlightedPageNum = 1;
        
        // 渲染第一页
        await renderPage(originalPageNum, 'original');
        
        // 启用搜索按钮
        searchBtn.disabled = false;
        
        // 更新页码信息
        updatePageInfo('original');
        
        // 清空高亮PDF容器
        highlightedContainer.innerHTML = '<div class="placeholder">请先检索并高亮文本</div>';
        downloadBtn.disabled = true;
        
    } catch (error) {
        console.error('加载PDF时出错:', error);
        alert('加载PDF文件时出错，请重试');
    } finally {
        showLoading(false);
    }
}

// 渲染PDF页面
async function renderPage(num, type) {
    const pdfDoc = type === 'original' ? originalPdfDoc : highlightedPdfDoc;
    const container = type === 'original' ? originalContainer : highlightedContainer;
    
    if (!pdfDoc) return;
    
    pageRendering = true;
    
    try {
        const page = await pdfDoc.getPage(num);
        const viewport = page.getViewport({scale: scale});
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        canvas.height = viewport.height;
        canvas.width = viewport.width;
        
        const renderContext = {
            canvasContext: context,
            viewport: viewport
        };
        
        await page.render(renderContext).promise;
        
        // 清空容器并添加canvas
        container.innerHTML = '';
        container.appendChild(canvas);
        
        // 如果是原始PDF且有搜索结果，且选择了直接高亮模式，则应用高亮
        if (type === 'original' && searchResults.length > 0 && 
            document.querySelector('input[name="highlight-mode"]:checked').value === 'overlay') {
            applyHighlights(num);
        }
        
        // 更新页码
        if (type === 'original') {
            originalPageNum = num;
        } else {
            highlightedPageNum = num;
        }
        
        updatePageInfo(type);
        
    } catch (error) {
        console.error(`渲染页面 ${num} 时出错:`, error);
    } finally {
        pageRendering = false;
        
        // 如果有待渲染的页面，继续渲染
        if (pageNumPending !== null) {
            renderPage(pageNumPending, type);
            pageNumPending = null;
        }
    }
}

// 队列渲染页面
function queueRenderPage(num, type) {
    if (pageRendering) {
        pageNumPending = num;
    } else {
        renderPage(num, type);
    }
}

// 显示页面
function showPage(num, type) {
    const pdfDoc = type === 'original' ? originalPdfDoc : highlightedPdfDoc;
    
    if (!pdfDoc) return;
    
    if (num < 1 || num > pdfDoc.numPages) return;
    
    queueRenderPage(num, type);
}

// 更新页码信息
function updatePageInfo(type) {
    const pdfDoc = type === 'original' ? originalPdfDoc : highlightedPdfDoc;
    const pageNumElement = type === 'original' ? pageNumOriginal : pageNumHighlighted;
    const prevBtn = type === 'original' ? prevPageOriginal : prevPageHighlighted;
    const nextBtn = type === 'original' ? nextPageOriginal : nextPageHighlighted;
    const currentPage = type === 'original' ? originalPageNum : highlightedPageNum;
    
    if (pdfDoc) {
        pageNumElement.textContent = `页码: ${currentPage}/${pdfDoc.numPages}`;
        prevBtn.disabled = currentPage <= 1;
        nextBtn.disabled = currentPage >= pdfDoc.numPages;
    }
}

// 搜索并高亮文本
async function searchAndHighlight() {
    searchTerm = searchInput.value.trim();
    if (!searchTerm) {
        alert('请输入要搜索的词语');
        return;
    }
    
    if (!originalPdfDoc) {
        alert('请先上传PDF文件');
        return;
    }
    
    showLoading(true);
    searchResults = [];
    currentResultIndex = 0;
    totalResults = 0;
    
    // 获取搜索选项
    const caseSensitive = document.getElementById('case-sensitive').checked;
    
    try {
        console.log('开始搜索，搜索词:', searchTerm);
        console.log('区分大小写:', caseSensitive);
        console.log('PDF总页数:', originalPdfDoc.numPages);
        
        // 搜索所有页面中的文本
        for (let pageNum = 1; pageNum <= originalPdfDoc.numPages; pageNum++) {
            const page = await originalPdfDoc.getPage(pageNum);
            
            // 获取文本内容和位置信息
            let textContent;
            try {
                textContent = await page.getTextContent();
                console.log(`页面 ${pageNum} 提取到 ${textContent.items.length} 个文本项`);
            } catch (error) {
                console.warn(`无法获取页面 ${pageNum} 的文本内容:`, error);
                continue;
            }
            
            // 提取文本并记录位置信息
            const pageText = textContent.items.map(item => item.str).join(' ');
            console.log(`页面 ${pageNum} 文本预览:`, pageText.substring(0, 100) + '...');
            
            // 根据是否区分大小写选择比较方法
            const searchText = caseSensitive ? pageText : pageText.toLowerCase();
            const searchPattern = caseSensitive ? searchTerm : searchTerm.toLowerCase();
            
            // 检查页面是否包含搜索词
            if (searchText.includes(searchPattern)) {
                console.log(`页面 ${pageNum} 找到匹配项`);
                
                // 获取文本位置信息
                const matches = [];
                
                // 使用更精确的搜索方法
                const fullText = textContent.items.map(item => item.str).join('');
                const fullTextSearch = caseSensitive ? fullText : fullText.toLowerCase();
                
                // 查找所有匹配位置
                let startIndex = 0;
                while ((startIndex = fullTextSearch.indexOf(searchPattern, startIndex)) !== -1) {
                    const endIndex = startIndex + searchTerm.length;
                    
                    // 找到匹配文本对应的文本项
                    let currentLength = 0;
                    let startItemIndex = -1;
                    let endItemIndex = -1;
                    let startOffset = -1;
                    let endOffset = -1;
                    
                    for (let i = 0; i < textContent.items.length; i++) {
                        const itemLength = textContent.items[i].str.length;
                        
                        if (startItemIndex === -1 && currentLength + itemLength > startIndex) {
                            startItemIndex = i;
                            startOffset = startIndex - currentLength;
                        }
                        
                        if (startItemIndex !== -1 && currentLength + itemLength >= endIndex) {
                            endItemIndex = i;
                            endOffset = endIndex - currentLength;
                            break;
                        }
                        
                        currentLength += itemLength;
                    }
                    
                    if (startItemIndex !== -1 && endItemIndex !== -1) {
                        // 获取匹配文本的边界框
                        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
                        
                        for (let i = startItemIndex; i <= endItemIndex; i++) {
                            const item = textContent.items[i];
                            
                            // PDF.js的textContent.items中的transform是6元素数组: [a, b, c, d, e, f]
                            // 其中 e=translateX, f=translateY (PDF坐标系，原点在左下角)
                            if (item.transform) {
                                const tx = item.transform;
                                const x = tx[4]; // translateX
                                const y = tx[5]; // translateY
                                
                                // 使用width和height属性（如果有）
                                let width, height;
                                if (item.width !== undefined && item.height !== undefined) {
                                    width = item.width;
                                    height = item.height;
                                } else {
                                    // 从变换矩阵估算
                                    const scaleX = Math.sqrt(tx[0] * tx[0] + tx[1] * tx[1]);
                                    const scaleY = Math.sqrt(tx[2] * tx[2] + tx[3] * tx[3]);
                                    width = item.str.length * scaleX * 0.6;
                                    height = scaleY;
                                }
                                
                                minX = Math.min(minX, x);
                                minY = Math.min(minY, y);
                                maxX = Math.max(maxX, x + width);
                                maxY = Math.max(maxY, y + height);
                            }
                        }
                        
                        // 确保边界框有效
                        if (minX !== Infinity && minY !== Infinity && maxX !== -Infinity && maxY !== -Infinity) {
                            const bbox = {
                                x: minX,
                                y: minY,
                                width: maxX - minX,
                                height: maxY - minY
                            };
                            
                            console.log(`找到匹配 "${fullText.substring(startIndex, endIndex)}" 在页面 ${pageNum}:`, bbox);
                            
                            matches.push({
                                startIndex: startIndex,
                                endIndex: endIndex,
                                startItemIndex: startItemIndex,
                                endItemIndex: endItemIndex,
                                startOffset: startOffset,
                                endOffset: endOffset,
                                text: fullText.substring(startIndex, endIndex),
                                bbox: bbox
                            });
                        }
                    }
                    
                    startIndex = endIndex;
                }
                
                if (matches.length > 0) {
                    searchResults.push({
                        pageNum: pageNum,
                        matches: matches
                    });
                    totalResults += matches.length;
                }
            }
        }
        
        console.log('搜索结果:', searchResults);
        
        if (searchResults.length === 0) {
            alert('未找到匹配的文本。提示：某些PDF可能包含扫描图像而非可搜索文本。请查看浏览器控制台获取更多信息。');
            showLoading(false);
            return;
        }
        
        // 显示搜索结果导航
        searchNavigation.style.display = 'flex';
        resultCount.textContent = `1/${totalResults}`;
        prevResultBtn.disabled = totalResults <= 1;
        nextResultBtn.disabled = totalResults <= 1;
        
        // 启用清除按钮
        clearBtn.disabled = false;
        
        // 根据选择的高亮模式执行不同操作
        const highlightMode = document.querySelector('input[name="highlight-mode"]:checked').value;
        
        if (highlightMode === 'overlay') {
            // 直接在原始PDF上高亮显示
            await renderPage(originalPageNum, 'original');
            downloadBtn.disabled = true; // 直接高亮模式下不提供下载功能
        } else {
            // 创建高亮PDF
            await createHighlightedPdf();
            
            // 显示高亮PDF的第一页
            await renderPage(1, 'highlighted');
            
            // 启用下载按钮
            downloadBtn.disabled = false;
        }
        
    } catch (error) {
        console.error('搜索和高亮文本时出错:', error);
        alert('处理文本时出错，请重试。错误详情: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// 创建高亮PDF
async function createHighlightedPdf() {
    try {
        // 获取原始PDF的字节数组
        const originalPdfArray = await originalPdfDoc.getData();
        
        // 使用pdf-lib加载PDF
        const pdfDoc = await PDFLib.PDFDocument.load(originalPdfArray);
        
        // 获取用户选择的高亮颜色
        const highlightColorInput = document.getElementById('highlight-color');
        const highlightColorHex = highlightColorInput.value;
        
        // 将十六进制颜色转换为RGB
        const r = parseInt(highlightColorHex.substr(1, 2), 16) / 255;
        const g = parseInt(highlightColorHex.substr(3, 2), 16) / 255;
        const b = parseInt(highlightColorHex.substr(5, 2), 16) / 255;
        
        // 设置高亮颜色
        const highlightColor = PDFLib.rgb(r, g, b);
        
        // 为每个搜索结果添加高亮
        for (const result of searchResults) {
            const page = pdfDoc.getPage(result.pageNum - 1);
            const { width, height } = page.getSize();
            
            // 获取原始页面的旋转信息
            const originalPage = await originalPdfDoc.getPage(result.pageNum);
            const viewport = originalPage.getViewport({ scale: 1.0 });
            const rotation = viewport.rotation || 0;
            
            // 为每个匹配项添加高亮矩形
            for (const match of result.matches) {
                if (!match.bbox) continue;
                
                let x, y, rectWidth, rectHeight;
                
                // PDF坐标系：原点在左下角，Y轴向上
                // pdf-lib使用相同的坐标系统
                if (rotation === 0) {
                    // 无旋转 - 直接使用bbox，但需要转换Y坐标
                    x = match.bbox.x;
                    y = height - match.bbox.y - match.bbox.height;
                    rectWidth = match.bbox.width;
                    rectHeight = match.bbox.height;
                } else if (rotation === 90) {
                    // 90度旋转
                    x = match.bbox.y;
                    y = match.bbox.x;
                    rectWidth = match.bbox.height;
                    rectHeight = match.bbox.width;
                } else if (rotation === 180) {
                    // 180度旋转
                    x = width - match.bbox.x - match.bbox.width;
                    y = match.bbox.y;
                    rectWidth = match.bbox.width;
                    rectHeight = match.bbox.height;
                } else if (rotation === 270) {
                    // 270度旋转
                    x = width - match.bbox.y - match.bbox.height;
                    y = height - match.bbox.x - match.bbox.width;
                    rectWidth = match.bbox.height;
                    rectHeight = match.bbox.width;
                } else {
                    // 其他角度，使用原始坐标
                    x = match.bbox.x;
                    y = height - match.bbox.y - match.bbox.height;
                    rectWidth = match.bbox.width;
                    rectHeight = match.bbox.height;
                }
                
                // 确保高亮矩形在页面范围内
                if (x >= 0 && y >= 0 && x + rectWidth <= width && y + rectHeight <= height) {
                    // 绘制半透明矩形作为高亮
                    page.drawRectangle({
                        x: x,
                        y: y,
                        width: rectWidth,
                        height: rectHeight,
                        color: highlightColor,
                        opacity: 0.3
                    });
                } else {
                    console.warn('高亮矩形超出页面范围:', { x, y, rectWidth, rectHeight, width, height });
                }
            }
        }
        
        // 保存修改后的PDF
        highlightedPdfBytes = await pdfDoc.save();
        
        // 加载修改后的PDF以供显示
        const loadingTask = pdfjsLib.getDocument({data: highlightedPdfBytes});
        highlightedPdfDoc = await loadingTask.promise;
        
    } catch (error) {
        console.error('创建高亮PDF时出错:', error);
        throw error;
    }
}

// 下载高亮后的PDF
function downloadHighlightedPdf() {
    if (!highlightedPdfBytes) {
        alert('没有可下载的高亮PDF');
        return;
    }
    
    const blob = new Blob([highlightedPdfBytes], { type: 'application/pdf' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `highlighted_${searchTerm}_${Date.now()}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// 清除高亮
function clearHighlights() {
    searchResults = [];
    currentResultIndex = 0;
    totalResults = 0;
    highlightedPdfDoc = null;
    highlightedPdfBytes = null;
    
    // 隐藏搜索结果导航
    searchNavigation.style.display = 'none';
    
    // 禁用清除和下载按钮
    clearBtn.disabled = true;
    downloadBtn.disabled = true;
    
    // 重新渲染原始PDF
    if (originalPdfDoc) {
        renderPage(originalPageNum, 'original');
    }
    
    // 清空高亮PDF容器
    highlightedContainer.innerHTML = '<div class="placeholder">请先检索并高亮文本</div>';
}

// 显示/隐藏加载提示
function showLoading(show) {
    loading.style.display = show ? 'flex' : 'none';
}

// 在原始PDF上应用高亮覆盖层
async function applyHighlights(pageNum, activeMatchIndex = -1) {
    // 查找当前页面的搜索结果
    const pageResults = searchResults.find(result => result.pageNum === pageNum);
    if (!pageResults || pageResults.matches.length === 0) return;
    
    // 获取当前页面的canvas
    const canvas = originalContainer.querySelector('canvas');
    if (!canvas) return;
    
    // 获取页面信息
    const page = await originalPdfDoc.getPage(pageNum);
    const viewport = page.getViewport({ scale: scale });
    
    // 获取canvas的实际渲染尺寸（屏幕像素）
    const canvasRect = canvas.getBoundingClientRect();
    const containerRect = originalContainer.getBoundingClientRect();
    
    // Canvas的实际尺寸（PDF单位 * scale）
    const pdfWidth = viewport.width;
    const pdfHeight = viewport.height;
    
    // 计算从PDF坐标到屏幕坐标的比例
    const scaleX = canvasRect.width / pdfWidth;
    const scaleY = canvasRect.height / pdfHeight;
    
    // 获取用户选择的高亮颜色
    const highlightColorInput = document.getElementById('highlight-color');
    const highlightColor = highlightColorInput.value;
    
    // 将十六进制颜色转换为RGB
    const r = parseInt(highlightColor.substr(1, 2), 16);
    const g = parseInt(highlightColor.substr(3, 2), 16);
    const b = parseInt(highlightColor.substr(5, 2), 16);
    
    // 检查是否启用调试模式
    const debugMode = document.getElementById('debug-mode').checked;
    
    console.log('Canvas尺寸:', canvasRect.width, canvasRect.height);
    console.log('PDF尺寸:', pdfWidth, pdfHeight);
    console.log('缩放比例:', scaleX, scaleY);
    
    // 为每个匹配项创建高亮覆盖层
    pageResults.matches.forEach((match, index) => {
        if (!match.bbox) return;
        
        // PDF坐标 (原点在左下角)
        const pdfX = match.bbox.x;
        const pdfY = match.bbox.y;
        const pdfW = match.bbox.width;
        const pdfH = match.bbox.height;
        
        // 转换到Canvas坐标系 (原点在左上角)
        // 直接使用Y坐标，不翻转（因为PDF.js已经处理了坐标系转换）
        const canvasX = pdfX * scaleX;
        const canvasY = pdfY * scaleY;
        const canvasW = pdfW * scaleX;
        const canvasH = pdfH * scaleY;
        
        // 调整到容器相对位置
        const finalX = canvasX + (canvasRect.left - containerRect.left);
        const finalY = canvasY + (canvasRect.top - containerRect.top);
        
        console.log(`匹配 "${match.text}": PDF坐标(${pdfX.toFixed(1)}, ${pdfY.toFixed(1)}, ${pdfW.toFixed(1)}, ${pdfH.toFixed(1)}) -> Canvas坐标(${canvasX.toFixed(1)}, ${canvasY.toFixed(1)}, ${canvasW.toFixed(1)}, ${canvasH.toFixed(1)})`);
        
        // 创建高亮覆盖层
        const highlight = document.createElement('div');
        highlight.className = 'highlight-overlay';
        
        // 设置高亮样式
        highlight.style.left = `${finalX}px`;
        highlight.style.top = `${finalY}px`;
        highlight.style.width = `${canvasW}px`;
        highlight.style.height = `${canvasH}px`;
        
        // 如果是当前活动结果，使用红色高亮
        if (index === activeMatchIndex) {
            highlight.style.backgroundColor = 'rgba(255, 0, 0, 0.3)';
        } else {
            // 使用用户选择的颜色
            highlight.style.backgroundColor = `rgba(${r}, ${g}, ${b}, 0.3)`;
        }
        
        // 添加到容器
        originalContainer.appendChild(highlight);
        
        // 如果启用调试模式，添加调试信息
        if (debugMode) {
            const debugInfo = document.createElement('div');
            debugInfo.className = 'debug-info';
            debugInfo.style.position = 'absolute';
            debugInfo.style.left = `${finalX}px`;
            debugInfo.style.top = `${finalY + canvasH + 2}px`;
            debugInfo.style.fontSize = '10px';
            debugInfo.style.color = 'red';
            debugInfo.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
            debugInfo.style.padding = '2px';
            debugInfo.style.border = '1px solid red';
            debugInfo.style.zIndex = '100';
            debugInfo.style.whiteSpace = 'nowrap';
            debugInfo.textContent = `"${match.text}" PDF:(${pdfX.toFixed(0)},${pdfY.toFixed(0)}) Canvas:(${canvasX.toFixed(0)},${canvasY.toFixed(0)})`;
            
            originalContainer.appendChild(debugInfo);
        }
    });
}

// 导航到上一个搜索结果
function navigateToPreviousResult() {
    if (totalResults === 0) return;
    
    currentResultIndex = (currentResultIndex - 1 + totalResults) % totalResults;
    navigateToResult(currentResultIndex);
}

// 导航到下一个搜索结果
function navigateToNextResult() {
    if (totalResults === 0) return;
    
    currentResultIndex = (currentResultIndex + 1) % totalResults;
    navigateToResult(currentResultIndex);
}

// 导航到指定的搜索结果
function navigateToResult(index) {
    if (totalResults === 0) return;
    
    // 计算结果所在的页面
    let resultCount = 0;
    let targetPage = -1;
    let targetMatchIndex = -1;
    
    for (const pageResult of searchResults) {
        if (resultCount + pageResult.matches.length > index) {
            targetPage = pageResult.pageNum;
            targetMatchIndex = index - resultCount;
            break;
        }
        resultCount += pageResult.matches.length;
    }
    
    if (targetPage === -1) return;
    
    // 更新结果计数显示
    resultCount.textContent = `${index + 1}/${totalResults}`;
    
    // 根据高亮模式导航到目标页面
    const highlightMode = document.querySelector('input[name="highlight-mode"]:checked').value;
    
    if (highlightMode === 'overlay') {
        // 直接高亮模式
        showPage(targetPage, 'original').then(() => {
            // 应用高亮并突出显示当前结果
            applyHighlights(targetPage, targetMatchIndex);
        });
    } else {
        // 生成PDF模式
        showPage(targetPage, 'highlighted');
    }
}
