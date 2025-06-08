import json
import random
import time
import pandas as pd
import polars as pl
from pathlib import Path

NUM_TRIALS = 1_000_000
SYMBOLS_JSON = Path("symbols.json")

# Load symbols
with SYMBOLS_JSON.open("r") as f:
    symbol_dict = json.load(f)

symbols = list(symbol_dict.keys())
ids = list(symbol_dict.values())

# Generate random lookup list
random.seed(42)
lookup_symbols = [random.choice(symbols) for _ in range(NUM_TRIALS)]

symbol_map = dict(symbol_dict)  # already symbol → id

start = time.perf_counter()
for symbol in lookup_symbols:
    result = symbol_map[symbol]
end = time.perf_counter()
print(f"Python dict avg lookup time: {(end - start) * 1e9 / NUM_TRIALS:.2f} ns")

