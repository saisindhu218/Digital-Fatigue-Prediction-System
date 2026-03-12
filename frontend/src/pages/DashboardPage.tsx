import { useUsageData } from '@/hooks/useUsageData';
import { StatCard } from '@/components/StatCard';
import { ChartCard } from '@/components/ChartCard';
import { Brain, Activity, Monitor, Layers, TrendingDown } from 'lucide-react';
import {
LineChart,Line,BarChart,Bar,PieChart,Pie,Cell,
XAxis,YAxis,CartesianGrid,Tooltip,ResponsiveContainer
} from 'recharts';

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

if(!usageQuery.data) return null;

const {predictions,summary,laptop_usage}=usageQuery.data;

/* REAL TREND DATA FROM BACKEND */
const fatigueTrend=usageQuery.data.trends?.fatigueTrend || [];
const productivityTrend=usageQuery.data.trends?.productivityTrend || [];

/* APP USAGE */
const appData=laptop_usage?.length
?laptop_usage.map(u=>({
name:u.active_app,
value:u.usage_duration
}))
:[{name:'No Data',value:1}];

/* PRODUCTIVITY BREAKDOWN */
const breakdownEntries=Object.entries(
predictions.productivity?.breakdown||{}
);

const totalLoss=predictions.productivity?.productivity_loss_hours||1;

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
value={`${summary.total_screen_time}h`}
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

<ChartCard title="Fatigue Trend" subtitle="Weekly fatigue score">

<ResponsiveContainer width="100%" height={220}>

<LineChart data={fatigueTrend}>

<CartesianGrid strokeDasharray="3 3" stroke="hsl(225,12%,16%)"/>

<XAxis dataKey="day" tick={{fill:'hsl(215,12%,50%)',fontSize:12}} axisLine={false}/>

<YAxis tick={{fill:'hsl(215,12%,50%)',fontSize:12}} axisLine={false}/>

<Tooltip {...tooltipStyle}/>

<Line type="monotone" dataKey="score" stroke="hsl(250,80%,65%)" strokeWidth={2.5}/>

</LineChart>

</ResponsiveContainer>

</ChartCard>

<ChartCard title="Productivity Trend" subtitle="Weekly productivity score">

<ResponsiveContainer width="100%" height={220}>

<BarChart data={productivityTrend}>

<CartesianGrid strokeDasharray="3 3" stroke="hsl(225,12%,16%)"/>

<XAxis dataKey="day" tick={{fill:'hsl(215,12%,50%)',fontSize:12}} axisLine={false}/>

<YAxis tick={{fill:'hsl(215,12%,50%)',fontSize:12}} axisLine={false}/>

<Tooltip {...tooltipStyle}/>

<Bar dataKey="score" fill="hsl(200,85%,55%)" radius={[4,4,0,0]}/>

</BarChart>

</ResponsiveContainer>

</ChartCard>

</div>

<div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

<ChartCard title="App Usage Distribution" subtitle="By duration">

<ResponsiveContainer width="100%" height={220}>

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

{appData.map((_,i)=>(
<Cell key={i} fill={COLORS[i%COLORS.length]}/>
))}

</Pie>

<Tooltip {...tooltipStyle}/>

</PieChart>

</ResponsiveContainer>

</ChartCard>

<ChartCard
title="Productivity Loss Breakdown"
subtitle="Hours lost per category"
className="lg:col-span-2"
>

<div className="space-y-4 mt-2">

{breakdownEntries.map(([key,val],i)=>(
<div key={key}>

<div className="flex justify-between text-sm mb-1.5">
<span className="text-muted-foreground">{key}</span>
<span className="font-medium">{val}h</span>
</div>

<div className="h-2 rounded-full bg-secondary overflow-hidden">

<div
className="h-full rounded-full"
style={{
width:`${(val/totalLoss)*100}%`,
background:COLORS[i%COLORS.length]
}}
/>

</div>

</div>
))}

</div>

<div className="flex items-center gap-2 mt-5 p-3 rounded-lg bg-destructive/10 text-sm">

<TrendingDown className="w-4 h-4 text-destructive"/>

<span className="text-muted-foreground">
Total productivity loss:
<span className="font-semibold text-foreground">
{predictions.productivity.productivity_loss_hours} hours/day
</span>
</span>

</div>

</ChartCard>

</div>

</div>
);
}