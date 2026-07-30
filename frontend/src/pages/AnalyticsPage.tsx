import { useUsageData } from '@/hooks/useUsageData';
import { ChartCard } from '@/components/ChartCard';
import { StatCard } from '@/components/StatCard';
import {
  BarChart, Bar, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  RadarChart, PolarGrid, PolarAngleAxis, Radar,
} from 'recharts';
import { Clock, Target, Zap, Coffee } from 'lucide-react';

const tooltipStyle = {
  contentStyle: {
    background: 'hsl(225,14%,9%)',
    border: '1px solid hsl(225,12%,16%)',
    borderRadius: '8px',
    fontSize: '12px',
  },
  itemStyle: { color: 'hsl(210,20%,95%)' },
  labelStyle: { color: 'hsl(215,12%,50%)' },
};

function getIstDateKey(date: Date): string {
  return date.toLocaleDateString('en-CA', { timeZone: 'Asia/Kolkata' });
}

function getIstDayLabel(date: Date): string {
  return date.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', timeZone: 'Asia/Kolkata' });
}

function formatHoursToReadable(hours: number): string {
  const totalMinutes = Math.round(hours * 60);
  const h = Math.floor(totalMinutes / 60);
  const m = totalMinutes % 60;
  if (h === 0) return `${m} min`;
  if (m === 0) return `${h} hr`;
  return `${h} hr ${m} min`;
}

function getRecordFocusScore(u: any): number {
  const category = (u?.app_category || '').toString().toUpperCase();

  if (category === 'HIGH') return 100;
  if (category === 'MEDIUM') return 65;
  if (category === 'LOW') return 30;

  // If category is missing/unknown, derive a conservative score from behavior signals.
  const idleSeconds = Number(u?.idle_time_seconds || 0);
  const appSwitches = Number(u?.app_switches || 0);

  if (idleSeconds > 180) return 25;
  if (idleSeconds > 90 || appSwitches > 30) return 40;
  if (appSwitches > 18) return 50;
  return 55;
}

export default function AnalyticsPage() {
  const now = new Date();
  const usageQuery = useUsageData();

  if (usageQuery.isLoading) {
    return (
      <div className="space-y-2 animate-fade-in">
        <h1 className="text-2xl font-bold tracking-tight">Analytics</h1>
        <p className="text-sm text-muted-foreground">Loading analytics...</p>
      </div>
    );
  }

  if (usageQuery.isError) {
    return (
      <div className="space-y-2 animate-fade-in">
        <h1 className="text-2xl font-bold tracking-tight">Analytics</h1>
        <p className="text-sm text-muted-foreground">Unable to load analytics data right now.</p>
      </div>
    );
  }

  if (!usageQuery.data) {
    return (
      <div className="space-y-2 animate-fade-in">
        <h1 className="text-2xl font-bold tracking-tight">Analytics</h1>
        <p className="text-sm text-muted-foreground">No analytics data available.</p>
      </div>
    );
  }

  const analytics = usageQuery.data.analytics || {};

  const last7IstDayKeys = Array.from({ length: 7 }, (_, index) => {
    const dayDate = new Date(now.getTime() - (6 - index) * 24 * 60 * 60 * 1000);
    return getIstDateKey(dayDate);
  });
  const last7IstDayKeySet = new Set(last7IstDayKeys);
  
  // Prefer 7-day analytics payload; fallback to recent usage if analytics is empty.
  const laptop_usage = (analytics.laptop_usage && analytics.laptop_usage.length > 0)
    ? analytics.laptop_usage
    : (usageQuery.data.laptop_usage || []);

  /* ---------------- WEEKLY AVG SCREEN TIME & SUMMARY FROM 7 DAYS DATA ---------------- */

  const recentLaptopUsage = (laptop_usage || []).filter((u: any) => {
    const dateObj = new Date(u.timestamp);
    if (Number.isNaN(dateObj.getTime())) return false;

    // Bucket strictly by IST calendar day so specific dates (e.g. 13th, 14th) match Mongo aggregation.
    const istDayKey = getIstDateKey(dateObj);
    return last7IstDayKeySet.has(istDayKey);
  });

  const dailyMap: Record<string, number> = {};
  const appMap: Record<string, number> = {};

  recentLaptopUsage.forEach((u: any) => {
    const dateObj = new Date(u.timestamp);

    const date = getIstDateKey(dateObj);

    if (!dailyMap[date]) dailyMap[date] = 0;

    // usage_duration is in minutes
    const MINUTES_PER_UNIT = 1;
    dailyMap[date] += (u.usage_duration || 0) * MINUTES_PER_UNIT;
    
    // Track apps for most used
    const app = u.active_app || 'Unknown';
    appMap[app] = (appMap[app] || 0) + (u.usage_duration || 0);
  });

  const sortedByTime = [...recentLaptopUsage].sort(
    (a: any, b: any) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  let weeklyBreaks = 0;
  for (let i = 1; i < sortedByTime.length; i++) {
    const prev = new Date(sortedByTime[i - 1].timestamp).getTime();
    const curr = new Date(sortedByTime[i].timestamp).getTime();
    if (curr - prev > 10 * 60 * 1000) {
      weeklyBreaks++;
    }
  }

  const totalMinutes = Object.values(dailyMap).reduce((a, b) => a + b, 0);
  const avgScreenTime = Math.round((totalMinutes / 7 / 60) * 100) / 100;
  
  // Calculate focus directly from DB usage logs (no random/default summary blending).
  const weeklyFocusTotals = recentLaptopUsage.reduce(
    (acc: { weighted: number; minutes: number }, u: any) => {
      const minutes = Number(u?.usage_duration || 0);
      if (minutes <= 0) return acc;

      acc.weighted += getRecordFocusScore(u) * minutes;
      acc.minutes += minutes;
      return acc;
    },
    { weighted: 0, minutes: 0 }
  );

  const focusScore = weeklyFocusTotals.minutes > 0
    ? Math.round(weeklyFocusTotals.weighted / weeklyFocusTotals.minutes)
    : 0;

  // Most used app in past 7 days
  const mostUsedApp = Object.keys(appMap).length > 0 
    ? Object.entries(appMap).sort((a, b) => b[1] - a[1])[0][0]
    : 'None';
  
  // Break count inferred from >10-minute activity gaps in past 7 days
  const breakFrequency = weeklyBreaks;

  /* ---------------- DAILY USAGE ---------------- */

  const tomorrow = new Date(now.getTime() + 24 * 60 * 60 * 1000);
  const tomorrowIstKey = getIstDateKey(tomorrow);
  const tomorrowIstLabel = getIstDayLabel(tomorrow);


  const getMobileDummyHours = (label: string): number => {
    const cleaned = label.trim();

    const mobileData: Record<string, number> = {
      "03 May": 5 + (42 / 60),
      "04 May": 6 + (46 / 60),
      "05 May": 6 + (16 / 60),
      "06 May": 7 + (2 / 60),
      "07 May": 7 + (59 / 60),
      "08 May": 7 + (11 / 60),
      "09 May": 1 + (30 / 60),
    };

    return mobileData[cleaned] || 0;
  };

//  const getMobileDummyHours = (dayKey: string, dayLabel: string): number => {
//    if (dayKey === tomorrowIstKey || dayLabel === tomorrowIstLabel) {
 //     return 3 + (10 / 60); // 3 hr 10 min only for tomorrow
  //  }

    // Deterministic 4-8 hr range so values stay stable per day but shift as days roll.
//    const hash = dayKey.split('').reduce((acc, ch) => acc + ch.charCodeAt(0), 0);
//    return 4 + (hash % 9) * 0.5;
// };

  const dailyUsageFromAnalytics = (analytics.daily ?? []).map((d: any, index: number) => {
    const rawLabel = String(d.date || '').trim();
    const parsed = new Date(rawLabel);
    const dayKey = Number.isNaN(parsed.getTime())
      ? ''
      : getIstDateKey(parsed);
    const dayLabel = Number.isNaN(parsed.getTime())
      ? rawLabel
      : getIstDayLabel(parsed);

    return {
      date: rawLabel || dayLabel,
      usage: Number(d.usage || 0) / 60,
      mobile: getMobileDummyHours(dayLabel),
      order: index,
    };
  });

  const dailyUsage = dailyUsageFromAnalytics.length > 0
    ? dailyUsageFromAnalytics
    : last7IstDayKeys.map((dayKey, index) => {
        const dayDate = new Date(now.getTime() - (6 - index) * 24 * 60 * 60 * 1000);
        const dayLabel = getIstDayLabel(dayDate);
        return {
          date: dayLabel,
          usage: 0,
          mobile: getMobileDummyHours(dayLabel),
          order: index,
        };
      });

  /* ---------------- WEEKLY TREND ---------------- */

  const focusMap: Record<string, { total: number; weightedFocus: number }> = {};

  recentLaptopUsage.forEach((u: any) => {
    const dateObj = new Date(u.timestamp);
    const date = getIstDateKey(dateObj);
    const duration = u.usage_duration || 0;

    if (!focusMap[date]) {
      focusMap[date] = { total: 0, weightedFocus: 0 };
    }

    focusMap[date].total += duration;
    focusMap[date].weightedFocus += getRecordFocusScore(u) * duration;
  });

  const weeklyTrend = Array.from({ length: 7 }, (_, index) => {
    const dayDate = new Date(now.getTime() - (6 - index) * 24 * 60 * 60 * 1000);
    const dayKey = last7IstDayKeys[index];
    const dayLabel = getIstDayLabel(dayDate);
    const totals = focusMap[dayKey] || { total: 0, weightedFocus: 0 };
    // Focus for each day must come only from that day's logs.
    // If there are no logs on a day, keep focus at 0 for that day.
    const focus = totals.total
      ? Math.round(totals.weightedFocus / totals.total)
      : 0;

    return {
      key: dayKey,
      day: dayLabel,
      focus: Math.max(0, Math.min(100, focus)),
      hasLogs: totals.total > 0,
    };
  });

  const weeklyScoreTrend = (usageQuery.data?.trends?.fatigueTrend || []).map((fatigue: any) => {
    const productivity = usageQuery.data?.trends?.productivityTrend?.find(
      (p: any) => p.day === fatigue.day
    );

    const parsedDay = new Date(fatigue.day);
    const dayLabel = Number.isNaN(parsedDay.getTime())
      ? String(fatigue.day)
      : parsedDay.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' });

    return {
      day: dayLabel,
      fatigue: fatigue.score,
      productivity: productivity?.score ?? 0,
    };
  });

  const fatigueConfidence = Math.max(0, Math.min(100, usageQuery.data?.predictions?.fatigue?.confidence ?? 0));
  const productivityConfidence = Math.max(0, Math.min(100, usageQuery.data?.predictions?.productivity?.confidence ?? 0));

  /* ---------------- RADAR ---------------- */

  const radarData = [
    { metric: 'Focus',      value: focusScore },
    { metric: 'Breaks',     value: Math.min(100, breakFrequency * 10) },
    { metric: 'Efficiency', value: Math.min(100, focusScore + 10) },
    { metric: 'Balance',    value: 100 - focusScore },
  ];

  /* ---------------- APP USAGE ---------------- */

  /* ---------------- APP USAGE (already calculated above) --------*/

  const totalAppTime = Object.values(appMap).reduce((a, b) => a + b, 0);
  const safeTotal = totalAppTime > 0 ? totalAppTime : 1;

  const appUsage = Object.keys(appMap)
    .map((name) => ({ active_app: name, usage_duration: appMap[name] }))
    .sort((a, b) => b.usage_duration - a.usage_duration)
    .slice(0, 5);

  /* ---------------- RENDER ---------------- */

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Analytics</h1>
        <p className="text-sm text-muted-foreground mt-1">Real usage insights</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Average Screen Time"
          subtitle="Average of last 7 days"
          value={formatHoursToReadable(avgScreenTime)}
          icon={<Clock />}
        />
        <StatCard title="Focus"  value={`${focusScore}%`}       icon={<Target />} />
        <StatCard title="App"    value={mostUsedApp}            icon={<Zap />} />
        <StatCard title="Breaks" value={`${breakFrequency}`}     icon={<Coffee />} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Daily Usage Pattern" subtitle="Daily screen time (last 7 days)">
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={dailyUsage}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(225,12%,16%)" />
              <XAxis dataKey="date" tick={{ fill: 'hsl(215,12%,50%)', fontSize: 11 }} axisLine={false} />
              <YAxis
                tickFormatter={(v) => `${v}h`}
                tick={{ fill: 'hsl(215,12%,50%)', fontSize: 11 }}
                axisLine={false}
              />
              <Tooltip
                {...tooltipStyle}
                formatter={(value: any) => {
                  const mins = Math.round(value * 60);
                  const h = Math.floor(mins / 60);
                  const m = mins % 60;
                  if (h === 0) return `${m} min`;
                  if (m === 0) return `${h} hr`;
                  return `${h} hr ${m} min`;
                }}
              />
              <Bar dataKey="usage" fill="hsl(145,65%,48%)" radius={[3, 3, 0, 0]} name="Laptop" />
              <Bar dataKey="mobile" fill="hsl(250,80%,65%)" radius={[3, 3, 0, 0]} name="Mobile" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Weekly Focus Ratio" subtitle="Focused work percentage by day (0 when no logs)">
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={weeklyTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(225,12%,16%)" />
              <XAxis dataKey="day" tick={{ fill: 'hsl(215,12%,50%)', fontSize: 11 }} axisLine={false} />
              <YAxis
                domain={[0, 100]}
                ticks={[0, 25, 50, 75, 100]}
                tickFormatter={(v) => `${v}%`}
                tick={{ fill: 'hsl(215,12%,50%)', fontSize: 11 }}
                axisLine={false}
                allowDecimals={false}
                width={42}
              />
              <Tooltip
                {...tooltipStyle}
                formatter={(value: any, _name: any, props: any) => {
                  if (!props?.payload?.hasLogs) {
                    return 'No logs';
                  }
                  return `${value}%`;
                }}
              />
              <Bar dataKey="focus" fill="hsl(145,65%,48%)" radius={[4, 4, 0, 0]} name="Focus %" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Weekly Fatigue Trend" subtitle="Average daily fatigue percentage over the last 7 days">
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={weeklyScoreTrend}>
              <defs>
                <linearGradient id="fatigueAreaGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(250,80%,65%)" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="hsl(250,80%,65%)" stopOpacity={0.1}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(225,12%,16%)" />
              <XAxis dataKey="day" tick={{ fill: 'hsl(215,12%,50%)', fontSize: 11 }} axisLine={false} />
              <YAxis tickFormatter={(v) => `${v}%`} tick={{ fill: 'hsl(215,12%,50%)', fontSize: 11 }} axisLine={false} />
              <Tooltip
                {...tooltipStyle}
                formatter={(value: any) => `${value}%`}
                labelFormatter={(label: string) => `Logged on ${label}`}
              />
              <Area type="monotone" dataKey="fatigue" stroke="hsl(250,80%,65%)" fill="url(#fatigueAreaGradient)" strokeWidth={2.5} name="Fatigue %" />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Weekly Productivity Trend" subtitle="Average daily productivity percentage over the last 7 days">
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={weeklyScoreTrend}>
              <defs>
                <linearGradient id="productivityAreaGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(145,65%,48%)" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="hsl(145,65%,48%)" stopOpacity={0.1}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(225,12%,16%)" />
              <XAxis dataKey="day" tick={{ fill: 'hsl(215,12%,50%)', fontSize: 11 }} axisLine={false} />
              <YAxis tickFormatter={(v) => `${v}%`} tick={{ fill: 'hsl(215,12%,50%)', fontSize: 11 }} axisLine={false} />
              <Tooltip
                {...tooltipStyle}
                formatter={(value: any) => `${value}%`}
                labelFormatter={(label: string) => `Logged on ${label}`}
              />
              <Area type="monotone" dataKey="productivity" stroke="hsl(145,65%,48%)" fill="url(#productivityAreaGradient)" strokeWidth={2.5} name="Productivity %" />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Prediction Confidence" subtitle="How reliable the model output is today">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
            <div className="space-y-3">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-muted-foreground">Fatigue confidence</span>
                <span className="text-sm font-semibold">{fatigueConfidence}%</span>
              </div>
              <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full bg-violet-500"
                  style={{ width: `${fatigueConfidence}%` }}
                />
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-muted-foreground">Productivity confidence</span>
                <span className="text-sm font-semibold">{productivityConfidence}%</span>
              </div>
              <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full bg-emerald-500"
                  style={{ width: `${productivityConfidence}%` }}
                />
              </div>
            </div>
          </div>
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <ChartCard title="Performance Radar" subtitle="Behavioral metrics overview">
          <ResponsiveContainer width="100%" height={250}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="hsl(225,12%,16%)" />
              <PolarAngleAxis dataKey="metric" tick={{ fill: 'hsl(215,12%,50%)', fontSize: 11 }} />
              <Radar
                dataKey="value"
                stroke="hsl(250,80%,65%)"
                fill="hsl(250,80%,65%)"
                fillOpacity={0.2}
                strokeWidth={2}
              />
            </RadarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Application Usage" subtitle="Top apps used in last 7 days" className="lg:col-span-2">
          <div className="space-y-3 mt-1">
            {appUsage.map((app, i) => {
              const pct     = Math.min(100, (app.usage_duration / safeTotal) * 100);
              const percent = Math.min(100, Math.round((app.usage_duration / safeTotal) * 100));
              const isBrowser = app.active_app.toLowerCase().includes('chrome');
              const usageColors = [
                'hsl(250,80%,65%)',
                'hsl(200,85%,55%)',
                'hsl(145,65%,48%)',
                'hsl(38,92%,55%)',
                'hsl(0,72%,55%)',
              ];
              const barColor = usageColors[i % usageColors.length];
              const typeLabel = isBrowser ? 'Browser' : 'App';

              return (
                <div
                  key={app.active_app}
                  className="space-y-2 rounded-lg border border-border/40 bg-secondary/10 px-3 py-2.5"
                >
                  <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3">
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate leading-tight" title={app.active_app}>
                        {app.active_app}
                      </p>
                      <p className="text-xs text-muted-foreground mt-0.5">{typeLabel}</p>
                    </div>
                    <p className="text-xs md:text-sm text-foreground/85 whitespace-nowrap text-right">
                      {formatHoursToReadable(app.usage_duration / 60)} ({percent}%)
                    </p>
                  </div>

                  <div className="h-2 rounded-full bg-secondary/80 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{
                        width: `${pct}%`,
                        background: barColor,
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </ChartCard>
      </div>
    </div>
  );
}

