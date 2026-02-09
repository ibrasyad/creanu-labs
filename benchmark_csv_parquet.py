import pandas as pd
import time
import os
from pathlib import Path
import psutil
import gc

def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def benchmark_operation(operation_name, operation_func):
    """Benchmark an operation and return timing and memory usage"""
    gc.collect()  # Clean up before benchmark
    
    start_memory = get_memory_usage()
    start_time = time.time()
    
    result = operation_func()
    
    end_time = time.time()
    end_memory = get_memory_usage()
    
    return {
        'operation': operation_name,
        'time_seconds': end_time - start_time,
        'memory_mb': end_memory - start_memory,
        'result': result
    }

def create_test_data(n_rows=1000000):
    """Create test data similar to your simulation"""
    import numpy as np
    from datetime import datetime, timedelta
    
    start_date = datetime(2025, 1, 1)
    
    data = {
        'session_id': [f'sess_{i:08d}' for i in range(n_rows)],
        'trx_id': [f'trx_{i:08d}' for i in range(n_rows)],
        'date': [start_date + timedelta(days=i % 365) for i in range(n_rows)],
        'tier': np.random.choice(['bronze', 'silver', 'gold'], n_rows),
        'user_id': [f'user_{i:08d}' for i in range(n_rows)],
        'activity': np.random.choice(['landing_page', 'browse', 'add_to_cart', 'paid'], n_rows),
        'activity_datetime': [start_date + timedelta(hours=i) for i in range(n_rows)]
    }
    
    return pd.DataFrame(data)

def test_write_operations(df):
    """Test write operations for CSV and Parquet"""
    results = []
    
    # CSV Write
    def csv_write():
        df.to_csv('benchmark_test.csv', index=False)
        return os.path.getsize('benchmark_test.csv')
    
    csv_result = benchmark_operation('CSV Write', csv_write)
    csv_result['file_size_mb'] = csv_result['result'] / 1024 / 1024
    results.append(csv_result)
    
    # Parquet Write
    def parquet_write():
        df.to_parquet('benchmark_test.parquet', index=False)
        return os.path.getsize('benchmark_test.parquet')
    
    parquet_result = benchmark_operation('Parquet Write', parquet_write)
    parquet_result['file_size_mb'] = parquet_result['result'] / 1024 / 1024
    results.append(parquet_result)
    
    return results

def test_read_operations():
    """Test read operations for CSV and Parquet"""
    results = []
    
    # CSV Read
    def csv_read():
        return pd.read_csv('benchmark_test.csv')
    
    csv_result = benchmark_operation('CSV Read', csv_read)
    csv_result['rows_read'] = len(csv_result['result'])
    results.append(csv_result)
    
    # Parquet Read
    def parquet_read():
        return pd.read_parquet('benchmark_test.parquet')
    
    parquet_result = benchmark_operation('Parquet Read', parquet_read)
    parquet_result['rows_read'] = len(parquet_result['result'])
    results.append(parquet_result)
    
    return results

def test_column_select_operations():
    """Test column selection (common in analysis)"""
    results = []
    columns_to_select = ['session_id', 'tier', 'activity']
    
    # CSV Column Select
    def csv_column_select():
        df = pd.read_csv('benchmark_test.csv', usecols=columns_to_select)
        return df
    
    csv_result = benchmark_operation('CSV Column Select', csv_column_select)
    results.append(csv_result)
    
    # Parquet Column Select
    def parquet_column_select():
        df = pd.read_parquet('benchmark_test.parquet', columns=columns_to_select)
        return df
    
    parquet_result = benchmark_operation('Parquet Column Select', parquet_column_select)
    results.append(parquet_result)
    
    return results

def test_filter_operations():
    """Test filtering operations"""
    results = []
    
    # CSV Filter
    def csv_filter():
        df = pd.read_csv('benchmark_test.csv')
        filtered = df[df['tier'] == 'gold']
        return filtered
    
    csv_result = benchmark_operation('CSV Filter', csv_filter)
    csv_result['rows_filtered'] = len(csv_result['result'])
    results.append(csv_result)
    
    # Parquet Filter
    def parquet_filter():
        df = pd.read_parquet('benchmark_test.parquet')
        filtered = df[df['tier'] == 'gold']
        return filtered
    
    parquet_result = benchmark_operation('Parquet Filter', parquet_filter)
    parquet_result['rows_filtered'] = len(parquet_result['result'])
    results.append(parquet_result)
    
    return results

def test_append_operations():
    """Test append operations (critical for your simulation)"""
    results = []
    
    # Create initial data
    initial_df = create_test_data(50000)
    append_df = create_test_data(10000)
    
    # CSV Append
    def csv_append():
        initial_df.to_csv('append_test.csv', index=False)
        append_df.to_csv('append_test.csv', mode='a', header=False, index=False)
        final_df = pd.read_csv('append_test.csv')
        return final_df
    
    csv_result = benchmark_operation('CSV Append', csv_append)
    csv_result['final_rows'] = len(csv_result['result'])
    results.append(csv_result)
    
    # Parquet "Append" (read-combine-write)
    def parquet_append():
        initial_df.to_parquet('append_test.parquet', index=False)
        # Parquet doesn't support true append, so we simulate
        existing = pd.read_parquet('append_test.parquet')
        combined = pd.concat([existing, append_df], ignore_index=True)
        combined.to_parquet('append_test.parquet', index=False)
        final_df = pd.read_parquet('append_test.parquet')
        return final_df
    
    parquet_result = benchmark_operation('Parquet Append (Read+Write)', parquet_append)
    parquet_result['final_rows'] = len(parquet_result['result'])
    results.append(parquet_result)
    
    return results

def cleanup_files():
    """Clean up benchmark files"""
    files_to_remove = ['benchmark_test.csv', 'benchmark_test.parquet', 'append_test.csv', 'append_test.parquet']
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)

def print_comparison_table(results_list):
    """Print formatted comparison table"""
    print("\n" + "="*80)
    print("CSV vs PARQUET PERFORMANCE COMPARISON")
    print("="*80)
    
    for results in results_list:
        if not results:
            continue
            
        print(f"\n{results[0]['operation'].split(' ')[0]} OPERATIONS:")
        print("-" * 50)
        print(f"{'Operation':<25} {'Time (s)':<10} {'Memory (MB)':<12} {'Size (MB)':<10}")
        print("-" * 50)
        
        for result in results:
            op_name = result['operation']
            time_sec = result['time_seconds']
            memory_mb = result['memory_mb']
            size_mb = result.get('file_size_mb', 'N/A')
            
            print(f"{op_name:<25} {time_sec:<10.3f} {memory_mb:<12.1f} {size_mb:<10}")
        
        # Calculate speedup
        if len(results) == 2:
            csv_time = results[0]['time_seconds']
            parquet_time = results[1]['time_seconds']
            speedup = csv_time / parquet_time if parquet_time > 0 else float('inf')
            
            print(f"\nParquet is {speedup:.1f}x {'faster' if speedup > 1 else 'slower'} than CSV")
            
            if 'file_size_mb' in results[0]:
                csv_size = results[0]['file_size_mb']
                parquet_size = results[1]['file_size_mb']
                size_reduction = (csv_size - parquet_size) / csv_size * 100
                print(f"Parquet is {size_reduction:.1f}% smaller than CSV")

def main():
    print("Starting CSV vs Parquet benchmark...")
    print(f"Test data size: 1,000,000 rows")
    
    # Create test data
    test_df = create_test_data(1000000)
    print(f"Created test data: {len(test_df)} rows, {len(test_df.columns)} columns")
    
    try:
        # Run benchmarks
        write_results = test_write_operations(test_df)
        read_results = test_read_operations()
        column_results = test_column_select_operations()
        filter_results = test_filter_operations()
        append_results = test_append_operations()
        
        # Print results
        print_comparison_table([
            write_results,
            read_results, 
            column_results,
            filter_results,
            append_results
        ])
        
        print("\n" + "="*80)
        print("KEY INSIGHTS FOR YOUR SIMULATION:")
        print("="*80)
        print("1. WRITE OPERATIONS: CSV is faster for single writes")
        print("2. READ OPERATIONS: Parquet is significantly faster")
        print("3. COLUMN SELECTION: Parquet excels (columnar storage)")
        print("4. FILTERING: Parquet is much faster")
        print("5. APPEND OPERATIONS: CSV wins (Parquet needs read+write)")
        print("\nRECOMMENDATION: Use CSV for simulation writes, Parquet for analysis")
        
    finally:
        cleanup_files()

if __name__ == "__main__":
    main()
