/**
 * Chart utility functions for data aggregation and formatting
 */

export interface TimeSeriesData {
  time: string;
  logged?: number;
  predicted?: number;
  value?: number;
  rawTime?: Date;
}

/**
 * Aggregates hourly data into 2-3 hour intervals
 * @param dataPoints Array of hourly data points with time and score
 * @param intervalHours Number of hours to aggregate (2 or 3)
 * @returns Aggregated data with 2-3 hour gaps
 */
export function aggregateToHourlyIntervals(
  dataPoints: Array<{ time: string; score?: number; value?: number; logged?: number; predicted?: number }>,
  intervalHours: number = 3
): TimeSeriesData[] {
  if (!dataPoints || dataPoints.length === 0) return [];

  // Parse time strings and group by interval
  const groupedData: Record<string, number[]> = {};
  const timeMap: Record<string, string> = {};

  dataPoints.forEach((point) => {
    // Try to parse time (handle various formats: "09:00", "9:00 AM", etc.)
    let hours = 0;
    const timeStr = point.time || '';
    
    // Extract hours from time string
    const match = timeStr.match(/(\d{1,2}):?(\d{2})?\s*(AM|PM)?/i);
    if (match) {
      hours = parseInt(match[1], 10);
      if (match[3] && match[3].toUpperCase() === 'PM' && hours !== 12) {
        hours += 12;
      } else if (match[3] && match[3].toUpperCase() === 'AM' && hours === 12) {
        hours = 0;
      }
    }

    // Round down to nearest interval
    const intervalStart = Math.floor(hours / intervalHours) * intervalHours;
    const key = `${intervalStart}:00`;

    if (!groupedData[key]) {
      groupedData[key] = [];
      timeMap[key] = formatTime(intervalStart);
    }

    const value = point.score ?? point.value ?? 0;
    if (value > 0) {
      groupedData[key].push(value);
    }
  });

  // Calculate averages for each interval
  return Object.entries(groupedData)
    .sort(([a], [b]) => parseInt(a) - parseInt(b))
    .map(([key, values]) => ({
      time: timeMap[key],
      rawTime: new Date(`2024-01-01 ${key}`),
      value: values.length > 0 ? Math.round(values.reduce((a, b) => a + b, 0) / values.length) : 0,
    }));
}

/**
 * Combines logged and predicted data with proper aggregation
 * Logged data is actual measured data, predicted is forecasted
 */
export function combineLoggedAndPredicted(
  loggedData: Array<{ time: string; score?: number; value?: number }>,
  predictedData: Array<{ time: string; score?: number; value?: number }>,
  intervalHours: number = 3
): TimeSeriesData[] {
  const loggedAggregated = aggregateToHourlyIntervals(loggedData, intervalHours);
  const predictedAggregated = aggregateToHourlyIntervals(predictedData, intervalHours);

  // Create a map of predicted data
  const predictedMap = new Map(
    predictedAggregated.map((item) => [item.time, item.value])
  );

  // Merge logged with predicted
  const merged = loggedAggregated.map((item) => ({
    ...item,
    logged: item.value,
    predicted: predictedMap.get(item.time) ?? item.value, // fallback to logged if no prediction
  }));

  // Add future predictions that don't have logged data
  predictedAggregated.forEach((predicted) => {
    if (!merged.find((item) => item.time === predicted.time)) {
      merged.push({
        time: predicted.time,
        rawTime: predicted.rawTime,
        logged: undefined,
        predicted: predicted.value,
      });
    }
  });

  // Sort by time
  return merged.sort((a, b) => {
    const aTime = a.rawTime ? a.rawTime.getTime() : 0;
    const bTime = b.rawTime ? b.rawTime.getTime() : 0;
    return aTime - bTime;
  });
}

/**
 * Formats hour number to 12-hour time format
 */
export function formatTime(hour: number): string {
  const h = hour % 24;
  const period = h >= 12 ? 'PM' : 'AM';
  const displayHour = h === 0 ? 12 : h > 12 ? h - 12 : h;
  return `${displayHour}:00 ${period}`;
}

/**
 * Formats time range string for chart labels
 * e.g., "09:00-12:00" from start hour 9 and interval 3
 */
export function formatTimeRange(startHour: number, intervalHours: number): string {
  const start = formatTime(startHour);
  const end = formatTime(startHour + intervalHours);
  return `${start.split(':')[0]}:00-${end.split(':')[0]}:00 ${end.split(' ')[1]}`;
}

/**
 * Generates mock data for testing/demo purposes
 */
export function generateMockTrendData(hoursBack: number = 24, intervalHours: number = 3) {
  const now = new Date();
  const data: TimeSeriesData[] = [];

  for (let i = hoursBack; i >= 0; i -= intervalHours) {
    const time = new Date(now.getTime() - i * 60 * 60 * 1000);
    const timeStr = time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
    
    // Generate realistic trend: fatigue increases over hours, productivity decreases
    const hoursIntoDay = time.getHours();
    const loggedScore = Math.max(20, Math.min(100, 40 + hoursIntoDay * 2 + Math.random() * 20));
    const predictionOffset = Math.random() * 10 - 5; // ±5% variation
    const predictedScore = Math.max(20, Math.min(100, loggedScore + predictionOffset));

    data.push({
      time: timeStr,
      rawTime: time,
      logged: Math.round(loggedScore),
      predicted: Math.round(predictedScore),
    });
  }

  return data.reverse();
}

/**
 * Calculate color based on score intensity
 */
export function getColorForScore(score: number, type: 'fatigue' | 'productivity' = 'fatigue'): string {
  if (type === 'fatigue') {
    if (score >= 70) return 'hsl(0,72%,55%)'; // Red - high fatigue
    if (score >= 50) return 'hsl(38,92%,55%)'; // Orange - moderate fatigue
    return 'hsl(145,65%,48%)'; // Green - low fatigue
  } else {
    // productivity
    if (score >= 70) return 'hsl(145,65%,48%)'; // Green - high productivity
    if (score >= 50) return 'hsl(38,92%,55%)'; // Orange - moderate productivity
    return 'hsl(0,72%,55%)'; // Red - low productivity
  }
}
