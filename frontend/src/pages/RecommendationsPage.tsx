import { useUsageData } from '@/hooks/useUsageData';
import { motion } from 'framer-motion';
import { Coffee, Moon, Repeat, Target, Smartphone, Eye, Timer, Brain } from 'lucide-react';

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

function getPriorityStyles(priority: string) {
  switch (priority) {
    case 'high': return 'border-l-destructive bg-destructive/5';
    case 'medium': return 'border-l-warning bg-warning/5';
    default: return 'border-l-info bg-info/5';
  }
}

function getPriorityBadge(priority: string) {
  switch (priority) {
    case 'high': return 'bg-destructive/15 text-destructive';
    case 'medium': return 'bg-warning/15 text-warning';
    default: return 'bg-info/15 text-info';
  }
}

export default function RecommendationsPage() {

  const { data } = useUsageData();

  if (!data) return null;

  const recommendations = (data as any).recommendations || [];

  return (
    <div className="space-y-6 animate-fade-in">

      <div>
        <h1 className="text-2xl font-bold tracking-tight">Recommendations</h1>
        <p className="text-sm text-muted-foreground mt-1">
          AI-powered suggestions to improve your digital wellbeing
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

        {recommendations.map((rec, i) => {

          const Icon = getIcon(rec.type);

          return (

            <motion.div
              key={i}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06 }}
              className={`glass-card rounded-xl p-5 border-l-4 ${getPriorityStyles('medium')}`}
            >

              <div className="flex items-start gap-4">

                <div className="p-2.5 rounded-lg bg-secondary shrink-0">
                  <Icon className="w-4 h-4 text-foreground" />
                </div>

                <div className="flex-1 min-w-0">

                  <div className="flex items-center gap-2 mb-1.5">

                    <h3 className="font-semibold text-sm">
                      {rec.title}
                    </h3>

                    <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full uppercase tracking-wide ${getPriorityBadge('medium')}`}>
                      AI
                    </span>

                  </div>

                  <p className="text-xs text-muted-foreground leading-relaxed mb-3">
                    {rec.description}
                  </p>

                </div>

              </div>

            </motion.div>

          );

        })}

      </div>

    </div>
  );
}