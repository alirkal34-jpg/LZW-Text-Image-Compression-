import numpy as np
import cv2

class Level3GrayDiffLZW:
    DICT_START = 512

    def __init__(self, codelength: int = 16):
        if codelength < 9 or codelength > 24:
            raise ValueError("For difference-based compression, codelength must be at least 9.")
        self.codelength = codelength
        self._max_dict_size = 1 << codelength

    def calculate_entropy(self, data) -> float:
        arr = np.asarray(data, dtype=np.int16).flatten()
        if arr.size == 0:
            return 0.0
        shifted = (arr + 255).astype(np.int32)
        counts = np.bincount(shifted, minlength=511)
        probabilities = counts[counts > 0] / arr.size
        return float(-np.sum(probabilities * np.log2(probabilities)))

    def compute_difference_image(self, img_array: np.ndarray) -> np.ndarray:
        height, width = img_array.shape
        diff = np.zeros((height, width), dtype=np.int16)
        diff[:, 1:] = img_array[:, 1:].astype(np.int16) - img_array[:, :-1].astype(np.int16)
        diff[1:, 0] = img_array[1:, 0].astype(np.int16) - img_array[:-1, 0].astype(np.int16)
        diff[0, 0] = int(img_array[0, 0])
        return diff

    def reconstruct_from_difference(self, diff_img: np.ndarray) -> np.ndarray:
        height, width = diff_img.shape
        rec = np.zeros((height, width), dtype=np.int32)
        rec[0, 0] = int(diff_img[0, 0])
        for i in range(1, height):
            rec[i, 0] = int(diff_img[i, 0]) + rec[i - 1, 0]
        for i in range(height):
            for j in range(1, width):
                rec[i, j] = int(diff_img[i, j]) + rec[i, j - 1]
        return np.clip(rec, 0, 255).astype(np.uint8)

    def _lzw_encode(self, pixels: list[int]) -> list[int]:
        dict_size = self.DICT_START
        dictionary: dict[tuple, int] = {(i - 255,): i for i in range(dict_size)}
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
        dict_size = self.DICT_START
        dictionary: dict[int, tuple] = {i: (i - 255,) for i in range(dict_size)}
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

    def compress(self, image_path: str) -> tuple[dict | None, np.ndarray | None]:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return None, None
        height, width = img.shape
        diff_img = self.compute_difference_image(img)
        codes = self._lzw_encode(diff_img.flatten().tolist())
        compressed_data = {
            "dimensions": (height, width),
            "codes": codes
        }
        return compressed_data, img

    def decompress(self, compressed_data: dict) -> np.ndarray:
        height, width = compressed_data["dimensions"]
        codes = list(compressed_data["codes"])
        if not codes:
            return np.zeros((height, width), dtype=np.uint8)
        diff_pixels = self._lzw_decode(codes)
        diff_img = np.array(diff_pixels, dtype=np.int16).reshape((height, width))
        return self.reconstruct_from_difference(diff_img)
