import numpy as np
import cv2

class ColorImageLZW:
    def __init__(self, codelength: int = 16):
        if codelength < 8 or codelength > 24:
            raise ValueError("codelength must be between 8 and 24.")
        self.codelength = codelength
        self._max_dict_size = 1 << codelength

    def calculate_entropy(self, data) -> float:
        arr = np.asarray(data, dtype=np.uint8).flatten()
        if arr.size == 0:
            return 0.0
        counts = np.bincount(arr, minlength=256)
        probabilities = counts[counts > 0] / arr.size
        return float(-np.sum(probabilities * np.log2(probabilities)))

    def compress_channel(self, channel_pixels: list[int]) -> list[int]:
        dict_size = 256
        dictionary: dict[tuple, int] = {(i,): i for i in range(dict_size)}
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

    def decompress_channel(self, compressed_codes: list[int]) -> list[int]:
        if not compressed_codes:
            return []
        codes = list(compressed_codes)
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

    def compress(self, image_path: str) -> tuple[dict | None, np.ndarray | None]:
        img = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if img is None:
            return None, None
        height, width = img.shape[:2]
        b_ch, g_ch, r_ch = cv2.split(img)
        compressed_data = {
            "dimensions": (height, width),
            "B": self.compress_channel(b_ch.flatten().tolist()),
            "G": self.compress_channel(g_ch.flatten().tolist()),
            "R": self.compress_channel(r_ch.flatten().tolist()),
        }
        return compressed_data, img

    def decompress(self, compressed_data: dict) -> np.ndarray:
        height, width = compressed_data["dimensions"]
        b_pixels = self.decompress_channel(list(compressed_data["B"]))
        g_pixels = self.decompress_channel(list(compressed_data["G"]))
        r_pixels = self.decompress_channel(list(compressed_data["R"]))
        b_ch = np.array(b_pixels, dtype=np.uint8).reshape((height, width))
        g_ch = np.array(g_pixels, dtype=np.uint8).reshape((height, width))
        r_ch = np.array(r_pixels, dtype=np.uint8).reshape((height, width))
        return cv2.merge((b_ch, g_ch, r_ch))