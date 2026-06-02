import { Bell, User, Activity, Menu } from 'lucide-react';
import { motion } from 'motion/react';

interface HeaderProps {
  title: string;
  onToggleSidebar?: () => void;
}

export function Header({ title, onToggleSidebar }: HeaderProps) {
  return (
    <header className="h-16 bg-white/95 backdrop-blur-sm fixed top-0 left-0 lg:left-[260px] right-0 z-40 border-b border-[#dbe3ea] transition-all duration-300">
      <div className="h-full px-4 sm:px-6 lg:px-8 flex items-center justify-between">
        <div className="flex items-center gap-4">
          {/* Mobile hamburger menu */}
          <button
            onClick={onToggleSidebar}
            className="lg:hidden text-[#334155] hover:text-[#0f766e] transition-colors"
          >
            <Menu size={24} />
          </button>
          <motion.h2
            className="text-lg font-semibold text-[#111827]"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            {title}
          </motion.h2>
        </div>
        
        <div className="flex items-center gap-3">
          {/* Activity Indicator */}
          <motion.div
            className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-md bg-[#ecfdf5] border border-[#bbf7d0]"
            whileHover={{ scale: 1.05 }}
          >
            <Activity size={14} className="text-[#059669]" />
            <span className="text-xs font-medium text-[#047857]">服务运行中</span>
          </motion.div>

          <motion.button
            className="w-10 h-10 rounded-md border border-[#dbe3ea] bg-white flex items-center justify-center transition-all duration-200 hover:bg-[#f8fafc] relative group"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            title="通知功能待实现"
          >
            <Bell size={18} className="text-[#64748b] group-hover:text-[#0f766e] transition-colors" />
          </motion.button>
          
          <motion.button 
            className="w-10 h-10 rounded-md bg-[#0f766e] flex items-center justify-center transition-all duration-200 hover:bg-[#115e59]"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
          >
            <User size={18} className="text-white" />
          </motion.button>
        </div>
      </div>
    </header>
  );
}
