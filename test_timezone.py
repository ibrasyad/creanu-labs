import pandas as pd
import numpy as np
from datetime import datetime

# Test timezone conversion behavior
print("=== Testing timezone conversion behavior ===")

# Test 1: Timezone-aware datetime (assuming it's in UTC)
print("\n1. Timezone-aware datetime:")
utc_time = pd.Series([pd.Timestamp('2026-01-01 17:00:00', tz='UTC')])
print(f"Original UTC time: {utc_time.iloc[0]}")

# Current method - just tz_convert
converted_current = utc_time.dt.tz_convert('Asia/Bangkok').dt.tz_localize(None)
print(f"Current method result: {converted_current.iloc[0]}")

# Correct method - convert to UTC+7 time values
converted_correct = utc_time.dt.tz_convert('Asia/Bangkok')
print(f"Correct method (with tz): {converted_correct.iloc[0]}")
converted_correct_naive = converted_correct.dt.tz_localize(None)
print(f"Correct method (naive): {converted_correct_naive.iloc[0]}")

# Test 2: Timezone-naive datetime (assuming it's in UTC)
print("\n2. Timezone-naive datetime (assuming UTC):")
naive_time = pd.Series([pd.Timestamp('2026-01-01 17:00:00')])
print(f"Original naive time: {naive_time.iloc[0]}")

# Current method - just tz_localize
converted_current_naive = naive_time.dt.tz_localize('Asia/Bangkok').dt.tz_localize(None)
print(f"Current method result: {converted_current_naive.iloc[0]}")

# Correct method - first assume UTC, then convert to UTC+7
converted_correct_naive2 = naive_time.dt.tz_localize('UTC').dt.tz_convert('Asia/Bangkok').dt.tz_localize(None)
print(f"Correct method (UTC->UTC+7): {converted_correct_naive2.iloc[0]}")

print(f"\n=== Summary ===")
print(f"If you want 17:00:00 UTC to become 00:00:00 UTC+7 (next day), you need to add 7 hours")
print(f"If you want 17:00:00 to stay 17:00:00 but be labeled as UTC+7, current method is correct")
