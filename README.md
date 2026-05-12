# Lettuce-Melon

## Objective

I built Lettuce-Melon to solve a common problem in data analytics: realistic transaction data. When you're learning analytics business intelligence tools, you need data that behaves like real customer behavior, not just random numbers. Though I don't claim this would show perfect real world behavior, it's a good starting point for learning.

## Method

The system uses a multi-layered simulation approach that models how different customer types actually shop. I segment customers into three main profiles (conservative, balanced, aggressive) with varying group behaviors and distinct shopping patterns, category preferences, and spending habits. Each group has its own probability distributions for basket size, product selection, and purchase frequency.

The temporal modeling accounts for weekly patterns (weekend vs weekday shopping) and seasonal variations (like holiday shopping spikes). I also model user lifecycle, including new customer acquisition and how their behavior evolves over time.

## Library

I built this with Python using pandas for data manipulation, scipy for statistical distributions, and pyarrow for efficient Parquet output. The configuration is entirely YAML-based, making it easy to adjust parameters without touching code. Well, also the biggest reason is that YAML is the only thing I'm familiar with, BUT it is also human-readable and version-controlled friendly.

## Output

The system generates multiple interconnected datasets:

- **Transaction headers** with session metadata and customer tier
- **Transaction items** with detailed product line items, quantities, and pricing
- **User analytics** tracking acquisition dates, transaction history, and total spending
- **Funnel data** for customer journey analysis and conversion tracking
- **Daily new user acquisition** with tier distribution

All data is output as Parquet files for efficient storage and fast querying. Ideally, I would like to connect this to a database, but I don't want to spend any cost on this project, so I'll leave it as is using free tools for now

## Use Case

I use this primarily for testing data pipelines and analytics systems. It's perfect for:

- Load testing your database with realistic query patterns
- Developing and validating BI dashboards
- Building machine learning models for customer segmentation
- Demonstrating data engineering capabilities in portfolio projects

The configurable nature means you can adjust everything from product catalog to customer behavior patterns to match your specific testing needs.