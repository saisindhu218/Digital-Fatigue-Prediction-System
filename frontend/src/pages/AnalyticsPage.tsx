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

  const { data } = useUsageData();
  if (!data) return null;

  const { summary, laptop_usage, mobile_usage } = data;

  /* ---------------- DAILY USAGE (REAL DATA) ---------------- */

  const hourlyMap: Record<string, { laptop: number; mobile: number }> = {};

  const hours = [
    '6am','8am','10am','12pm','2pm','4pm','6pm','8pm','10pm'
  ];

  hours.forEach(h => {
    hourlyMap[h] = { laptop: 0, mobile: 0 };
  });

  laptop_usage.forEach(u => {

    const date = new Date((u as any).timestamp);
    const h = date.getHours();

    const key =
      h < 8 ? '6am' :
      h < 10 ? '8am' :
      h < 12 ? '10am' :
      h < 14 ? '12pm' :
      h < 16 ? '2pm' :
      h < 18 ? '4pm' :
      h < 20 ? '6pm' :
      h < 22 ? '8pm' : '10pm';

    hourlyMap[key].laptop += (u.usage_duration || 0);

  });

  mobile_usage.forEach(u => {

    const date = new Date((u as any).timestamp);
    const h = date.getHours();

    const key =
      h < 8 ? '6am' :
      h < 10 ? '8am' :
      h < 12 ? '10am' :
      h < 14 ? '12pm' :
      h < 16 ? '2pm' :
      h < 18 ? '4pm' :
      h < 20 ? '6pm' :
      h < 22 ? '8pm' : '10pm';

    hourlyMap[key].mobile += (u.screen_time || 0);

  });

  const dailyUsage = hours.map(h => ({
    hour: h,
    laptop: Math.round(hourlyMap[h].laptop),
    mobile: Math.round(hourlyMap[h].mobile)
  }));


  /* ---------------- WEEKLY TREND (REAL DATA) ---------------- */

  const weeklyMap: Record<string, { screenTime: number }> = {};

  laptop_usage.forEach(u => {

    const date = new Date((u as any).timestamp);
    const day = date.toLocaleDateString(undefined, { weekday: 'short' });

    if (!weeklyMap[day]) {
      weeklyMap[day] = { screenTime: 0 };
    }

    weeklyMap[day].screenTime += (u.usage_duration || 0) / 60;

  });

  const weeklyTrend = Object.keys(weeklyMap).map(day => ({
    week: day,
    screenTime: Math.round(weeklyMap[day].screenTime * 10) / 10,
    focus: summary.focus_score
  }));


  /* ---------------- RADAR METRICS ---------------- */

  const radarData = [
    { metric: 'Focus', value: summary.focus_score },
    { metric: 'Breaks', value: summary.break_frequency * 10 },
    { metric: 'Consistency', value: summary.focus_score },
    { metric: 'Efficiency', value: summary.focus_score },
    { metric: 'Balance', value: 100 - summary.focus_score },
    { metric: 'Recovery', value: summary.break_frequency * 15 },
  ];


  /* ---------------- APP USAGE (AGGREGATED) ---------------- */

  const appMap: Record<string, { duration: number; category: string }> = {};

  laptop_usage.forEach(a => {

    const name = a.active_app || "Unknown";

    if (!appMap[name]) {
      appMap[name] = { duration: 0, category: a.app_category };
    }

    appMap[name].duration += a.usage_duration || 0;

  });

  const appUsage = Object.keys(appMap)
    .map(name => ({
      active_app: name,
      usage_duration: appMap[name].duration,
      app_category: appMap[name].category
    }))
    .sort((a,b)=> b.usage_duration - a.usage_duration)
    .slice(0,6);

  const maxApp = Math.max(...appUsage.map(a => a.usage_duration));


  return (
    <div className="space-y-6 animate-fade-in">

      <div>
        <h1 className="text-2xl font-bold tracking-tight">Analytics</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Detailed usage patterns and insights
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">

        <StatCard
          title="Avg Daily Usage"
          value={`${summary.total_screen_time}h`}
          icon={<Clock className="w-4 h-4" />}
        />

        <StatCard
          title="Focus Ratio"
          value={`${summary.focus_score}%`}
          icon={<Target className="w-4 h-4" />}
        />

        <StatCard
          title="Most Used App"
          value={summary.most_used_app}
          icon={<Zap className="w-4 h-4" />}
        />

        <StatCard
          title="Break Frequency"
          value={`${summary.break_frequency}/day`}
          icon={<Coffee className="w-4 h-4" />}
        />

      </div>


      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

        <ChartCard title="Daily Usage Pattern" subtitle="Laptop vs Mobile usage by hour">

          <ResponsiveContainer width="100%" height={250}>

            <BarChart data={dailyUsage}>

              <CartesianGrid strokeDasharray="3 3" stroke="hsl(225,12%,16%)" />

              <XAxis dataKey="hour" tick={{ fill: 'hsl(215,12%,50%)', fontSize: 11 }} axisLine={false} />

              <YAxis tick={{ fill: 'hsl(215,12%,50%)', fontSize: 11 }} axisLine={false} />

              <Tooltip {...tooltipStyle} />

              <Bar dataKey="laptop" fill="hsl(250,80%,65%)" radius={[3, 3, 0, 0]} name="Laptop" />

              <Bar dataKey="mobile" fill="hsl(200,85%,55%)" radius={[3, 3, 0, 0]} name="Mobile" />

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


        <ChartCard title="Application Usage" subtitle="Top apps by time spent" className="lg:col-span-2">

          <div className="space-y-3 mt-1">

            {appUsage.map((app, i) => {

              const pct = (app.usage_duration / maxApp) * 100;

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
                      <span className="text-xs font-medium">{Math.round(app.usage_duration)}m</span>
                    </div>

                  </div>

                  <span className="text-xs text-muted-foreground w-20">{app.app_category}</span>

                </div>

              );

            })}

          </div>

        </ChartCard>

      </div>

    </div>
  );
}