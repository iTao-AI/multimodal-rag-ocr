import { Home, Database, MessageSquare, Search, Settings, Layers3, X } from 'lucide-react';
import { motion } from 'motion/react';

interface SidebarProps {
  activeView: string;
  onNavigate: (view: string) => void;
  isOpen?: boolean;
  onToggle?: () => void;
}

export function Sidebar({ activeView, onNavigate, isOpen, onToggle }: SidebarProps) {
  const menuItems = [
    { id: 'dashboard', label: '仪表盘', icon: Home },
    { id: 'knowledge', label: '知识库管理', icon: Database },
    { id: 'chat', label: '对话', icon: MessageSquare },
    { id: 'retrieval', label: '检索测试', icon: Search },
    { id: 'settings', label: '设置', icon: Settings },
  ];

  const navContent = (
    <nav className="flex-1 px-4 py-6 space-y-1">
      {menuItems.map((item, index) => {
        const Icon = item.icon;
        const isActive = activeView === item.id;
        return (
          <motion.button
            key={item.id}
            onClick={() => { onNavigate(item.id); onToggle?.(); }}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3, delay: index * 0.1 }}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md transition-all duration-200 group ${
              isActive
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
            }`}
          >
            <Icon size={18} className={isActive ? 'text-primary-foreground' : 'text-muted-foreground group-hover:text-foreground transition-colors'} />
            <span className="text-sm font-medium">{item.label}</span>
          </motion.button>
        );
      })}
    </nav>
  );

  const logoBlock = (
    <div className="flex items-center gap-2">
      <div className="w-8 h-8 rounded-md bg-primary flex items-center justify-center">
        <Layers3 size={17} className="text-primary-foreground" />
      </div>
      <div>
        <h1 className="text-sm font-semibold text-foreground">RAG OCR</h1>
        <p className="text-[11px] text-muted-foreground">Knowledge Base</p>
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile sidebar */}
      <div className={`lg:hidden fixed inset-y-0 left-0 z-50 w-[240px] border-r border-border bg-sidebar transform transition-transform duration-300 ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="h-full flex flex-col">
          <div className="h-16 flex items-center justify-between px-5 border-b border-border">
            {logoBlock}
            <button onClick={onToggle} className="text-muted-foreground hover:text-foreground transition-colors">
              <X size={20} />
            </button>
          </div>
          {navContent}
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:flex w-[240px] h-screen bg-sidebar fixed left-0 top-0 flex-col z-50 border-r border-border">
        <div className="h-16 flex items-center px-5 border-b border-border">
          <motion.div
            className="flex items-center gap-2"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
          >
            {logoBlock}
          </motion.div>
        </div>
        {navContent}
        <div className="px-5 py-4 border-t border-border">
          <p className="text-[11px] text-muted-foreground">RAG OCR v2.0</p>
        </div>
      </div>
    </>
  );
}
