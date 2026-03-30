# min_code - Minimal Binary Serialization

A lightweight, efficient binary serialization module for MicroPython.

## Overview

`min_code` provides fast encoding/decoding of Python data structures to/from a compact binary format. Supports integers, floats, strings, bytes, lists, dicts, and None.

Designed to take up very little bytecode space. You can still easily extend it if you want more data types.

## Functions

### `encode(v, stream=None)`
Serialize a Python value to binary format.

**Parameters:**
- `v` - Value to encode (int, float, str, bytes, list, dict, None)
- `stream` - Optional writeable stream. If omitted, returns `bytes`.

**Returns:** `bytes` if `stream` is None, otherwise `None`.

```python
data = min_code.encode({"name": "test", "value": 42})
```

### `decode(src)`
Deserialize binary data back to a Python value.

**Parameters:**
- `src` - `bytes` object or readable stream

**Returns:** Decoded Python value

**Raises:** `ValueError` on invalid input

```python
obj = min_code.decode(data)
```

## Supported Types

| Type | Notes |
|------|-------|
| `int` | Any size (optimized for small ints) |
| `float` | 32-bit precision |
| `str` | UTF-8 encoded |
| `bytes` / `bytearray` | Raw binary data |
| `list` / `tuple` | Sequences (tuples decode as lists) |
| `dict` | Keys/values can be any supported type |
| `None` | |
| `bool` | Encoded as 0/1 integers, decode as int |

## Examples

```python
import min_code

# Encode to bytes
data = min_code.encode([1, 2.5, "hello", None])

# Decode back
result = min_code.decode(data)
print(result)  # [1, 2.5, 'hello', None]

# Stream encoding
import io
stream = io.BytesIO()
min_code.encode({"a": 100, "b": 200}, stream)
stream.seek(0)
obj = min_code.decode(stream)

# Nested structures
complex_data = {
    "items": [1, 2, 3],
    "metadata": {"version": 1, "active": True}
}
packed = min_code.encode(complex_data)
```

## Performance Notes

- Compact format: small ints use 1 byte, larger ints use 2-5 bytes
- Strings ≤13 bytes stored inline; larger strings use length prefix
- 32-bit floats only (not 64-bit)
- Booleans encode as integers; decode as `0`/`1`, not `True`/`False`

## Binary Format (Reference)

- Version header: `0x3E 0x00`
- End marker: `0x3F`
- Small ints: `0x40-0x7F` (value - 0x80)
- Strings/bytes: type nibble + length (0-13 inline, 0x0E = 1-byte length, 0x0F = 4-byte length)
- Lists/dicts: start marker (`0x30`/`0x31`) followed by items, end with `0x32`

# License

2026 shea m puckett
MIT license

