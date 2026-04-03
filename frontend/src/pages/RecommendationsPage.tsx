import { useUsageData } from '@/hooks/useUsageData';
import { motion } from 'framer-motion';
import { Coffee, Moon, Repeat, Target, Smartphone, Eye, Brain, CheckCircle } from 'lucide-react';

function getIcon(name: string) {
  switch (name) {
    case 'fatigue': return Coffee;
    case 'sleep': return Moon;
    case 'focus': return Repeat;
    case 'productivity': return Target;
    case 'screen': return Smartphone;
    case 'health': return Eye;
    default: return Brain;
  }
}

export default function RecommendationsPage() {

  const { data } = useUsageData();
  if (!data) return null;

  const recommendations = (data as any).recommendations || [];
  const count = recommendations.length;

  return (
    <div className="space-y-6 animate-fade-in">

      {/* HEADER */}
      <div className="flex items-center justify-between">

        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-3">
            Recommendations

            {/* 🔥 COUNT BADGE */}
            <span className="text-xs px-2.5 py-1 rounded-full bg-primary/15 text-primary font-medium">
              {count} suggestions
            </span>

          </h1>

          <p className="text-sm text-muted-foreground mt-1">
            Personalized actions to improve your digital habits
          </p>
        </div>

      </div>

      {/* 🧠 AI INSIGHT */}
      <div className="p-5 rounded-2xl bg-primary/10 border border-primary/20">
        <div className="flex items-center gap-3 mb-2">
          <Brain className="w-5 h-5 text-primary" />
          <p className="font-medium">AI Insight</p>
        </div>
        <p className="text-sm text-muted-foreground">
          {count > 0
            ? `We found ${count} personalized suggestions based on your recent activity.`
            : "Keep using the app to receive personalized recommendations."}
        </p>
      </div>

      {/* 💡 RECOMMENDATIONS */}
      {count > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

          {recommendations.map((rec, i) => {

            const Icon = getIcon(rec.type);

            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="glass-card p-5 rounded-xl hover:scale-[1.02] transition-all"
              >

                <div className="flex items-start gap-4">

                  {/* ICON */}
                  <div className="p-3 rounded-xl bg-secondary">
                    <Icon className="w-5 h-5 text-foreground" />
                  </div>

                  {/* TEXT */}
                  <div className="flex-1">

                    <p className="text-sm leading-relaxed">
                      {rec.description}
                    </p>

                    {/* ACTION TAG */}
                    <div className="mt-3 flex items-center gap-2 text-xs text-green-400">
                      <CheckCircle className="w-3.5 h-3.5" />
                      Suggested action
                    </div>

                  </div>

                </div>

              </motion.div>
            );
          })}

        </div>
      ) : (

        /* 💤 EMPTY STATE */
        <div className="glass-card p-6 rounded-xl text-center">
          <p className="text-sm text-muted-foreground">
            No recommendations yet. Keep using the app to get smarter suggestions.
          </p>
        </div>

      )}

    </div>
  );
}