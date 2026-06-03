import { ArrowRight, BookOpen, FileText, Search, Zap, Upload, Layers3, MessageSquare, Bot } from 'lucide-react';
import { motion } from 'motion/react';
import { useState, useEffect, useRef } from 'react';
import { UploadDialog } from './UploadDialog';
import { config } from '../src/config';
import { safeFetchJSON } from '../src/api';

interface DashboardProps {
  onNavigate?: (view: string) => void;
}

export function Dashboard({ onNavigate }: DashboardProps = {}) {
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [stats, setStats] = useState([
    { id: 1, label: '知识库', value: '0', unit: '个', icon: BookOpen, gradient: 'text-primary' },
    { id: 2, label: '文档数', value: '0', unit: '', icon: FileText, gradient: 'text-success' },
    { id: 3, label: 'Chunk 数', value: '0', unit: '', icon: Search, gradient: 'text-info' },
    { id: 4, label: '响应时间', value: '0', unit: 'ms', icon: Zap, gradient: 'text-warning' },
  ]);

  const fetchStatsRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    let cancelled = false;
    const doFetch = async () => {
      try {
        const result = await safeFetchJSON(`${config.milvusApiUrl}/stats/all`);
        if (!cancelled && result.status === 'success') {
          const data = result.data;
          const collections = data.collections || [];

          // 显示全部 collection，不再按版本过滤
          const totalCollections = collections.length;
          const totalDocuments = collections.reduce((sum: number, col: any) =>
            sum + (col.total_documents || 0), 0);
          const totalChunks = collections.reduce((sum: number, col: any) =>
            sum + (col.total_chunks || 0), 0);

          setStats([
            { id: 1, label: '知识库', value: String(totalCollections), unit: '个', icon: BookOpen, gradient: 'text-primary' },
            { id: 2, label: '文档数', value: String(totalDocuments), unit: '', icon: FileText, gradient: 'text-success' },
            { id: 3, label: 'Chunk 数', value: String(totalChunks), unit: '', icon: Search, gradient: 'text-info' },
            { id: 4, label: '响应时间', value: '142', unit: 'ms', icon: Zap, gradient: 'text-warning' },
          ]);
        }
      } catch (error) {
        if (!cancelled) console.error('获取统计数据失败:', error);
      }
    };
    fetchStatsRef.current = doFetch;
    doFetch();
    const interval = setInterval(doFetch, 30000);
    return () => { cancelled = true; clearInterval(interval); };
  }, []);

  const handleUpload = (files: File[], kbId: string, config: any) => {
    console.log('Uploading files:', files, 'to KB:', kbId, 'with config:', config);
    fetchStatsRef.current?.();
  };

  const [conversations, setConversations] = useState<any[]>([]);

  useEffect(() => {
    let cancelled = false;
    const loadRecentConversations = () => {
      try {
        const savedSessions = localStorage.getItem('chat_sessions');
        if (savedSessions) {
          const sessions = JSON.parse(savedSessions);
          const recentSessions = sessions.slice(0, 3).map((session: any) => ({
            id: session.id,
            title: session.title,
            lastMessage: session.lastMessage || '暂无消息',
            timestamp: session.updatedAt || session.createdAt,
          }));
          if (!cancelled) setConversations(recentSessions);
        }
      } catch {
        if (!cancelled) setConversations([]);
      }
    };
    loadRecentConversations();
    return () => { cancelled = true; };
  }, []);

  const quickActions = [
    { id: 'upload', label: '上传文档', icon: Upload, onClick: () => setShowUploadDialog(true), variant: 'primary' as const },
    { id: 'knowledge', label: '管理知识库', icon: Layers3, onClick: () => onNavigate?.('knowledge'), variant: 'secondary' as const },
    { id: 'chat', label: '开始对话', icon: MessageSquare, onClick: () => onNavigate?.('chat'), variant: 'tertiary' as const },
  ];

  const variantStyles = {
    primary: 'bg-primary text-primary-foreground hover:bg-primary/90',
    secondary: 'bg-secondary text-foreground hover:bg-accent border border-border',
    tertiary: 'text-muted-foreground hover:text-foreground hover:bg-secondary',
  };

  return (
    <div className="space-y-8">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={stat.id}
              className="bg-card border border-border rounded-xl p-5"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
              whileHover={{ backgroundColor: '#1a1b1c' }}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm text-muted-foreground">{stat.label}</span>
                <Icon size={20} className={stat.gradient} />
              </div>
              <div className="flex items-baseline gap-1">
                <span className="text-2xl font-semibold text-foreground">{stat.value}</span>
                <span className="text-sm text-muted-foreground">{stat.unit}</span>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Pipeline Status */}
      <motion.div
        className="bg-card border border-border rounded-xl p-5"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.2 }}
      >
        <div className="flex items-center gap-3 mb-4">
          <Bot size={20} className="text-primary" />
          <h3 className="text-sm font-semibold text-foreground">RAG Pipeline</h3>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <span className="px-2 py-1 rounded bg-secondary border border-border">PDF → Markdown</span>
          <span className="text-muted-foreground">→</span>
          <span className="px-2 py-1 rounded bg-secondary border border-border">智能切分</span>
          <span className="text-muted-foreground">→</span>
          <span className="px-2 py-1 rounded bg-secondary border border-border">向量嵌入</span>
          <span className="text-muted-foreground">→</span>
          <span className="px-2 py-1 rounded bg-secondary border border-border">Milvus 存储</span>
          <span className="text-muted-foreground">→</span>
          <span className="px-2 py-1 rounded bg-primary/10 text-primary border border-primary/20">混合检索 + LLM</span>
        </div>
      </motion.div>

      {/* Quick Actions */}
      <div>
        <h3 className="text-sm font-semibold text-foreground mb-3">快速操作</h3>
        <div className="flex flex-wrap gap-3">
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <motion.button
                key={action.id}
                onClick={action.onClick}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${variantStyles[action.variant]}`}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <Icon size={16} />
                <span>{action.label}</span>
              </motion.button>
            );
          })}
        </div>
      </div>

      {/* Recent Conversations */}
      <div>
        <h3 className="text-sm font-semibold text-foreground mb-3">最近对话</h3>
        {conversations.length === 0 ? (
          <div className="text-center py-8">
            <MessageSquare size={32} className="mx-auto mb-3 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">暂无对话记录</p>
            <p className="text-xs text-muted-foreground mt-1">上传文档后开始对话</p>
          </div>
        ) : (
          <div className="space-y-2">
            {conversations.map((conv) => (
              <motion.div
                key={conv.id}
                className="bg-card border border-border rounded-lg p-4 flex items-center justify-between cursor-pointer hover:bg-secondary transition-colors"
                whileHover={{ scale: 1.01 }}
                onClick={() => onNavigate?.('chat')}
              >
                <div>
                  <p className="text-sm font-medium text-foreground">{conv.title}</p>
                  <p className="text-xs text-muted-foreground mt-1">{conv.lastMessage}</p>
                </div>
                <ArrowRight size={16} className="text-muted-foreground" />
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {showUploadDialog && (
        <UploadDialog
          isOpen={showUploadDialog}
          onClose={() => setShowUploadDialog(false)}
          onUpload={handleUpload}
        />
      )}
    </div>
  );
}
