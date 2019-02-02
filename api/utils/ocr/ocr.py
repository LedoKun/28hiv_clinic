import pytesseract
from PIL import Image

from page_detection import PageDetection


class OCR(object):
    page = None
    text = None

    def __init__(self, img_path):
        self.page = PageDetection(img_path)

    def getText(self):
        if not self.text:
            cv2_page = self.page.getThreshPage()
            pil_im = Image.fromarray(cv2_page)
            self.text = pytesseract.image_to_string(
                pil_im, lang="eng", config="--psm 3 --oem 2"
            )

        return self.text
