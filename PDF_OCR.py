import os
import pytesseract
from pdf2image import convert_from_path
import pdfplumber
from PIL import Image
class PdfOcrParser:
    """
    一个用于解析PDF文件的模块，支持直接文本提取和OCR识别。
    会自动判断PDF类型并选择最优解析方式。
    """
    def __init__(self, ocr_lang='chi_sim+eng'):
        """
        初始化解析器。
        :param ocr_lang: Tesseract OCR使用的语言包，默认为中文简体和英文。
                         'chi_sim' 为中文简体，'eng' 为英文。
        """
        # 在某些环境中，需要手动指定tesseract执行路径
        # 如果tesseract不在系统的PATH中，请取消下面一行的注释并设置正确路径
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        self.ocr_lang = ocr_lang
        self.min_text_length_per_page = 50 # 每页最少字符数，低于此值则使用OCR
    def parse(self, pdf_path: str) -> str:
        """
        解析PDF文件，提取所有文本。
        :param pdf_path: PDF文件的路径。
        :return: 提取出的完整文本字符串。
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"文件未找到: {pdf_path}")
        print(f"正在尝试直接从 {pdf_path} 提取文本...")
        text, page_count = self._extract_text_directly(pdf_path)
        # 判断直接提取的文本量是否足够
        if len(text.strip()) > page_count * self.min_text_length_per_page:
            print("直接文本提取成功，内容丰富。")
            return text
        else:
            print("直接提取的文本量较少或为空，切换到OCR模式。")
            return self._extract_text_with_ocr(pdf_path)
    def _extract_text_directly(self, pdf_path: str) -> (str, int):
        """使用pdfplumber直接提取文本。"""
        full_text = ""
        page_count = 0
        try:
            with pdfplumber.open(pdf_path) as pdf:
                page_count = len(pdf.pages)
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
        except Exception as e:
            print(f"直接文本提取时出错: {e}")
        return full_text, page_count
    def _extract_text_with_ocr(self, pdf_path: str) -> str:
        """使用pdf2image和pytesseract进行OCR识别。"""
        full_text = ""
        try:
            # 将PDF转换为图像列表
            # poppler_path参数在Windows上可能需要手动指定
            images = convert_from_path(pdf_path, dpi=300) # 300 DPI能提供较好的识别清晰度
            print(f"PDF已转换为 {len(images)} 张图片，开始OCR识别...")
            for i, image in enumerate(images):
                print(f"正在识别第 {i+1}/{len(images)} 页...")
                # 使用PIL.Image对象直接进行OCR
                text = pytesseract.image_to_string(image, lang=self.ocr_lang)
                full_text += text + "\n"
        except Exception as e:
            print(f"OCR识别过程中出错: {e}")
            print("请确保已安装Tesseract-OCR和poppler-utils，并将其添加到系统PATH中。")
            return ""
        return full_text
# --- 使用示例 ---
if __name__ == '__main__':
    # 创建一个解析器实例，默认识别中英文
    parser = PdfOcrParser(ocr_lang='chi_sim+eng')
    # 请将 'your_document.pdf' 替换为你的PDF文件路径
    pdf_file = 'test.pdf' 
    # 如果没有示例文件，可以创建一个提示
    if not os.path.exists(pdf_file):
        print(f"请将此脚本与名为'{pdf_file}'的PDF文件放在同一目录下，或修改pdf_file变量指向正确的文件路径。")
    else:
        try:
            extracted_text = parser.parse(pdf_file)
            # 将结果保存到文本文件
            output_file = os.path.splitext(pdf_file)[0] + '_output.txt'
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(extracted_text)
            print("\n--- 解析完成 ---")
            print(f"提取的文本已保存到: {output_file}")
            print("\n--- 文本预览 (前500字符) ---")
            print(extracted_text[:500])
        except FileNotFoundError as e:
            print(e)
        except Exception as e:
            print(f"发生未知错误: {e}")