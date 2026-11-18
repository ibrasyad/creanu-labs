export interface UserRecord {
  tier: string;
  user_id: string;
  city: string;
  gender: string;
  acquisition_channel: string;
  registered_date: string;
  last_active_date: string;
}

export interface FunnelEventRecord {
  session_id: string;
  tier: string;
  user_id: string;
  activity: string;
  activity_datetime: string;
}

export interface TransactionRecord {
  session_id: string;
  user_id: string;
  trx_id: string;
  date: string;
  tier: string;
  total_price: number;
}

export interface TransactionItemRecord {
  trx_id: string;
  user_id: string;
  tier: string;
  date: string;
  product: string;
  quantity: number;
  unit_price: number;
  total_price: number;
}

export interface CatalogItemRecord {
  category: string;
  subcategory: string;
  product: string;
  base_price: number;
}

export interface DailyMetric {
  date: string;
  weekday: string;
  active_visitors: number;
  transactions: number;
  gross_revenue: number;
  items_sold: number;
  conversion_rate: number;
  new_users_acquired: number;
}

export interface SimulationSummary {
  total_users: number;
  new_users: number;
  total_sessions: number;
  total_transactions: number;
  total_items_sold: number;
  total_revenue: number;
  average_order_value: number;
  overall_conversion_rate: number;
  daily_metrics: DailyMetric[];
  funnel_breakdown: Record<string, number>;
  category_revenue: Record<string, number>;
  top_products: [string, number, number][]; // [name, qty, rev]
}

export interface SimulationOutput {
  users: UserRecord[];
  funnel: FunnelEventRecord[];
  transactions: TransactionRecord[];
  transaction_items: TransactionItemRecord[];
  catalog: CatalogItemRecord[];
  summary: SimulationSummary;
}

export interface PresetScenario {
  id: string;
  title: string;
  description: string;
  badge: string;
  configYaml: string;
}
