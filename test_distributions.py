"""
Test script to compare triangular and Bounded Normal distributions
"""
import pandas as pd
import numpy as np
from scipy.stats import beta, truncnorm
import matplotlib.pyplot as plt

def generate_triangular_distribution(min_val, avg_val, max_val, size=1000):
    """
    Generate random numbers from a triangular distribution.
    NOTE: Mean will be (min + mode + max) / 3, NOT avg_val!
    """
    return np.random.triangular(left=min_val, mode=avg_val, right=max_val, size=size)


def generate_normal_distribution_with_bounds(min_val, avg_val, max_val, std_dev=None, size=1000):
    """
    Generate random numbers from a NORMAL distribution with specified mean.
    Optional soft bounds (clips outliers but mean stays at avg_val).
    
    Args:
        min_val: Soft minimum (clips values below this)
        avg_val: Mean (target average) - THIS is where the mean will be!
        max_val: Soft maximum (clips values above this)
        std_dev: Standard deviation. If None, calculated as 1/6 of range (68% within bounds)
        size: Number of samples
    
    Returns:
        Array of random numbers, clipped to [min_val, max_val]
    """
    if std_dev is None:
        # Default: std_dev such that 3*std_dev = range (99.7% within bounds)
        std_dev = (max_val - min_val) / 6.0
    
    # Generate normal distribution centered at avg_val
    data = np.random.normal(loc=avg_val, scale=std_dev, size=size)
    
    # Clip to bounds
    return np.clip(data, min_val, max_val)


def print_stats(data, name):
    """Print statistics for a distribution"""
    print(f"\n{name}:")
    print(f"  Mean:     {np.mean(data):.2f}")
    print(f"  Median:   {np.median(data):.2f}")
    print(f"  Std Dev:  {np.std(data):.2f}")
    print(f"  Min:      {np.min(data):.2f}")
    print(f"  Max:      {np.max(data):.2f}")
    print(f"  Skewness: {beta.stats(2, 2, moments='s'):.4f}")


# Test parameters
min_val = 10
avg_val = 180
max_val = 3600
size = 30000

print("="*60)
print("DISTRIBUTION COMPARISON")
print("="*60)
print(f"\nParameters: min={min_val}, avg={avg_val}, max={max_val}, samples={size}")

# Generate samples
triangular_data = generate_triangular_distribution(min_val, avg_val, max_val, size)
normal_bounded_data = generate_normal_distribution_with_bounds(min_val, avg_val, max_val, std_dev=None, size=size)

# Print statistics
print_stats(triangular_data, "TRIANGULAR DISTRIBUTION")
print_stats(normal_bounded_data, "NORMAL DISTRIBUTION (CLIPPED)")

#export noaml_bounded_data to csv
df = pd.DataFrame(normal_bounded_data, columns=['value'])
df.to_csv('/workspaces/lettuce-melon/normal_bounded_data.csv', index=False)
print("\n✓ Normal bounded data exported to: normal_bounded_data.csv")

# Create visualization
plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.hist(triangular_data, bins=50, alpha=0.7, edgecolor='black', color='blue')
plt.axvline(np.mean(triangular_data), color='red', linestyle='--', linewidth=2, label=f'Actual Mean: {np.mean(triangular_data):.2f}')
plt.axvline(avg_val, color='green', linestyle='--', linewidth=2, label=f'Target Mode: {avg_val}')
plt.xlabel('Value')
plt.ylabel('Frequency')
plt.title('Triangular Distribution\n(Mean ≠ Mode)')
plt.legend()
plt.grid(alpha=0.3)

plt.subplot(1, 2, 2)
plt.hist(normal_bounded_data, bins=50, alpha=0.7, edgecolor='black', color='orange')
plt.axvline(np.mean(normal_bounded_data), color='red', linestyle='--', linewidth=2, label=f'Actual Mean: {np.mean(normal_bounded_data):.2f}')
plt.axvline(avg_val, color='green', linestyle='--', linewidth=2, label=f'Target Mean: {avg_val}')
plt.xlabel('Value')
plt.ylabel('Frequency')
plt.title('Normal Distribution (Clipped)\n(Mean ≈ Mode)')
plt.legend()
plt.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('/workspaces/lettuce-melon/distribution_comparison.png', dpi=100, bbox_inches='tight')
print("\n✓ Visualization saved to: distribution_comparison.png")
print("="*60)
