import numpy as np
import cv2

class ColorDiffLZW:
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
        diff = np.zeros_like(img_array, dtype=np.int16)
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

    def compress_channel_diff(self, channel_pixels: list[int]) -> list[int]:
        dict_size = self.DICT_START
        dictionary: dict[tuple, int] = {(i - 255,): i for i in range(dict_size)}
        w: tuple = ()
        codes: list[int] = []
        for val in channel_pixels:
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

    def decompress_channel_diff(self, compressed_codes: list[int]) -> list[int]:
        if not compressed_codes:
            return []
        codes = list(compressed_codes)
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
        img = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if img is None:
            return None, None
        height, width = img.shape[:2]
        b_ch, g_ch, r_ch = cv2.split(img)
        compressed_data = {
            "dimensions": (height, width),
            "B": self.compress_channel_diff(self.compute_difference_image(b_ch).flatten().tolist()),
            "G": self.compress_channel_diff(self.compute_difference_image(g_ch).flatten().tolist()),
            "R": self.compress_channel_diff(self.compute_difference_image(r_ch).flatten().tolist()),
        }
        return compressed_data, img

    def decompress(self, compressed_data: dict) -> np.ndarray:
        height, width = compressed_data["dimensions"]
        b_pixels = self.decompress_channel_diff(list(compressed_data["B"]))
        g_pixels = self.decompress_channel_diff(list(compressed_data["G"]))
        r_pixels = self.decompress_channel_diff(list(compressed_data["R"]))
        diff_b = np.array(b_pixels, dtype=np.int16).reshape((height, width))
        diff_g = np.array(g_pixels, dtype=np.int16).reshape((height, width))
        diff_r = np.array(r_pixels, dtype=np.int16).reshape((height, width))
        b_ch = self.reconstruct_from_difference(diff_b)
        g_ch = self.reconstruct_from_difference(diff_g)
        r_ch = self.reconstruct_from_difference(diff_r)
        return cv2.merge((b_ch, g_ch, r_ch))