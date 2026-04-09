import React from 'react';
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { ChartCard } from './ChartCard';

interface LoggedVsPredictedChartProps {
  title: string;
  subtitle?: string;
  data: Array<{
    time: string;
    logged?: number;
    predicted?: number;
  }>;
  tooltipStyle?: any;
  loggedColor?: string;
  predictedColor?: string;
  height?: number;
}

/**
 * LoggedVsPredictedChart - Shows actual measured data vs predicted data
 * Uses bars for logged data and line for predicted data for easy distinction
 */
export function LoggedVsPredictedChart({
  title,
  subtitle,
  data,
  tooltipStyle = {
    contentStyle: {
      background: 'hsl(225,14%,9%)',
      border: '1px solid hsl(225,12%,16%)',
      borderRadius: '8px',
      fontSize: '12px',
    },
    itemStyle: { color: 'hsl(210,20%,95%)' },
    labelStyle: { color: 'hsl(215,12%,50%)' },
  },
  loggedColor = 'hsl(200,85%,55%)',
  predictedColor = 'hsl(250,80%,65%)',
  height = 300,
}: LoggedVsPredictedChartProps) {
  return (
    <ChartCard title={title} subtitle={subtitle}>
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(225,12%,16%)" />
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
          
          {/* Bars for logged data (actual measured) */}
          <Bar
            dataKey="logged"
            fill={loggedColor}
            opacity={0.7}
            name="Measured"
            radius={[4, 4, 0, 0]}
          />
          
          {/* Line for predicted data (forecast) */}
          <Line
            type="monotone"
            dataKey="predicted"
            stroke={predictedColor}
            strokeWidth={2.5}
            name="Predicted"
            dot={{ fill: predictedColor, r: 4 }}
            activeDot={{ r: 6 }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

export default LoggedVsPredictedChart;
