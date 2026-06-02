import math
from collections import Counter

class TextLZW:
    def __init__(self, codelength: int = 16):
        if codelength < 8 or codelength > 24:
            raise ValueError("codelength must be between 8 and 24.")
        self.codelength = codelength
        self._max_dict_size = 1 << codelength

    def calculate_entropy(self, text: str) -> float:
        if not text:
            return 0.0
        counts = Counter(text)
        total = len(text)
        entropy = 0.0
        for count in counts.values():
            p = count / total
            entropy -= p * math.log2(p)
        return entropy

    def compress(self, uncompressed: str) -> tuple[list[int], str]:
        if not uncompressed:
            return [], uncompressed
        dict_size = 256
        dictionary: dict[str, int] = {chr(i): i for i in range(dict_size)}
        w = ""
        result: list[int] = []
        for c in uncompressed:
            wc = w + c
            if wc in dictionary:
                w = wc
            else:
                result.append(dictionary[w])
                if dict_size < self._max_dict_size:
                    dictionary[wc] = dict_size
                    dict_size += 1
                w = c
        if w:
            result.append(dictionary[w])
        return result, uncompressed

    def decompress(self, compressed: list[int]) -> str:
        if not compressed:
            return ""
        compressed = list(compressed)
        dict_size = 256
        dictionary: dict[int, str] = {i: chr(i) for i in range(dict_size)}
        result: list[str] = []
        k = compressed.pop(0)
        if k not in dictionary:
            raise ValueError(f"Invalid starting code: {k}")
        w = dictionary[k]
        result.append(w)
        for k in compressed:
            if k in dictionary:
                entry = dictionary[k]
            elif k == dict_size:
                entry = w + w[0]
            else:
                raise ValueError(f"Corrupted code: {k}")
            result.append(entry)
            if dict_size < self._max_dict_size:
                dictionary[dict_size] = w + entry[0]
                dict_size += 1
            w = entry
        return "".join(result)