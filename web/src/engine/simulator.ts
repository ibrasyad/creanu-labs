import yaml from 'js-yaml';
import {
  SimulationOutput,
  SimulationSummary,
  UserRecord,
  FunnelEventRecord,
  TransactionRecord,
  TransactionItemRecord,
  CatalogItemRecord,
  DailyMetric,
} from '../types/simulation';

// Fast deterministic pseudo-random number generator (Mulberry32)
function mulberry32(seed: number) {
  return function () {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function sampleTriangular(min: number, max: number, mode: number, rand: () => number): number {
  const f = (mode - min) / (max - min);
  const u = rand();
  return u <= f ? min + Math.sqrt(u * (max - min) * (mode - min)) : max - Math.sqrt((1 - u) * (max - min) * (max - mode));
}

// Standard normal via Box-Muller
function sampleNormal(mean: number, stdDev: number, rand: () => number): number {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  return mean + stdDev * Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

// Bounded beta sample whose expected value is `mean` (mirrors sim/utils.py controlled_random)
function controlledRandom(mean: number, min: number, max: number, rand: () => number): number {
  if (![mean, min, max].every(Number.isFinite) || min > max || mean < min || mean > max) {
    throw new Error('Stage duration must satisfy min_duration <= avg_duration <= max_duration');
  }
  if (min === max) return min;
  const position = (mean - min) / (max - min);
  if (position === 0) return min;
  if (position === 1) return max;
  const concentration = 6.0;
  const a = position * concentration;
  const b = (1 - position) * concentration;
  // Marsaglia-Tsang gamma sampling for beta(a, b)
  const gamma = (shape: number): number => {
    if (shape < 1) return gamma(shape + 1) * Math.pow(Math.max(rand(), 1e-9), 1 / shape);
    const d = shape - 1 / 3;
    const c = 1 / Math.sqrt(9 * d);
    for (;;) {
      let x: number;
      let v: number;
      do {
        x = sampleNormal(0, 1, rand);
        v = 1 + c * x;
      } while (v <= 0);
      v = v * v * v;
      const u = Math.max(rand(), 1e-9);
      if (u < 1 - 0.0331 * x * x * x * x) return d * v;
      if (Math.log(u) < 0.5 * x * x + d * (1 - v + Math.log(v))) return d * v;
    }
  };
  const ga = gamma(a);
  const gb = gamma(b);
  const beta = ga / (ga + gb || 1);
  return min + (max - min) * beta;
}

// Mean-one multiplicative noise (mirrors sim/utils.py apply_noise)
function applyNoise(value: number, noiseCfg: any, rand: () => number): number {
  if (!noiseCfg) return value;
  const cv = Math.max(0, Number(noiseCfg.multiplier ?? 1) - 1);
  if (cv === 0) return value;
  const distribution = noiseCfg.distribution || 'lognormal';
  if (distribution === 'uniform') {
    return value * (Math.max(0, 1 - cv) + rand() * 2 * cv);
  }
  if (!['poisson', 'normal', 'lognormal'].includes(distribution)) {
    throw new Error(`Unsupported noise distribution: ${distribution}`);
  }
  const sigma = Math.sqrt(Math.log1p(cv * cv));
  return value * Math.exp(sampleNormal(-0.5 * sigma * sigma, sigma, rand));
}

// Visit decay lookup (mirrors sim/generate_funnel.py get_visit_decay_multiplier)
function getVisitDecayMultiplier(daysSinceLastVisit: number, visitDecay: any): number {
  if (!Array.isArray(visitDecay) || visitDecay.length === 0) return 1.0;
  const rules = [...visitDecay].sort((a, b) => Number(a.days) - Number(b.days));
  let multiplier = Number(rules[0].multiplier ?? 1.0);
  for (const rule of rules) {
    if (daysSinceLastVisit >= Number(rule.days)) multiplier = Number(rule.multiplier ?? 1.0);
    else break;
  }
  return multiplier;
}

// Weighted peak-hour pick (mirrors sim/generate_funnel.py generate_landing_datetime)
function sampleVisitHour(peaks: any, rand: () => number): number {
  const entries = peaks && typeof peaks === 'object' ? Object.values<any>(peaks) : [];
  if (entries.length === 0) {
    return Math.min(23, Math.max(0, Math.round(sampleNormal(19, 2, rand))));
  }
  const weights: [any, number][] = entries.map((p) => [p, Number(p?.weight ?? 1)]);
  const peak = weightedChoice(weights, rand);
  const hourCfg = peak?.hour || {};
  const min = Number(hourCfg.min ?? 0);
  const max = Number(hourCfg.max ?? 23);
  const avg = Number(hourCfg.avg ?? 19);
  return Math.min(max, Math.max(min, Math.round(sampleNormal(avg, 2, rand))));
}

// Poisson sample (Knuth) for small lambdas, normal approximation for large
function poissonSample(lambda: number, rand: () => number): number {
  if (!(lambda > 0)) return 0;
  if (lambda > 30) {
    return Math.max(0, Math.round(sampleNormal(lambda, Math.sqrt(lambda), rand)));
  }
  const L = Math.exp(-lambda);
  let k = 0;
  let p = 1;
  do {
    k++;
    p *= rand();
  } while (p > L);
  return k - 1;
}

function formatDateTime(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())} ${pad(
    d.getUTCHours()
  )}:${pad(d.getUTCMinutes())}:${pad(d.getUTCSeconds())}`;
}

function addSeconds(d: Date, seconds: number): Date {
  return new Date(d.getTime() + Math.max(0, Math.round(seconds)) * 1000);
}

function weightedChoice<T>(items: [T, number][], rand: () => number): T {
  const total = items.reduce((sum, item) => sum + (item[1] > 0 ? item[1] : 0), 0);
  if (total <= 0) return items[0][0];
  let roll = rand() * total;
  for (const [val, weight] of items) {
    if (weight <= 0) continue;
    if (roll < weight) return val;
    roll -= weight;
  }
  return items[items.length - 1][0];
}

// ============================================================================
// GROWTH & EVENT MULTIPLIERS (Exact mapping from sim/growth.py & sim/event.py)
// ============================================================================

function getSimulationYear(current: Date, start: Date): number {
  let year = current.getUTCFullYear() - start.getUTCFullYear() + 1;
  if (
    current.getUTCMonth() < start.getUTCMonth() ||
    (current.getUTCMonth() === start.getUTCMonth() && current.getUTCDate() < start.getUTCDate())
  ) {
    year -= 1;
  }
  return Math.max(1, year);
}

function getGrowthMultiplier(
  current: Date,
  simStart: Date,
  growthCfg: any,
  profile: string,
  metric: 'new_user' | 'visit' | 'conversion'
): number {
  if (!growthCfg) return 1.0;
  const simYear = getSimulationYear(current, simStart);
  const yearlyCfg = growthCfg.yearly || {};
  const yearKey = `year_${simYear}`;
  const yearly = yearlyCfg[yearKey] || yearlyCfg['year_8_plus'] || {};
  const base = growthCfg.base || {};

  const baseOverall = Number(base.overall?.[metric] ?? 1.0);
  const baseProfile = Number(base.tier_profiles?.[profile]?.[metric] ?? 1.0);
  const yearlyOverall = Number(yearly.overall?.[metric] ?? 1.0);
  const yearlyProfile = Number(yearly.profile_multipliers?.[profile]?.[metric] ?? 1.0);

  return baseOverall * baseProfile * yearlyOverall * yearlyProfile;
}

function getEventMultiplier(
  eventsCfg: any,
  simYear: number,
  currentMonth: number,
  tierName: string,
  profile: string,
  metric: 'new_user' | 'visit' | 'conversion',
  funnelStep?: string
): number {
  if (!eventsCfg || typeof eventsCfg !== 'object') return 1.0;
  let mult = 1.0;

  for (const event of Object.values<any>(eventsCfg)) {
    if (!event || event.year !== simYear) continue;
    const startM = event.start_month || 1;
    const endM = event.end_month || 12;
    if (currentMonth < startM || currentMonth > endM) continue;

    let target = event.tiers?.[tierName]?.[metric];
    if (target === undefined && profile) {
      target = event.profiles?.[profile]?.[metric];
    }
    if (target === undefined) {
      target = event.overall?.[metric];
    }

    if (typeof target === 'number') {
      mult *= target;
    } else if (typeof target === 'object' && funnelStep && target[funnelStep] !== undefined) {
      mult *= Number(target[funnelStep]);
    }
  }

  return mult;
}

export type SimulatorProgress = (day: number, totalDays: number, dateStr: string) => void;

export function runSimulationClient(
  configYaml: string,
  onProgress?: SimulatorProgress
): SimulationOutput {
  const cfg = yaml.load(configYaml) as any;
  const baseSeed = Number(cfg?.simulation?.random_seed ?? 20260101);
  let globalRng = mulberry32(baseSeed);

  const startDateStr: string = cfg?.date?.start_date || '2026-01-01';
  const endDateStr: string = cfg?.date?.end_date || '2026-03-31'; // Default 90 days

  const startDate = new Date(startDateStr);
  const endDate = new Date(endDateStr);
  const totalDays = Math.max(1, Math.round((endDate.getTime() - startDate.getTime()) / (1000 * 3600 * 24)) + 1);

  // Flatten Catalog (all 19 categories from catalog.yaml)
  const catalogRecords: CatalogItemRecord[] = [];
  const catalogMap: Record<string, Record<string, { cooldown: number; products: Record<string, { base_price: number; weight: number }> }>> = {};

  if (cfg.catalog) {
    for (const [catName, subcats] of Object.entries<any>(cfg.catalog)) {
      catalogMap[catName] = {};
      for (const [subcatName, subcat] of Object.entries<any>(subcats)) {
        catalogMap[catName][subcatName] = {
          cooldown: subcat.cooldown || 1,
          products: {},
        };
        for (const [prodName, prod] of Object.entries<any>(subcat.product || {})) {
          catalogMap[catName][subcatName].products[prodName] = {
            base_price: prod.base_price,
            weight: prod.weight || 1.0,
          };
          catalogRecords.push({
            category: catName,
            subcategory: subcatName,
            product: prodName,
            base_price: prod.base_price,
          });
        }
      }
    }
  }

  const allCategoryNames = Object.keys(catalogMap);

  // 1. Generate Base Users
  const users: UserRecord[] = [];
  let userCounter = 1;
  const cities = [['Jakarta', 0.5], ['Surabaya', 0.2], ['Bandung', 0.15], ['Medan', 0.1], ['Semarang', 0.05]] as [string, number][];
  const genders = [['Female', 0.6], ['Male', 0.4]] as [string, number][];
  const channels = [['Organic Search', 0.35], ['Social Media', 0.3], ['Referral', 0.2], ['Direct', 0.15]] as [string, number][];

  for (const [tierName, tierCfg] of Object.entries<any>(cfg.tiers || {})) {
    const baseCount = Number(tierCfg.base_user || 10);
    for (let i = 0; i < baseCount; i++) {
      users.push({
        tier: tierName,
        user_id: `usr-${String(userCounter++).padStart(6, '0')}`,
        city: weightedChoice(cities, globalRng),
        gender: weightedChoice(genders, globalRng),
        acquisition_channel: weightedChoice(channels, globalRng),
        registered_date: startDateStr,
        last_active_date: startDateStr,
      });
    }
  }

  const allFunnel: FunnelEventRecord[] = [];
  const allTrx: TransactionRecord[] = [];
  const allItems: TransactionItemRecord[] = [];
  const dailyMetrics: DailyMetric[] = [];

  const purchaseHistory = new Map<string, Date>(); // key: `${userId}:${cat}:${subcat}`
  const lastVisitByUser = new Map<string, Date>();
  let totalRevenue = 0;
  let totalItemsSold = 0;
  const funnelCounts: Record<string, number> = {};
  const categoryRevenue: Record<string, number> = {};
  const productStats = new Map<string, { qty: number; rev: number }>();

  // 2. Iterate Day by Day
  const current = new Date(startDate);
  let dayIdx = 0;

  while (current <= endDate) {
    const dateStr = current.toISOString().slice(0, 10);
    const dateSeed = (baseSeed + dayIdx * 7919) >>> 0;
    const dayRng = mulberry32(dateSeed);

    const weekday = current.toLocaleDateString('en-US', { weekday: 'long', timeZone: 'UTC' }).toLowerCase();
    const isWeekend = weekday === 'saturday' || weekday === 'sunday';
    const currentMonthNum = current.getUTCMonth() + 1;
    const currentMonthName = current.toLocaleDateString('en-US', { month: 'long', timeZone: 'UTC' }).toLowerCase();
    const simYear = getSimulationYear(current, startDate);

    // Monthly transaction-volume multiplier (config/date.yaml → transaction_volume)
    const monthlyRateCfg = cfg.date?.transaction_volume?.monthly_rate;
    const monthlyRate = Number(monthlyRateCfg?.[currentMonthName] ?? 1.0);
    const monthlyNoiseCfg = cfg.date?.transaction_volume?.monthly_rate_noise;
    const monthlyVolumeMultiplier = applyNoise(monthlyRate, monthlyNoiseCfg, dayRng);

    // A. Daily new user acquisition with growth and event multipliers
    let newUsersToday = 0;
    for (const [tierName, tierCfg] of Object.entries<any>(cfg.tiers || {})) {
      const profile = tierCfg.profile || 'balanced';
      let chance = isWeekend
        ? (tierCfg.daily_new_user_chance_weekend ?? tierCfg.daily_new_user_chance ?? 0.1)
        : (tierCfg.daily_new_user_chance ?? 0.1);

      // Apply growth and event multipliers
      chance *= getGrowthMultiplier(current, startDate, cfg.growth, profile, 'new_user');
      chance *= getEventMultiplier(cfg.event, simYear, currentMonthNum, tierName, profile, 'new_user');

      const retries = tierCfg.daily_retry || 3;
      for (let r = 0; r < retries; r++) {
        if (dayRng() < chance) {
          users.push({
            tier: tierName,
            user_id: `usr-${String(userCounter++).padStart(6, '0')}`,
            city: weightedChoice(cities, dayRng),
            gender: weightedChoice(genders, dayRng),
            acquisition_channel: weightedChoice(channels, dayRng),
            registered_date: dateStr,
            last_active_date: dateStr,
          });
          newUsersToday++;
        }
      }
    }

    // B. Simulate Visits & Funnels
    let dayVisitors = 0;
    let dayTrxCount = 0;
    let dayRevenue = 0;
    let dayItemsCount = 0;
    let sessionCounter = 1;
    const activeUserIndices: number[] = [];

    const datePrefix = dateStr.replace(/-/g, '');

    for (let uIdx = 0; uIdx < users.length; uIdx++) {
      const u = users[uIdx];
      const tierCfg = cfg.tiers?.[u.tier] || {};
      const profile = tierCfg.profile || 'balanced';

      // Visit chance
      let visitChance = tierCfg.visit_chance?.[weekday] ?? (isWeekend ? 0.08 : 0.05);
      visitChance *= getGrowthMultiplier(current, startDate, cfg.growth, profile, 'visit');
      visitChance *= getEventMultiplier(cfg.event, simYear, currentMonthNum, u.tier, profile, 'visit');
      visitChance *= monthlyVolumeMultiplier;

      // Engagement decay based on recency, with a small reactivation floor
      const lastVisit = lastVisitByUser.get(u.user_id) || new Date(u.registered_date);
      const daysSinceLastVisit = Math.max(
        0,
        Math.round((current.getTime() - lastVisit.getTime()) / (1000 * 3600 * 24))
      );
      const decay = getVisitDecayMultiplier(daysSinceLastVisit, cfg.simulation?.visit_decay);
      visitChance *= decay;
      if (decay <= 0) {
        visitChance = Math.max(visitChance, Number(cfg.simulation?.reactivation_probability ?? 0.002));
      }

      if (dayRng() < visitChance) {
        dayVisitors++;
        activeUserIndices.push(uIdx);
        lastVisitByUser.set(u.user_id, new Date(current));
        const sessionId = `${datePrefix}-${String(sessionCounter++).padStart(8, '0')}`;

        // Hour of visit from configured peak-hour weights
        const peaks = {
          ...(cfg.funnel?.visit_hour_peak || {}),
          ...(tierCfg.visit_hour_peak || {}),
        };
        const hour = sampleVisitHour(peaks, dayRng);
        const minute = Math.floor(dayRng() * 60);
        const sec = Math.floor(dayRng() * 60);
        const landingDate = new Date(current);
        landingDate.setUTCHours(hour, minute, sec, 0);
        const landingDt = formatDateTime(landingDate);

        // 1. landing_page
        allFunnel.push({
          session_id: sessionId,
          tier: u.tier,
          user_id: u.user_id,
          activity: 'landing_page',
          activity_datetime: landingDt,
        });
        funnelCounts['landing_page'] = (funnelCounts['landing_page'] || 0) + 1;

        // Funnel progression with conversion multipliers
        const convGrowth = getGrowthMultiplier(current, startDate, cfg.growth, profile, 'conversion');
        const noiseCfg = tierCfg.funnel_noise ?? cfg.funnel?.funnel_noise;

        let convProductView = (tierCfg.landing_page?.conversion_rate ?? cfg.funnel?.landing_page?.conversion_rate ?? 0.65) * convGrowth;
        convProductView *= getEventMultiplier(cfg.event, simYear, currentMonthNum, u.tier, profile, 'conversion', 'landing_page');
        convProductView = applyNoise(convProductView, noiseCfg, dayRng);

        let convAddToCart = (tierCfg.product_view?.conversion_rate ?? cfg.funnel?.product_view?.conversion_rate ?? 0.50) * convGrowth;
        convAddToCart *= getEventMultiplier(cfg.event, simYear, currentMonthNum, u.tier, profile, 'conversion', 'product_view');
        convAddToCart = applyNoise(convAddToCart, noiseCfg, dayRng);

        let convCheckout = (tierCfg.add_to_cart?.conversion_rate ?? cfg.funnel?.add_to_cart?.conversion_rate ?? 0.60) * convGrowth;
        convCheckout *= getEventMultiplier(cfg.event, simYear, currentMonthNum, u.tier, profile, 'conversion', 'add_to_cart');
        convCheckout = applyNoise(convCheckout, noiseCfg, dayRng);

        let convPaid = (tierCfg.checkout?.conversion_rate ?? cfg.funnel?.checkout?.conversion_rate ?? 0.70) * convGrowth;
        convPaid *= getEventMultiplier(cfg.event, simYear, currentMonthNum, u.tier, profile, 'conversion', 'checkout');
        convPaid = applyNoise(convPaid, noiseCfg, dayRng);

        // Stage dwell time (config/funnel.yaml → duration)
        const stageDuration = (step: string): number => {
          const dur = {
            ...(cfg.funnel?.[step]?.duration || {}),
            ...(tierCfg[step]?.duration || {}),
          };
          if (!dur) return 0;
          return controlledRandom(
            Number(dur.avg_duration ?? 10),
            Number(dur.min_duration ?? 5),
            Number(dur.max_duration ?? 60),
            dayRng
          );
        };

        let reachedPaid = false;
        let eventDate = landingDate;
        let eventDt = landingDt;

        if (dayRng() < convProductView) {
          eventDate = addSeconds(eventDate, stageDuration('landing_page'));
          eventDt = formatDateTime(eventDate);
          allFunnel.push({ session_id: sessionId, tier: u.tier, user_id: u.user_id, activity: 'product_view', activity_datetime: eventDt });
          funnelCounts['product_view'] = (funnelCounts['product_view'] || 0) + 1;

          if (dayRng() < convAddToCart) {
            eventDate = addSeconds(eventDate, stageDuration('product_view'));
            eventDt = formatDateTime(eventDate);
            allFunnel.push({ session_id: sessionId, tier: u.tier, user_id: u.user_id, activity: 'add_to_cart', activity_datetime: eventDt });
            funnelCounts['add_to_cart'] = (funnelCounts['add_to_cart'] || 0) + 1;

            if (dayRng() < convCheckout) {
              eventDate = addSeconds(eventDate, stageDuration('add_to_cart'));
              eventDt = formatDateTime(eventDate);
              allFunnel.push({ session_id: sessionId, tier: u.tier, user_id: u.user_id, activity: 'checkout', activity_datetime: eventDt });
              funnelCounts['checkout'] = (funnelCounts['checkout'] || 0) + 1;

              if (dayRng() < convPaid) {
                eventDate = addSeconds(eventDate, stageDuration('checkout'));
                eventDt = formatDateTime(eventDate);
                allFunnel.push({ session_id: sessionId, tier: u.tier, user_id: u.user_id, activity: 'paid', activity_datetime: eventDt });
                funnelCounts['paid'] = (funnelCounts['paid'] || 0) + 1;
                reachedPaid = true;
              }
            }
          }
        }

        // Generate Basket for Paid Transaction
        if (reachedPaid) {
          const basketCfg = tierCfg.basket || cfg.simulation?.basket || { min_items: 2, max_items: 8 };
          const targetItems = Math.max(1, Math.round(sampleTriangular(basketCfg.min_items, basketCfg.max_items, (basketCfg.min_items + basketCfg.max_items) / 2, dayRng)));

          const trxId = `trx-${sessionId}`;
          let trxTotal = 0;
          const basketRows: TransactionItemRecord[] = [];
          const pickedSubcats = new Set<string>();

          // Choose category weights across all available catalog categories
          const catWeights: [string, number][] = allCategoryNames.map((cat) => {
            const definedWeight = tierCfg.category_weight?.[cat];
            return [cat, typeof definedWeight === 'number' ? definedWeight : 1.0];
          });

          for (let itemIdx = 0; itemIdx < targetItems; itemIdx++) {
            if (catWeights.length === 0) break;
            const chosenCat = weightedChoice(catWeights, dayRng);
            const subcats = catalogMap[chosenCat];
            if (!subcats) continue;

            const subcatNames = Object.keys(subcats);
            if (subcatNames.length === 0) continue;
            const chosenSubcatName = subcatNames[Math.floor(dayRng() * subcatNames.length)];
            const chosenSubcat = subcats[chosenSubcatName];

            // Subcategory duplicate control (config/simulation.yaml → subcategory_allow_duplicates)
            const dupRules = {
              ...(cfg.simulation?.subcategory_allow_duplicates || {}),
              ...(tierCfg.subcategory_allow_duplicates || {}),
            };
            if (dupRules[chosenSubcatName] === false && pickedSubcats.has(chosenSubcatName)) continue;

            // Cooldown check
            const histKey = `${u.user_id}:${chosenCat}:${chosenSubcatName}`;
            const lastDate = purchaseHistory.get(histKey);
            if (lastDate) {
              const diffDays = Math.round((current.getTime() - lastDate.getTime()) / (1000 * 3600 * 24));
              if (diffDays < chosenSubcat.cooldown) continue;
            }

            const prodList = Object.entries(chosenSubcat.products);
            if (prodList.length === 0) continue;
            const chosenProdPair = weightedChoice(
              prodList.map(([name, p]) => [name, Number(p.weight ?? 1)] as [string, number]),
              dayRng
            );
            const prodName = chosenProdPair;
            const basePrice = chosenSubcat.products[prodName].base_price;

            // Quantity model (Poisson with tier bias)
            const baseLambda = Number(
              tierCfg.quantity_model?.base_lambda ?? cfg.simulation?.quantity_model?.base_lambda ?? 1.0
            );
            const qtyBias = Number(tierCfg.quantity_bias?.[chosenCat] ?? 1.0);
            const qty = Math.max(1, poissonSample(baseLambda * qtyBias, dayRng));

            // Price variation (lognormal, mean-preserving)
            const cv = Number(cfg.simulation?.price_variation?.std_pct ?? 0.08);
            const sigma = Math.sqrt(Math.log1p(cv * cv));
            const priceFactor = Math.exp(sampleNormal(-0.5 * sigma * sigma, sigma, dayRng));
            const unitPrice = Math.max(1, Math.round((basePrice * priceFactor) / 100) * 100);
            const totalPrice = unitPrice * qty;

            trxTotal += totalPrice;
            dayItemsCount += qty;
            pickedSubcats.add(chosenSubcatName);

            basketRows.push({
              trx_id: trxId,
              user_id: u.user_id,
              tier: u.tier,
              date: eventDt,
              product: prodName,
              quantity: qty,
              unit_price: unitPrice,
              total_price: totalPrice,
            });

            // Update stats
            const stat = productStats.get(prodName) || { qty: 0, rev: 0 };
            stat.qty += qty;
            stat.rev += totalPrice;
            productStats.set(prodName, stat);

            categoryRevenue[chosenCat] = (categoryRevenue[chosenCat] || 0) + totalPrice;
            purchaseHistory.set(histKey, new Date(current));
          }

          if (basketRows.length > 0) {
            dayTrxCount++;
            dayRevenue += trxTotal;
            allTrx.push({
              session_id: sessionId,
              user_id: u.user_id,
              trx_id: trxId,
              date: eventDt,
              tier: u.tier,
              total_price: trxTotal,
            });
            allItems.push(...basketRows);
          }
        }
      }
    }

    // Update active dates
    for (const idx of activeUserIndices) {
      users[idx].last_active_date = dateStr;
    }

    totalRevenue += dayRevenue;
    totalItemsSold += dayItemsCount;

    dailyMetrics.push({
      date: dateStr,
      weekday,
      active_visitors: dayVisitors,
      transactions: dayTrxCount,
      gross_revenue: dayRevenue,
      items_sold: dayItemsCount,
      conversion_rate: dayVisitors > 0 ? dayTrxCount / dayVisitors : 0,
      new_users_acquired: newUsersToday,
    });

    dayIdx++;
    if (onProgress) {
      onProgress(dayIdx, totalDays, dateStr);
    }

    current.setUTCDate(current.getUTCDate() + 1);
  }

  // Top products
  const topProducts: [string, number, number][] = Array.from(productStats.entries())
    .map(([name, s]): [string, number, number] => [name, s.qty, s.rev])
    .sort((a, b) => (b[2] as number) - (a[2] as number))
    .slice(0, 10);

  const summary: SimulationSummary = {
    total_users: users.length,
    new_users: users.length - (Object.values<any>(cfg.tiers || {}).reduce((s, t) => s + (t.base_user || 10), 0)),
    total_sessions: funnelCounts['landing_page'] || 0,
    total_transactions: allTrx.length,
    total_items_sold: totalItemsSold,
    total_revenue: totalRevenue,
    average_order_value: allTrx.length > 0 ? totalRevenue / allTrx.length : 0,
    overall_conversion_rate: (funnelCounts['landing_page'] || 0) > 0 ? allTrx.length / funnelCounts['landing_page'] : 0,
    daily_metrics: dailyMetrics,
    funnel_breakdown: funnelCounts,
    category_revenue: categoryRevenue,
    top_products: topProducts,
  };

  return {
    users,
    funnel: allFunnel,
    transactions: allTrx,
    transaction_items: allItems,
    catalog: catalogRecords,
    summary,
  };
}
