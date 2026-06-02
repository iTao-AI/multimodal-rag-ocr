import { Home, Database, MessageSquare, Search, Settings, Layers3, X } from 'lucide-react';
import { motion } from 'motion/react';

interface SidebarProps {
  activeView: string;
  onNavigate: (view: string) => void;
  isV2?: boolean;
  onToggleVersion?: () => void;
  isOpen?: boolean;
  onToggle?: () => void;
}

export function Sidebar({ activeView, onNavigate, isV2 = false, onToggleVersion, isOpen, onToggle }: SidebarProps) {
  const menuItems = [
    { id: 'dashboard', label: '仪表盘', icon: Home, disabled: false },
    { id: 'knowledge', label: '知识库管理', icon: Database, disabled: false },
    { id: 'chat', label: '对话', icon: MessageSquare, disabled: false },
    { id: 'retrieval', label: '检索测试', icon: Search, disabled: true, badge: '待开发' },
    { id: 'settings', label: '设置', icon: Settings, disabled: false, badge: '待优化' },
  ];

  return (
    <>
      {/* Mobile sidebar overlay - slide in from left */}
      <div className={`lg:hidden fixed inset-y-0 left-0 z-50 w-[260px] border-r border-[#dbe3ea] bg-white transform transition-transform duration-300 ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="h-full flex flex-col">
          {/* Mobile header with close button */}
          <div className="h-16 flex items-center justify-between px-5 border-b border-[#e5eaf0]">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-md bg-[#0f766e] flex items-center justify-center">
                <Layers3 size={17} className="text-white" />
              </div>
              <div>
                <h1 className="text-sm font-semibold text-[#111827]">RAG OCR</h1>
                <p className="text-[11px] text-[#64748b]">Evidence Workspace</p>
              </div>
            </div>
            <button onClick={onToggle} className="text-[#64748b] hover:text-[#111827] transition-colors">
              <X size={20} />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-1">
            {menuItems.map((item, index) => {
              const Icon = item.icon;
              const isActive = activeView === item.id;
              const isDisabled = item.disabled;
              return (
                <motion.button
                  key={item.id}
                  onClick={() => { if (!isDisabled) { onNavigate(item.id); onToggle?.(); } }}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                  disabled={isDisabled}
                  className={`w-full flex items-center justify-between gap-3 px-3 py-2.5 rounded-md transition-all duration-200 group ${
                    isDisabled
                      ? 'text-[#94a3b8] opacity-70 cursor-not-allowed'
                      : isActive
                      ? 'bg-[#0f766e] text-white shadow-sm'
                      : 'text-[#475569] hover:bg-[#eef3f1] hover:text-[#0f172a]'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon size={18} className={`${isDisabled ? 'text-[#94a3b8]' : isActive ? 'text-white' : 'text-[#64748b] group-hover:text-[#0f766e]'} transition-colors`} />
                    <span className="text-sm font-medium">{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className="px-2 py-0.5 text-[11px] bg-[#fef3c7] text-[#92400e] rounded-full border border-[#fde68a]">
                      {item.badge}
                    </span>
                  )}
                </motion.button>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="px-5 py-4 border-t border-[#e5eaf0]">
            <motion.button
              onClick={onToggleVersion}
              className="text-[#64748b] text-xs flex items-center gap-2 hover:text-[#0f766e] transition-colors cursor-pointer w-full"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <div className="w-2 h-2 rounded-full bg-[#10b981]" />
              <span>
                <span className="font-medium">{isV2 ? 'OCR模式 v2.0.0' : 'VLM模式 v1.0.0'}</span>
                <span className="text-[10px] text-[#94a3b8] ml-1">{isV2 ? '(切换 VLM)' : '(切换 OCR)'}</span>
              </span>
            </motion.button>
          </div>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:flex w-[260px] h-screen bg-white fixed left-0 top-0 flex-col z-50 border-r border-[#dbe3ea]">
        {/* Logo/Brand */}
        <div className="h-16 flex items-center justify-between px-5 border-b border-[#e5eaf0]">
          <motion.div
            className="flex items-center gap-2"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="w-8 h-8 rounded-md bg-[#0f766e] flex items-center justify-center">
              <Layers3 size={17} className="text-white" />
            </div>
            <div>
              <h1 className="text-sm font-semibold text-[#111827]">RAG OCR</h1>
              <p className="text-[11px] text-[#64748b]">Evidence Workspace</p>
            </div>
          </motion.div>

          {/* Version toggle */}
          {onToggleVersion && (
            <motion.button
              onClick={onToggleVersion}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              className="flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium bg-[#eef7f4] text-[#0f766e] border border-[#cde7de] hover:bg-[#dff0eb] transition-all"
            >
              <span>{isV2 ? '2.0' : '1.0'}</span>
            </motion.button>
          )}
        </div>

        {/* Navigation Menu */}
        <nav className="flex-1 px-4 py-6 space-y-1">
          {menuItems.map((item, index) => {
            const Icon = item.icon;
            const isActive = activeView === item.id;
            const isDisabled = item.disabled;

            return (
              <motion.button
                key={item.id}
                onClick={() => !isDisabled && onNavigate(item.id)}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
                disabled={isDisabled}
                className={`w-full flex items-center justify-between gap-3 px-3 py-2.5 rounded-md transition-all duration-200 group ${
                  isDisabled
                    ? 'text-[#94a3b8] opacity-70 cursor-not-allowed'
                    : isActive
                    ? 'bg-[#0f766e] text-white shadow-sm'
                    : 'text-[#475569] hover:bg-[#eef3f1] hover:text-[#0f172a]'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon size={18} className={`${isDisabled ? 'text-[#94a3b8]' : isActive ? 'text-white' : 'text-[#64748b] group-hover:text-[#0f766e]'} transition-colors`} />
                  <span className="text-sm font-medium">{item.label}</span>
                </div>
                {item.badge && (
                  <span className="px-2 py-0.5 text-[11px] bg-[#fef3c7] text-[#92400e] rounded-full border border-[#fde68a]">
                    {item.badge}
                  </span>
                )}
              </motion.button>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="px-5 py-4 border-t border-[#e5eaf0]">
          <motion.button
            onClick={onToggleVersion}
            className="text-[#64748b] text-xs flex items-center gap-2 hover:text-[#0f766e] transition-colors cursor-pointer w-full"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <div className="w-2 h-2 rounded-full bg-[#10b981]" />
            <span>
              <span className="font-medium">
                {isV2 ? 'OCR模式 v2.0.0' : 'VLM模式 v1.0.0'}
              </span>
              <span className="text-[10px] text-[#94a3b8] ml-1">
                {isV2 ? '(切换 VLM)' : '(切换 OCR)'}
              </span>
            </span>
          </motion.button>
        </div>
      </div>
    </>
  );
}
