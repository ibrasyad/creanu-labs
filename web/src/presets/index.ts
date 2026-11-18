import yaml from 'js-yaml';
import { PresetScenario } from '../types/simulation';
import { DEFAULT_CONFIG_YAML } from '../engine/defaultConfig';

function createPreset(mutator: (cfg: any) => void): string {
  const cloned = yaml.load(DEFAULT_CONFIG_YAML) as any;
  mutator(cloned);
  return yaml.dump(cloned);
}

export const PRESET_SCENARIOS: PresetScenario[] = [
  {
    id: 'default',
    title: 'Balanced Supermarket Baseline',
    description: 'Standard retail mix of family shoppers, students, and health-conscious patrons.',
    badge: 'Baseline',
    configYaml: DEFAULT_CONFIG_YAML,
  },
  {
    id: 'weekend_rush',
    title: 'Weekend Family Supermarket Rush',
    description: 'Surge in Saturday & Sunday traffic with massive baskets (8–15 items) and family staple shopping.',
    badge: 'High AOV',
    configYaml: createPreset((cfg) => {
      if (cfg.tiers?.family_shoppers) {
        cfg.tiers.family_shoppers.base_user = 50;
        cfg.tiers.family_shoppers.basket = { min_items: 8, max_items: 16 };
        if (cfg.tiers.family_shoppers.visit_chance) {
          cfg.tiers.family_shoppers.visit_chance.saturday = 0.35;
          cfg.tiers.family_shoppers.visit_chance.sunday = 0.30;
        }
      }
    }),
  },
  {
    id: 'health_wave',
    title: 'Healthy Living & Organic Wave',
    description: 'Heavy preference for leafy greens, berries, and citrus with frequent daily store visits.',
    badge: 'High Frequency',
    configYaml: createPreset((cfg) => {
      if (cfg.tiers?.health_conscious) {
        cfg.tiers.health_conscious.base_user = 60;
        cfg.tiers.health_conscious.daily_new_user_chance = 0.25;
        if (cfg.tiers.health_conscious.category_weight) {
          cfg.tiers.health_conscious.category_weight.vegetables = 3.5;
          cfg.tiers.health_conscious.category_weight.fruits = 2.5;
        }
      }
    }),
  },
  {
    id: 'student_quick',
    title: 'Student & Young Pro Quick-Bites',
    description: 'Budget-friendly quick convenience shopping. Rapid checkout, small basket sizes, weekday traffic.',
    badge: 'High Conversion',
    configYaml: createPreset((cfg) => {
      if (cfg.tiers?.students) {
        cfg.tiers.students.base_user = 75;
        cfg.tiers.students.basket = { min_items: 1, max_items: 3 };
      }
      if (cfg.funnel?.checkout) {
        cfg.funnel.checkout.conversion_rate = 0.88;
      }
    }),
  },
  {
    id: 'holiday_surge',
    title: 'Holiday Harvest & Festive Surge',
    description: 'Year-end holiday spike in berries, tropical fruits, and large family celebration baskets.',
    badge: 'Peak GMV',
    configYaml: createPreset((cfg) => {
      if (cfg.date) {
        cfg.date.start_date = '2026-12-15';
        cfg.date.end_date = '2026-12-31';
        if (cfg.date.transaction_volume?.monthly_rate) {
          cfg.date.transaction_volume.monthly_rate.december = 1.6;
        }
      }
      if (cfg.catalog?.fruits?.berries?.product?.strawberries) {
        cfg.catalog.fruits.berries.product.strawberries.base_price = 14000;
        cfg.catalog.fruits.berries.product.strawberries.weight = 2.5;
      }
    }),
  },
];
