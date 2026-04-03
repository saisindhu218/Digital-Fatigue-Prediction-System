import { useUsageData } from '@/hooks/useUsageData';
import { ChartCard } from '@/components/ChartCard';
import { StatCard } from '@/components/StatCard';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar } from 'recharts';
import { Clock, Target, Zap, Coffee } from 'lucide-react';

const tooltipStyle = {
  contentStyle: { background: 'hsl(225,14%,9%)', border: '1px solid hsl(225,12%,16%)', borderRadius: '8px', fontSize: '12px' },
  itemStyle: { color: 'hsl(210,20%,95%)' },
  labelStyle: { color: 'hsl(215,12%,50%)' },
};

export default function AnalyticsPage() {
  const now = new Date();  
  const usageQuery = useUsageData();

  if (!usageQuery.data) return null;

  const { summary, laptop_usage } = usageQuery.data;
  const analytics = usageQuery.data.analytics || {};

/* ---------------- WEEKLY AVG SCREEN TIME ---------------- */

const dailyMap: Record<string, number> = {};

laptop_usage.forEach(u => {
  const dateObj = new Date((u as any).timestamp);

  // ✅ FILTER LAST 7 DAYS ONLY
  const diffMs = now.getTime() - dateObj.getTime();
  const diffDays = diffMs / (1000 * 60 * 60 * 24);

// allow slight buffer
  if (diffDays > 8) return;
  
  const date = dateObj.toLocaleDateString("en-IN", { timeZone: "Asia/Kolkata" });

  if (!dailyMap[date]) dailyMap[date] = 0;

  const BATCH_MINUTES = 10;
  dailyMap[date] += (u.usage_duration || 0) * BATCH_MINUTES;
});

// get number of days
const days = Object.keys(dailyMap).length || 1;

// total minutes
const totalMinutes = Object.values(dailyMap).reduce((a, b) => a + b, 0);

// avg per day (in hours)
const avgScreenTime = Math.round((totalMinutes / days / 60) * 100) / 100;

  /* ---------------- DAILY USAGE ---------------- */

const dailyUsage = (usageQuery.data?.analytics?.daily ?? [])
  .map((d: any) => {
    const dateObj = new Date(d.date);
    return {
      date: dateObj.toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short"
      }),
      usage: (d.usage || 0) / 60,
      rawDate: dateObj
    };
  })
  .sort((a, b) => a.rawDate.getTime() - b.rawDate.getTime());

  /* ---------------- WEEKLY TREND (FIXED ORDER) ---------------- */

const weeklyTrend = (analytics.weekly || []).map((w: any) => ({
  week: w.day,
  screenTime: Math.round((w.usage / 60) * 10) / 10,
  focus: w.usage === 0 ? 0 : Math.max(40, 100 - (w.usage / 60) * 5)
}));

/* ---------------- RADAR ---------------- */

  const radarData = [
    { metric: 'Focus', value: summary.focus_score },
    { metric: 'Breaks', value: summary.break_frequency * 10 },
    { metric: 'Efficiency', value: summary.focus_score },
    { metric: 'Balance', value: 100 - summary.focus_score },
  ];


  /* ---------------- APP USAGE ---------------- */

const appMap: Record<string, number> = {};

// 1️⃣ Fill data
laptop_usage.forEach((a: any) => {
  const date = new Date(a?.timestamp || Date.now());
  const diffDays = (now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24);

  if (diffDays > 8) return;

  const name = a.active_app || "Unknown";

  if (!appMap[name]) {
    appMap[name] = 0;
  }

  appMap[name] += a.usage_duration || 0;
});

// 2️⃣ THEN calculate totals
const totalAppTime = Object.values(appMap).reduce((a, b) => a + b, 0);
const safeTotal = totalAppTime > 0 ? totalAppTime : 1;

// 3️⃣ THEN build UI data
const appUsage = Object.keys(appMap)
  .map(name => ({
    active_app: name,
    usage_duration: appMap[name]
  }))
  .sort((a, b) => b.usage_duration - a.usage_duration)
  .slice(0, 5);
  
function formatHoursToReadable(hours: number) {
  const totalMinutes = Math.round(hours * 60);

  const h = Math.floor(totalMinutes / 60);
  const m = totalMinutes % 60;

  if (h === 0) return `${m} min`;
  if (m === 0) return `${h} hr`;
  return `${h} hr ${m} min`;
}

  return (
    <div className="space-y-6 animate-fade-in">

      <div>
        <h1 className="text-2xl font-bold tracking-tight">Analytics</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Real usage insights
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">

        <StatCard 
          title="Average Screen Time" 
          subtitle="Average of last 7 days"
          value={formatHoursToReadable(avgScreenTime)}
          icon={<Clock />} 
         />
        <StatCard title="Focus" value={`${summary.focus_score}%`} icon={<Target />} />
        <StatCard title="App" value={summary.most_used_app} icon={<Zap />} />
        <StatCard title="Breaks" value={`${summary.break_frequency}`} icon={<Coffee />} />

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
                  const totalMinutes = Math.round(value * 60);
                  const h = Math.floor(totalMinutes / 60);
                  const m = totalMinutes % 60;

                  if (h === 0) return `${m} min`;
                  if (m === 0) return `${h} hr`;
                  return `${h} hr ${m} min`;
                }}
              />

              <Bar dataKey="usage" fill="hsl(250,80%,65%)" radius={[3, 3, 0, 0]} name="Hours" />

            </BarChart>

          </ResponsiveContainer>

        </ChartCard>


        <ChartCard title="Weekly Trends" subtitle="Screen time & focus score over weeks">

          <ResponsiveContainer width="100%" height={250}>

            <LineChart data={weeklyTrend}>

              <CartesianGrid strokeDasharray="3 3" stroke="hsl(225,12%,16%)" />

              <XAxis dataKey="week" tick={{ fill: 'hsl(215,12%,50%)', fontSize: 11 }} axisLine={false} />

              <YAxis tick={{ fill: 'hsl(215,12%,50%)', fontSize: 11 }} axisLine={false} />

              <Tooltip {...tooltipStyle} />

              <Line type="monotone" dataKey="screenTime" stroke="hsl(250,80%,65%)" strokeWidth={2} name="Screen Time (h)" />

              <Line type="monotone" dataKey="focus" stroke="hsl(145,65%,48%)" strokeWidth={2} name="Focus %" />

            </LineChart>

          </ResponsiveContainer>

        </ChartCard>

      </div>


      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        <ChartCard title="Performance Radar" subtitle="Behavioral metrics overview">

          <ResponsiveContainer width="100%" height={250}>

            <RadarChart data={radarData}>

              <PolarGrid stroke="hsl(225,12%,16%)" />

              <PolarAngleAxis dataKey="metric" tick={{ fill: 'hsl(215,12%,50%)', fontSize: 11 }} />

              <Radar dataKey="value" stroke="hsl(250,80%,65%)" fill="hsl(250,80%,65%)" fillOpacity={0.2} strokeWidth={2} />

            </RadarChart>

          </ResponsiveContainer>

        </ChartCard>


        <ChartCard title="Application Usage" subtitle="Top apps used in last 7 days " className="lg:col-span-2">

          <div className="space-y-3 mt-1">

            {appUsage.map((app, i) => {

              const pct = Math.min(
                100,
                (app.usage_duration / safeTotal) * 100
              );
              
              const percent = Math.min(
                100,
                Math.round((app.usage_duration / safeTotal) * 100)
              );
              return (

                <div key={i} className="flex items-center gap-3">

                  <span className="text-sm text-muted-foreground w-20 truncate">{app.active_app}</span>

                  <div className="flex-1 h-7 rounded-md bg-secondary overflow-hidden relative">

                    <div
                      className="h-full rounded-md transition-all duration-700 flex items-center px-2"
                      style={{
                        width: `${pct}%`,
                        background: i === 0 ? 'hsl(250,80%,65%)' : i === 1 ? 'hsl(200,85%,55%)' : 'hsl(225,14%,22%)'
                      }}
                    >
                      <span className="text-xs font-medium">
                        {formatHoursToReadable(app.usage_duration / 60)} ({percent}%)
                      </span>
                    </div>

                  </div>

                  <span className="text-xs text-muted-foreground w-20">
                    {app.active_app.includes("chrome") ? "Browser" : "App"}
                  </span>
                </div>

              );

            })}

          </div>

        </ChartCard>

      </div>

    </div>
  );
}