import { useTrends, useUsageData } from '@/hooks/useUsageData';
import { StatCard } from '@/components/StatCard';
import { ChartCard } from '@/components/ChartCard';
import { Brain, Activity, Monitor, Layers, TrendingDown } from 'lucide-react';
import {
  LineChart, Line, AreaChart, Area, ComposedChart, Bar,
  PieChart, Pie, Cell, BarChart,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { 
  aggregateToHourlyIntervals, 
  combineLoggedAndPredicted,
  generateMockTrendData,
  formatTime 
} from '@/lib/chartUtils';

const COLORS=[
'hsl(250,80%,65%)',
'hsl(200,85%,55%)',
'hsl(145,65%,48%)',
'hsl(38,92%,55%)',
'hsl(0,72%,55%)'
];

const tooltipStyle={
contentStyle:{
background:'hsl(225,14%,9%)',
border:'1px solid hsl(225,12%,16%)',
borderRadius:'8px',
fontSize:'12px'
},
itemStyle:{color:'hsl(210,20%,95%)'},
labelStyle:{color:'hsl(215,12%,50%)'}
};

export default function DashboardPage(){

const usageQuery=useUsageData();
const todayTrendQuery = useTrends(1);

console.log('Dashboard Debug:', {
  usageQueryLoading: usageQuery.isLoading,
  usageQueryData: usageQuery.data,
  todayTrendQueryLoading: todayTrendQuery.isLoading,
  todayTrendQueryData: todayTrendQuery.data,
  todayTrendQueryError: todayTrendQuery.error
});

if(!usageQuery.data) return null;

const {predictions,summary,laptop_usage}=usageQuery.data;

/* REAL TREND DATA FROM BACKEND */
const fatigueTrend =
  usageQuery.data?.trends?.fatigueTrend?.length
    ? usageQuery.data.trends.fatigueTrend
    : [{ day: "No Data", score: 0 }];

const productivityTrend =
  usageQuery.data?.trends?.productivityTrend?.length
    ? usageQuery.data.trends.productivityTrend
    : [{ day: "No Data", score: 0 }];

const todayFatigueTrend =
  todayTrendQuery.data?.fatigueTrend?.length
    ? todayTrendQuery.data.fatigueTrend
    : [];

const todayProductivityTrend =
  todayTrendQuery.data?.productivityTrend?.length
    ? todayTrendQuery.data.productivityTrend
    : [];

const todayFatigueData = (todayFatigueTrend || []).map((item: any) => ({
  time: item.day || item.time,
  logged: item.score,
}));

const todayProductivityData = (todayProductivityTrend || []).map((item: any) => ({
  time: item.day || item.time,
  logged: item.score,
}));

// Aggregate data to 3-hour intervals only if we have real data
const aggregatedFatigueData = todayFatigueData.length > 0 
  ? todayFatigueData.sort((a: any, b: any) => {
      const timeA = new Date(`2024-01-01 ${a.time}`).getTime();
      const timeB = new Date(`2024-01-01 ${b.time}`).getTime();
      return timeA - timeB;
    })
  : [];

const aggregatedProductivityData = todayProductivityData.length > 0 
  ? todayProductivityData.sort((a: any, b: any) => {
      const timeA = new Date(`2024-01-01 ${a.time}`).getTime();
      const timeB = new Date(`2024-01-01 ${b.time}`).getTime();
      return timeA - timeB;
    })
  : [];

// Use real data if available, otherwise generate mock data with realistic patterns
const finalFatigueData = aggregatedFatigueData.length > 0 
  ? aggregatedFatigueData 
  : generateMockTrendData(24, 3).map((d: any) => ({
      time: d.time,
      logged: d.logged,
    }));

const finalProductivityData = aggregatedProductivityData.length > 0 
  ? aggregatedProductivityData 
  : generateMockTrendData(24, 3).map((d: any) => ({
      time: d.time,
      logged: d.predicted,
    }));

// ✅ Combine app usage (group by app name)
const appMap: Record<string, number> = {};

(laptop_usage || []).forEach((u: any) => {
  const appName = u.active_app || "Unknown";

  if (!appMap[appName]) {
    appMap[appName] = 0;
  }

  appMap[appName] += (u.usage_duration || 0);
});

const totalMinutes = Object.values(appMap).reduce((a, b) => a + b, 0);

// ✅ Convert to chart format + sort + limit
const appData = Object.entries(appMap)
  .map(([name, value]) => ({
    name,
    value: Math.round(value), // total minutes
  }))
  .sort((a, b) => b.value - a.value)
  .slice(0, 6); // top 6 apps only (clean UI)

// ✅ total for percentage (optional)
const totalUsage = appData.reduce((sum, app) => sum + app.value, 0) || 1;

/* PRODUCTIVITY BREAKDOWN */

/* -------- REAL PRODUCTIVITY BREAKDOWN (BALANCED) -------- */

let fatigueMin = 0;
let contextSwitchMin = 0;
let distractionMin = 0;

(laptop_usage || []).forEach((u: any) => {
  const duration = u.usage_duration || 0;

  let f = 0, c = 0, d = 0;

  // signals
  if ((u.idle_time_seconds || 0) > 60) f = 1;
  if ((u.app_switches || 0) > 20) c = 1;
  if (["LOW", "MEDIUM"].includes(u.app_category)) d = 1;

  const totalSignals = f + c + d;

  if (totalSignals === 0) return;

  // ✅ split proportionally
  fatigueMin += (f / totalSignals) * duration;
  contextSwitchMin += (c / totalSignals) * duration;
  distractionMin += (d / totalSignals) * duration;
});

const realBreakdown = {
  Fatigue: fatigueMin / 60,
  "Context Switching": contextSwitchMin / 60,
  Distractions: distractionMin / 60
};

const breakdownEntries = Object.entries(realBreakdown);

const totalUsageMin = fatigueMin + contextSwitchMin + distractionMin;

const confidence =
  totalUsageMin === 0
    ? 0
    : Math.min(
        100,
        Math.round(
          ((laptop_usage.length || 1) * 5) // more data = more confidence
        )
      );

/* -------- AI INSIGHT -------- */

let insight = "Your productivity is balanced.";

if (realBreakdown["Context Switching"] > realBreakdown.Distractions &&
    realBreakdown["Context Switching"] > realBreakdown.Fatigue) {
  insight = "Frequent app switching is reducing your focus.";
}
else if (realBreakdown.Distractions > realBreakdown["Context Switching"]) {
  insight = "Distractions from low-value apps are impacting productivity.";
}
else if (realBreakdown.Fatigue > 0.3) {
  insight = "High idle time indicates possible fatigue or disengagement.";
}

/* -------- RISK LEVEL -------- */

let risk = "Low";

if (totalUsageMin / 60 > 2) risk = "High";
else if (totalUsageMin / 60 > 1) risk = "Medium";


/*screen time user freindly*/
function formatScreenTime(hours: number) {
  const totalMinutes = Math.round(hours * 60);

  const h = Math.floor(totalMinutes / 60);
  const m = totalMinutes % 60;

  if (h === 0) return `${m} min`;
  return `${h}h ${m}m`;
}

function formatHoursToReadable(hours: number) {
  const totalMinutes = Math.round(hours * 60);

  const h = Math.floor(totalMinutes / 60);
  const m = totalMinutes % 60;

  if (h === 0) return `${m} min`;
  if (m === 0) return `${h} hr`;
  return `${h} hr ${m} min`;
}

const totalLoss = totalUsageMin / 60 || 1;

return(
<div className="space-y-6 animate-fade-in">

<div>
<h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
<p className="text-sm text-muted-foreground mt-1">
Real-time digital fatigue & productivity insights
</p>
</div>

<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">

<StatCard
title="Fatigue Score"
value={`${predictions.fatigue.fatigue_score}%`}
subtitle={`Level: ${predictions.fatigue.fatigue_level}`}
icon={<Brain className="w-4 h-4"/>}
/>

<StatCard
title="Productivity Score"
value={`${predictions.productivity.productivity_score}%`}
subtitle={`Loss: ${predictions.productivity.productivity_loss_hours}h/day`}
icon={<Activity className="w-4 h-4"/>}
/>

<StatCard
title="Screen Time"
value={formatScreenTime(totalMinutes / 60)}
subtitle={`Peak: ${summary.peak_hours}`}
icon={<Monitor className="w-4 h-4"/>}
/>

<StatCard
title="Sessions"
value={summary.total_sessions}
subtitle={`Avg: ${summary.avg_session_length} min`}
icon={<Layers className="w-4 h-4"/>}
/>

</div>

<div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

  {/* FATIGUE TREND - AREA CHART WITH TODAY'S DATA */}
  <ChartCard title="Fatigue Trend - Today" subtitle="Hourly measurements">
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={finalFatigueData}>
        <defs>
          <linearGradient id="fatigueGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="hsl(250,80%,65%)" stopOpacity={0.8}/>
            <stop offset="95%" stopColor="hsl(250,80%,65%)" stopOpacity={0.1}/>
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(225,12%,16%)"/>
        <XAxis
          dataKey="time"
          tick={{ fill: 'hsl(215,12%,50%)', fontSize: 11 }}
          axisLine={false}
        />
        <YAxis
          tick={{ fill: 'hsl(215,12%,50%)', fontSize: 11 }}
          axisLine={false}
          domain={[0, 100]}
          tickFormatter={(v) => `${v}%`}
        />
        <Tooltip 
          {...tooltipStyle} 
          formatter={(value: any) => `${value}%`}
          labelFormatter={(label) => `Time: ${label}`}
        />
        <Legend />
        <Area 
          type="monotone" 
          dataKey="logged" 
          stroke="hsl(250,80%,65%)" 
          fill="url(#fatigueGradient)"
          strokeWidth={2.5}
          name="Fatigue Score"
        />
      </AreaChart>
    </ResponsiveContainer>
  </ChartCard>

  {/* PRODUCTIVITY TREND - AREA CHART WITH TODAY'S DATA */}
  <ChartCard title="Productivity Trend - Today" subtitle="Hourly measurements">
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={finalProductivityData}>
        <defs>
          <linearGradient id="productivityGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="hsl(145,65%,48%)" stopOpacity={0.8}/>
            <stop offset="95%" stopColor="hsl(145,65%,48%)" stopOpacity={0.1}/>
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(225,12%,16%)"/>
        <XAxis
          dataKey="time"
          tick={{ fill: 'hsl(215,12%,50%)', fontSize: 11 }}
          axisLine={false}
        />
        <YAxis
          tick={{ fill: 'hsl(215,12%,50%)', fontSize: 11 }}
          axisLine={false}
          domain={[0, 100]}
          tickFormatter={(v) => `${v}%`}
        />
        <Tooltip 
          {...tooltipStyle} 
          formatter={(value: any) => `${value}%`}
          labelFormatter={(label) => `Time: ${label}`}
        />
        <Legend />
        <Area 
          type="monotone" 
          dataKey="logged" 
          stroke="hsl(145,65%,48%)" 
          fill="url(#productivityGradient)"
          strokeWidth={2.5}
          name="Productivity Score"
        />
      </AreaChart>
    </ResponsiveContainer>
  </ChartCard>

</div>

<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

<ChartCard title="App Usage Distribution" subtitle="By duration">

  <div className="flex flex-col items-center justify-center">

    {/*PIE */}
    <div className="w-full max-w-[300px] h-[220px]">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>

          <Pie
            data={appData}
            cx="50%"
            cy="50%"
            innerRadius={55}
            outerRadius={85}
            paddingAngle={3}
            dataKey="value"
          >
            {appData.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>

          <Tooltip
            formatter={(value: any, name: any) => [
              `${value} min`,
              name
            ]}
          />

        </PieChart>
      </ResponsiveContainer>
    </div>

    {/* LEGEND below pie */}
    <div className="mt-4 w-full max-w-[300px] space-y-2">

      {appData.map((entry, index) => (
        <div key={index} className="flex items-center gap-2 text-sm">

          {/* color */}
          <div
            className="w-3 h-3 rounded-sm"
            style={{ backgroundColor: COLORS[index % COLORS.length] }}
          />

          {/* app */}
          <span className="text-muted-foreground">
            {entry.name}
          </span>

          {/* % */}
          <span className="ml-auto text-xs text-muted-foreground">
            {((entry.value / totalUsage) * 100).toFixed(1)}%
          </span>

          {/* minutes */}
          <span className="text-xs text-muted-foreground w-12 text-right">
            {entry.value}m
          </span>

        </div>
      ))}

    </div>

  </div>

</ChartCard>

<ChartCard 
  title="AI Productivity Analysis"
  subtitle="Estimated loss based on behavioral patterns"
>

<div className="space-y-4 mt-2">

{breakdownEntries.map(([key,val],i)=>(
<div key={key}>

<div className="flex justify-between text-sm mb-1.5">
<span className="text-muted-foreground">{key}</span>
<span className="font-medium">
  {formatHoursToReadable((val as number) || 0)}
</span>
</div>

<div className="h-2 rounded-full bg-secondary overflow-hidden">

<div
className="h-full rounded-full"
style={{
width:`${(((val as number) || 0) / totalLoss) * 100}%`,
background:COLORS[i%COLORS.length]
}}
/>

</div>

</div>
))}

</div>

{/* TOTAL */}
<div className="flex items-center gap-2 mt-5 p-3 rounded-lg bg-destructive/10 text-sm">

<TrendingDown className="w-4 h-4 text-destructive"/>

<span className="text-muted-foreground">
Total productivity loss:
<span className="font-semibold text-foreground">
{formatHoursToReadable(totalLoss)} /day
</span>
</span>

</div>

{/* AI INFO */}
<div className="mt-3 text-sm text-muted-foreground">

<div>
AI Confidence: <span className="font-medium">{confidence}%</span>
</div>

<div className="mt-1">
Risk Level: 
<span className={`ml-1 font-medium ${
  risk === "High" ? "text-red-400" :
  risk === "Medium" ? "text-yellow-400" :
  "text-green-400"
}`}>
  {risk}
</span>
</div>

<div className="mt-2">
{insight}
</div>

</div>

</ChartCard>
</div>
</div>

);
}