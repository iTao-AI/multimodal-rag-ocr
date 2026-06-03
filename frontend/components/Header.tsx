import { User, Activity, Menu } from 'lucide-react';
import { motion } from 'motion/react';

interface HeaderProps {
  title: string;
  onToggleSidebar?: () => void;
}

export function Header({ title, onToggleSidebar }: HeaderProps) {
  return (
    <header className="h-16 bg-background/95 backdrop-blur-sm fixed top-0 left-0 lg:left-[240px] right-0 z-40 border-b border-border transition-all duration-300">
      <div className="h-full px-4 sm:px-6 lg:px-8 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={onToggleSidebar}
            className="lg:hidden text-muted-foreground hover:text-foreground transition-colors"
          >
            <Menu size={24} />
          </button>
          <motion.h2
            className="text-lg font-semibold text-foreground"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            {title}
          </motion.h2>
        </div>

        <div className="flex items-center gap-3">
          <motion.div
            className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-md bg-secondary border border-border"
            whileHover={{ scale: 1.05 }}
          >
            <Activity size={14} className="text-primary" />
            <span className="text-xs font-medium text-muted-foreground">服务运行中</span>
          </motion.div>

          <motion.button
            className="w-10 h-10 rounded-md bg-primary flex items-center justify-center transition-all duration-200 hover:bg-primary/90"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
          >
            <User size={18} className="text-primary-foreground" />
          </motion.button>
        </div>
      </div>
    </header>
  );
}
