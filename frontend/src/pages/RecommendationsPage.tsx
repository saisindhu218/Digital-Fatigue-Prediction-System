import { useUsageData } from '@/hooks/useUsageData';
import { motion } from 'framer-motion';
import { Coffee, Moon, Repeat, Target, Smartphone, Eye, Brain, Sparkles, CheckCircle } from 'lucide-react';
import { useNotifications } from '@/contexts/NotificationContext';
import { useEffect, useRef } from 'react';

type Recommendation = {
  type: string;
  title: string;
  description: string;
};

function sanitizeRecommendations(value: unknown): Recommendation[] {
  if (!Array.isArray(value)) return [];

  return value
    .filter((item) => !!item && typeof item === 'object')
    .map((item) => {
      const rec = item as Partial<Recommendation>;
      return {
        type: typeof rec.type === 'string' && rec.type.trim() ? rec.type : 'general',
        title: typeof rec.title === 'string' && rec.title.trim() ? rec.title : 'Recommendation',
        description:
          typeof rec.description === 'string' && rec.description.trim()
            ? rec.description
            : 'Review your latest usage insights and continue healthy focus habits.',
      };
    });
}

function buildFallbackRecommendations(data: any): Recommendation[] {
  const fatigueScore = data?.predictions?.fatigue?.fatigue_score ?? 0;
  const productivityScore = data?.predictions?.productivity?.productivity_score ?? 0;
  const screenTimeHours = data?.summary?.total_screen_time ?? 0;

  const fallback: Recommendation[] = [];

  if (fatigueScore >= 70) {
    fallback.push({
      type: 'fatigue',
      title: 'Take a Recovery Break',
      description: `Fatigue is currently ${Math.round(fatigueScore)}%. Take a 10-15 minute break and reduce multitasking for the next session.`,
    });
  }

  if (productivityScore <= 65) {
    fallback.push({
      type: 'focus',
      title: 'Run a Focus Block',
      description: `Productivity is ${Math.round(productivityScore)}%. Try a 25-minute deep-focus session with notifications muted.`,
    });
  }

  if (screenTimeHours >= 6) {
    fallback.push({
      type: 'screen',
      title: 'Reduce Continuous Screen Time',
      description: `Screen usage is ${screenTimeHours.toFixed(1)} hours. Add a short break every hour to lower fatigue buildup.`,
    });
  }

  if (fallback.length === 0) {
    fallback.push({
      type: 'positive',
      title: 'Maintain Current Rhythm',
      description: 'Your current signals look healthy. Continue balanced work sessions and keep regular short breaks.',
    });
  }

  return fallback;
}

type Priority = 'High' | 'Medium' | 'Low';

function getPriority(rec: Recommendation): Priority {
  if (rec.type === 'fatigue' || rec.type === 'health' || rec.type === 'sleep') return 'High';
  if (rec.type === 'focus' || rec.type === 'screen' || rec.type === 'productivity') return 'Medium';
  return 'Low';
}

function getPriorityClass(priority: Priority) {
  if (priority === 'High') return 'text-red-400 bg-red-500/10 border-red-500/30';
  if (priority === 'Medium') return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30';
  return 'text-green-400 bg-green-500/10 border-green-500/30';
}

function getPriorityOrder(priority: Priority) {
  if (priority === 'High') return 0;
  if (priority === 'Medium') return 1;
  return 2;
}

function getCategoryLabel(type: string) {
  if (type === 'fatigue' || type === 'health' || type === 'sleep') return 'Wellbeing';
  if (type === 'focus' || type === 'productivity') return 'Focus';
  if (type === 'screen') return 'Screen Habit';
  if (type === 'positive') return 'Positive Pattern';
  return 'General';
}

function getIcon(name: string) {
  switch (name) {
    case 'fatigue': return Coffee;
    case 'sleep': return Moon;
    case 'focus': return Repeat;
    case 'productivity': return Target;
    case 'screen': return Smartphone;
    case 'health': return Eye;
    case 'positive': return Sparkles;
    default: return Brain;
  }
}

export default function RecommendationsPage() {
  const { data, isLoading, error } = useUsageData();
  const { addNotification, notifications } = useNotifications();
  const notifiedRef = useRef(false);

  if (isLoading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <h1 className="text-2xl font-bold tracking-tight">Recommendations</h1>
        <div className="glass-card p-6 rounded-xl text-sm text-muted-foreground">
          Loading recommendations...
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-6 animate-fade-in">
        <h1 className="text-2xl font-bold tracking-tight">Recommendations</h1>
        <div className="glass-card p-6 rounded-xl text-sm text-red-400">
          Unable to load recommendations right now. Please try again in a moment.
        </div>
      </div>
    );
  }


  const recommendations = sanitizeRecommendations((data as { recommendations?: unknown }).recommendations);
  const effectiveRecommendations = recommendations.length > 0 ? recommendations : buildFallbackRecommendations(data);

  const sortedRecommendations = [...effectiveRecommendations].sort(
    (a, b) => getPriorityOrder(getPriority(a)) - getPriorityOrder(getPriority(b))
  );

  const topRecommendation = sortedRecommendations[0];
  const highCount = sortedRecommendations.filter((rec) => getPriority(rec) === 'High').length;
  const mediumCount = sortedRecommendations.filter((rec) => getPriority(rec) === 'Medium').length;
  const lowCount = sortedRecommendations.filter((rec) => getPriority(rec) === 'Low').length;
  const count = sortedRecommendations.length;

  // Notify user if there are recommendations and not already notified this session
  useEffect(() => {
    if (count > 0 && !notifiedRef.current) {
      // Avoid duplicate notifications in the same session
      const alreadyNotified = notifications.some(
        (n) => n.type === 'recommendation' && n.title === 'You have new recommendations' && !n.is_read
      );
      if (!alreadyNotified) {
        addNotification({
          notification_id: `rec-${Date.now()}`,
          timestamp: new Date().toISOString(),
          title: 'You have new recommendations',
          message: 'Check the Recommendations page for personalized suggestions.',
          type: 'recommendation',
          is_read: false,
          action_url: '/recommendations',
        });
        notifiedRef.current = true;
      }
    }
  }, [count, addNotification, notifications]);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight">Recommendations</h1>
            <span className="text-xs px-2.5 py-1 rounded-full bg-primary/15 text-primary font-medium">
              {count} suggestions
            </span>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Personalized actions to improve your digital habits
          </p>
        </div>
      </div>

      {/* AI insight at top with compact right-side priority text */}
      <div className="p-5 rounded-2xl bg-primary/10 border border-primary/20">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="font-medium mb-2">AI Insight</p>
            <p className="text-sm text-muted-foreground">
              {count > 0
                ? `We found ${count} personalized suggestions. Highest priority right now: ${topRecommendation?.title ?? 'Maintain healthy habits'}.`
                : 'Keep using the app to receive personalized recommendations.'}
            </p>
          </div>

          {count > 0 && (
            <div className="text-xs text-muted-foreground shrink-0 text-right">
              <p><span className="text-red-400 font-medium">High:</span> {highCount}</p>
              <p><span className="text-yellow-400 font-medium">Medium:</span> {mediumCount}</p>
              <p><span className="text-green-400 font-medium">Low:</span> {lowCount}</p>
            </div>
          )}
        </div>
      </div>

      {/* Recommendations at top */}
      {count > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {sortedRecommendations.map((rec, i) => {
            const Icon = getIcon(rec.type);
            const priority = getPriority(rec);

            return (
              <motion.div
                key={`${rec.title}-${rec.description}-${i}`}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="glass-card p-5 rounded-xl hover:scale-[1.02] transition-all"
              >
                <div className="flex items-start gap-4">
                  <div className="p-3 rounded-xl bg-secondary">
                    <Icon className="w-5 h-5 text-foreground" />
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <p className="text-sm font-semibold">{rec.title}</p>
                      <span className={`text-[11px] px-2 py-0.5 rounded-full border ${getPriorityClass(priority)}`}>
                        {priority}
                      </span>
                    </div>

                    <p className="text-sm leading-relaxed">{rec.description}</p>

                    <div className="mt-2 text-xs text-muted-foreground flex items-center gap-2">
                      <span className="inline-block h-1.5 w-1.5 rounded-full bg-primary/70" />
                      <span>{getCategoryLabel(rec.type)}</span>
                    </div>

                    <div className="mt-3 flex items-center gap-2 text-xs text-green-400">
                      <CheckCircle className="w-3.5 h-3.5" />
                      Suggested action for today
                    </div>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      ) : (
        <div className="glass-card p-6 rounded-xl text-center">
          <p className="text-sm text-muted-foreground">
            No recommendations yet. Keep using the app to get smarter suggestions.
          </p>
        </div>
      )}
    </div>
  );
}
