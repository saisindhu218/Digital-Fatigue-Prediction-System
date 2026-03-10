import { useUsageData } from '@/hooks/useUsageData';
import { ChartCard } from '@/components/ChartCard';
import { StatCard } from '@/components/StatCard';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar } from 'recharts';
import { Clock, Target, Zap, Coffee } from 'lucide-react';

const dailyUsage = [
  { hour: '6am', laptop: 0, mobile: 10 }, { hour: '8am', laptop: 30, mobile: 15 },
  { hour: '10am', laptop: 55, mobile: 8 }, { hour: '12pm', laptop: 40, mobile: 20 },
  { hour: '2pm', laptop: 50, mobile: 12 }, { hour: '4pm', laptop: 45, mobile: 18 },
  { hour: '6pm', laptop: 20, mobile: 35 }, { hour: '8pm', laptop: 10, mobile: 40 },
  { hour: '10pm', laptop: 5, mobile: 25 },
];

const weeklyTrend = [
  { week: 'W1', screenTime: 6.2, focus: 75 }, { week: 'W2', screenTime: 7.1, focus: 68 },
  { week: 'W3', screenTime: 7.5, focus: 72 }, { week: 'W4', screenTime: 6.8, focus: 78 },
];

const radarData = [
  { metric: 'Focus', value: 72 }, { metric: 'Breaks', value: 45 },
  { metric: 'Consistency', value: 68 }, { metric: 'Efficiency', value: 80 },
  { metric: 'Balance', value: 55 }, { metric: 'Recovery', value: 62 },
];

const tooltipStyle = {
  contentStyle: { background: 'hsl(225,14%,9%)', border: '1px solid hsl(225,12%,16%)', borderRadius: '8px', fontSize: '12px' },
  itemStyle: { color: 'hsl(210,20%,95%)' },
  labelStyle: { color: 'hsl(215,12%,50%)' },
};

export default function AnalyticsPage() {
  const { data } = useUsageData();
  if (!data) return null;
  const { summary } = data;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Analytics</h1>
        <p className="text-sm text-muted-foreground mt-1">Detailed usage patterns and insights</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Avg Daily Usage" value={`${summary.total_screen_time}h`} icon={<Clock className="w-4 h-4" />} />
        <StatCard title="Focus Ratio" value={`${summary.focus_score}%`} icon={<Target className="w-4 h-4" />} />
        <StatCard title="Most Used App" value={summary.most_used_app} icon={<Zap className="w-4 h-4" />} />
        <StatCard title="Break Frequency" value={`${summary.break_frequency}/day`} icon={<Coffee className="w-4 h-4" />} />
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
            {data.laptop_usage.map((app, i) => {
              const max = Math.max(...data.laptop_usage.map(a => a.usage_duration));
              const pct = (app.usage_duration / max) * 100;
              return (
                <div key={app.active_app} className="flex items-center gap-3">
                  <span className="text-sm text-muted-foreground w-20 truncate">{app.active_app}</span>
                  <div className="flex-1 h-7 rounded-md bg-secondary overflow-hidden relative">
                    <div className="h-full rounded-md transition-all duration-700 flex items-center px-2" style={{ width: `${pct}%`, background: i === 0 ? 'hsl(250,80%,65%)' : i === 1 ? 'hsl(200,85%,55%)' : 'hsl(225,14%,22%)' }}>
                      <span className="text-xs font-medium">{app.usage_duration}m</span>
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
