# Customer Tier Configurations

Each YAML file in this directory defines a customer tier with its own shopping behavior, preferences, and growth patterns.

## Adding a New Tier

1. Copy `_template.yaml`:
   ```bash
   cp _template.yaml your_tier_name.yaml
   ```

2. Edit `your_tier_name.yaml`:
   - Replace `template:` with your tier name (e.g., `luxury_tier:`)
   - Adjust the configuration values:
     - `base_user`: Starting number of users
     - `daily_retry`: Number of chances per day to create new users (1-10)
     - `daily_new_user_chance`: Probability per retry on weekdays (0.0-1.0)
     - `daily_new_user_chance_weekend`: Probability per retry on weekends
     - `basket`: Min/max items per transaction
     - `category_weight`: Shopping preferences (higher = more likely)
     - `quantity_bias`: Units per item multiplier for each category
     - `transaction_weight`: Activity by day of week

3. Save the file - it will automatically be loaded on the next run!

## Configuration Values Explained

### Daily User Growth
- `daily_retry: 3` + `daily_new_user_chance: 0.1` = 3 independent 10% chances each day
- Expected new users per day ≈ 3 × 0.1 = 0.3 (but can vary 0-3+)

### Noise
- `daily_new_user_noise`: Adds ±15% variance to probabilities (multiplier: 1.15)
- `monthly_new_user_noise`: Monthly volatility

### Example: Budget Tier
- More frequent but smaller purchases
- Higher preference for staples (vegetables, grains)
- Lower preference for premium items (seafood, meat)

