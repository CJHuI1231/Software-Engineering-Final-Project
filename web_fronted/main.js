let pdfDoc = null;
let currentPage = 1;
let totalPages = 1;
let scale = 1.0;

const canvas = document.getElementById("pdfCanvas");
const ctx = canvas.getContext("2d");
const fileInput = document.getElementById("pdfFile");
const fileName = document.getElementById("fileName");

fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
        fileName.textContent = fileInput.files[0].name;
    }
    const file = fileInput.files[0];
    if (!file) return;

    const fileReader = new FileReader();
    fileReader.onload = function () {
        const typedarray = new Uint8Array(this.result);

        pdfjsLib.getDocument(typedarray).promise.then(pdf => {
            pdfDoc = pdf;
            totalPages = pdf.numPages;
            currentPage = 1;
            renderPage();
        });
    };
    fileReader.readAsArrayBuffer(file);

});

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