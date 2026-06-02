import numpy as np
import cv2

class GrayscaleImageLZW:
    def __init__(self, codelength: int = 16):
        if codelength < 8 or codelength > 24:
            raise ValueError("codelength must be between 8 and 24.")
        self.codelength = codelength
        self._max_dict_size = 1 << codelength

    def calculate_entropy(self, image_array) -> float:
        data = np.asarray(image_array, dtype=np.uint8).flatten()
        if data.size == 0:
            return 0.0
        counts = np.bincount(data, minlength=256)
        probabilities = counts[counts > 0] / data.size
        return float(-np.sum(probabilities * np.log2(probabilities)))

    def _lzw_encode(self, pixels: list[int]) -> list[int]:
        dict_size = 256
        dictionary: dict[tuple, int] = {(i,): i for i in range(dict_size)}
        w: tuple = ()
        codes: list[int] = []
        for val in pixels:
            wc = w + (val,)
            if wc in dictionary:
                w = wc
            else:
                codes.append(dictionary[w])
                if dict_size < self._max_dict_size:
                    dictionary[wc] = dict_size
                    dict_size += 1
                w = (val,)
        if w:
            codes.append(dictionary[w])
        return codes

    def _lzw_decode(self, codes: list[int]) -> list[int]:
        if not codes:
            return []
        codes = list(codes)
        dict_size = 256
        dictionary: dict[int, tuple] = {i: (i,) for i in range(dict_size)}
        result: list[int] = []
        k = codes.pop(0)
        w = dictionary[k]
        result.extend(w)
        for k in codes:
            if k in dictionary:
                entry = dictionary[k]
            elif k == dict_size:
                entry = w + (w[0],)
            else:
                raise ValueError(f"Corrupted code found: {k}")
            result.extend(entry)
            if dict_size < self._max_dict_size:
                dictionary[dict_size] = w + (entry[0],)
                dict_size += 1
            w = entry
        return result

    def compress_image(self, image_path: str) -> tuple[dict | None, np.ndarray | None]:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return None, None
        height, width = img.shape
        codes = self._lzw_encode(img.flatten().tolist())
        compressed_data = {
            "dimensions": (height, width),
            "codes": codes
        }
        return compressed_data, img

    def decompress_image(self, compressed_data: dict) -> np.ndarray:
        height, width = compressed_data["dimensions"]
        codes = list(compressed_data["codes"])
        if not codes:
            return np.zeros((height, width), dtype=np.uint8)
        pixels = self._lzw_decode(codes)
        return np.array(pixels, dtype=np.uint8).reshape((height, width))