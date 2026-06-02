HEADER_FIELD_COUNT = 7
HEADER_BITS = HEADER_FIELD_COUNT * 16

def header_to_binary_string(header_array: list[int]) -> str:
    if len(header_array) != HEADER_FIELD_COUNT:
        raise ValueError(f"Header must contain {HEADER_FIELD_COUNT} elements, {len(header_array)} provided.")
    return "".join(format(num, '016b') for num in header_array)

def binary_string_to_header(encoded_text: str) -> list[int]:
    if len(encoded_text) < HEADER_BITS:
        raise ValueError(f"Header requires at least {HEADER_BITS} bits.")
    return [int(encoded_text[i:i + 16], 2) for i in range(0, HEADER_BITS, 16)]

def _initial_codelength(dict_size: int) -> int:
    if dict_size <= 0:
        raise ValueError("dict_size must be positive.")
    return max(1, dict_size.bit_length())

def encode_progressive(int_array: list[int], start_dict_size: int, max_codelength: int = 16) -> str:
    if not int_array:
        return ""
    bitstr_parts = []
    dict_size = start_dict_size
    codelength = _initial_codelength(dict_size)
    for idx, num in enumerate(int_array):
        bitstr_parts.append(format(num, f'0{codelength}b'))
        if idx < len(int_array) - 1:
            if dict_size < (1 << max_codelength):
                dict_size += 1
                if dict_size == (1 << codelength):
                    codelength += 1
    return "".join(bitstr_parts)

def decode_progressive(
    encoded_text: str,
    start_dict_size: int,
    max_codelength: int,
    num_codes: int
) -> tuple[list[int], int]:
    if num_codes == 0:
        return [], 0
    int_codes = []
    dict_size = start_dict_size
    codelength = _initial_codelength(dict_size)
    i = 0
    if i + codelength > len(encoded_text):
        return [], 0
    int_codes.append(int(encoded_text[i:i + codelength], 2))
    i += codelength
    while len(int_codes) < num_codes:
        if dict_size < (1 << max_codelength):
            dict_size += 1
            if dict_size == (1 << codelength):
                codelength += 1
        if i + codelength > len(encoded_text):
            break
        int_codes.append(int(encoded_text[i:i + codelength], 2))
        i += codelength
    return int_codes, i

def pad_encoded_text(encoded_text: str) -> str:
    extra_padding = (8 - len(encoded_text) % 8) % 8
    padded_info = format(extra_padding, '08b')
    return padded_info + encoded_text + "0" * extra_padding

def remove_padding(padded_encoded_text: str) -> str:
    if len(padded_encoded_text) < 8:
        raise ValueError("Invalid padded string: at least 8 bits required.")
    extra_padding = int(padded_encoded_text[:8], 2)
    content = padded_encoded_text[8:]
    if extra_padding > 0:
        return content[:-extra_padding]
    return content

def get_byte_array(padded_encoded_text: str) -> bytearray:
    if len(padded_encoded_text) % 8 != 0:
        raise ValueError("String is not padded correctly (not a multiple of 8).")
    b = bytearray()
    for i in range(0, len(padded_encoded_text), 8):
        b.append(int(padded_encoded_text[i:i + 8], 2))
    return b