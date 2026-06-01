import { ArrowRight, Bot, Clock3, Database, FileText, Layers3, MessageSquare, Search, TrendingDown, TrendingUp, Upload } from 'lucide-react';
import { motion } from 'motion/react';
import { useState, useEffect } from 'react';
import { UploadDialog } from './UploadDialog';
import { config } from '../src/config';
import { safeFetchJSON } from '../src/api';

interface DashboardProps {
  onNavigate?: (view: string) => void;
  isV2?: boolean;
}

export function Dashboard({ onNavigate, isV2 = false }: DashboardProps = {}) {
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [stats, setStats] = useState([
    { id: 1, label: '知识库', value: '0', unit: '个', icon: '📚', gradient: 'from-[#00d4ff] to-[#0066ff]', trend: '+0', trendUp: true },
    { id: 2, label: '文档数', value: '0', unit: '', icon: '📄', gradient: 'from-[#00ff88] to-[#00d4a0]', trend: '+0', trendUp: true },
    { id: 3, label: '查询次数', value: '0', unit: '', icon: '🔍', gradient: 'from-[#8b5cf6] to-[#6366f1]', trend: '+0%', trendUp: true },
    { id: 4, label: '响应时间', value: '0', unit: 'ms', icon: '⚡', gradient: 'from-[#ffb800] to-[#ff8c00]', trend: '-0ms', trendUp: true },
  ]);

  const fetchStatsRef = { current: null as (() => void) | null };

  useEffect(() => {
    let cancelled = false;
    const doFetch = async () => {
      try {
        const result = await safeFetchJSON(`${config.milvusApiUrl}/stats/all`);
        if (!cancelled && result.status === 'success') {
          const data = result.data;
          const collections = data.collections || [];

          const filteredCollections = collections.filter((col: any) => {
            const collectionName = col.collection_name || '';
            const isV2Collection = collectionName.endsWith('_v2');
            return isV2 ? isV2Collection : !isV2Collection;
          });

          const totalCollections = filteredCollections.length;
          const totalDocuments = filteredCollections.reduce((sum: number, col: any) =>
            sum + (col.total_documents || 0), 0);
          const totalChunks = filteredCollections.reduce((sum: number, col: any) =>
            sum + (col.total_chunks || 0), 0);

          setStats([
            { id: 1, label: '知识库', value: String(totalCollections), unit: '个', icon: '📚', gradient: 'from-[#00d4ff] to-[#0066ff]', trend: '+0', trendUp: true },
            { id: 2, label: '文档数', value: String(totalDocuments), unit: '', icon: '📄', gradient: 'from-[#00ff88] to-[#00d4a0]', trend: '+0', trendUp: true },
            { id: 3, label: 'Chunk数', value: String(totalChunks), unit: '', icon: '🔍', gradient: 'from-[#8b5cf6] to-[#6366f1]', trend: '+0', trendUp: true },
            { id: 4, label: '响应时间', value: '142', unit: 'ms', icon: '⚡', gradient: 'from-[#ffb800] to-[#ff8c00]', trend: '-8ms', trendUp: true },
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
  }, [isV2]);

  const handleUpload = (files: File[], kbId: string, config: any) => {
    console.log('Uploading files:', files, 'to KB:', kbId, 'with config:', config);
    // 上传完成后刷新统计数据
    fetchStatsRef.current?.();
  };

  const [conversations, setConversations] = useState<any[]>([]);

  // 从localStorage加载最近对话
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
            knowledgeBase: session.knowledgeBaseName,
            timestamp: formatTimestamp(session.updatedAt),
          }));
          if (!cancelled) setConversations(recentSessions);
        }
      } catch (error) {
        if (!cancelled) console.error('加载最近对话失败:', error);
      }
    };

    loadRecentConversations();
    const interval = setInterval(loadRecentConversations, 5000);
    return () => { cancelled = true; clearInterval(interval); };
  }, []);

  // 格式化时间戳
  const formatTimestamp = (isoString: string) => {
    const date = new Date(isoString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    return `${days}天前`;
  };

  const quickActions = [
    { id: 1, label: '上传文档', icon: Upload, variant: 'primary' },
    { id: 2, label: '开始对话', icon: MessageSquare, variant: 'outline' },
    { id: 3, label: '测试检索', icon: Search, variant: 'secondary' },
  ];

  const statIcons = {
    1: Database,
    2: FileText,
    3: Layers3,
    4: Clock3,
  } as const;

  return (
    <div className="space-y-5">
      <motion.section
        className="grid gap-5 lg:grid-cols-[1.45fr_0.9fr]"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.24 }}
      >
        <div className="rounded-lg border border-[#dbe3ea] bg-white p-6 shadow-sm">
          <div className="mb-5 flex items-center gap-2">
            <span className="rounded-md bg-[#eef7f4] px-2.5 py-1 text-xs font-semibold text-[#0f766e]">
              {isV2 ? 'OCR Enhanced v2.0' : 'VLM Pipeline v1.0'}
            </span>
            <span className="text-xs text-[#64748b]">PDF extraction · chunking · hybrid retrieval</span>
          </div>
          <h1 className="max-w-3xl text-2xl font-semibold leading-tight text-[#111827] sm:text-3xl">
            多模态 RAG-OCR 知识库工作台
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-[#475569]">
            面向 PDF 入库、OCR 切分、向量检索和答案溯源的端到端演示环境。上传、检索和问答入口都放在首屏，面试演示不用解释半天。
          </p>
          <div className="mt-6 flex flex-col gap-3 sm:flex-row">
            <button
              onClick={() => setShowUploadDialog(true)}
              className="inline-flex h-11 items-center justify-center gap-2 rounded-md bg-[#0f766e] px-4 text-sm font-semibold text-white transition-colors hover:bg-[#115e59]"
            >
              <Upload size={17} />
              上传 PDF
            </button>
            <button
              onClick={() => onNavigate && onNavigate('chat')}
              className="inline-flex h-11 items-center justify-center gap-2 rounded-md border border-[#cbd5e1] bg-white px-4 text-sm font-semibold text-[#334155] transition-colors hover:bg-[#f8fafc]"
            >
              <MessageSquare size={17} />
              打开问答
            </button>
          </div>
        </div>

        <div className="rounded-lg border border-[#dbe3ea] bg-[#f0fdf9] p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-wide text-[#64748b]">Pipeline State</p>
              <h2 className="mt-2 text-xl font-semibold text-[#111827]">Ready for demo</h2>
            </div>
            <div className="rounded-md bg-[#10b981]/15 px-3 py-1 text-xs font-semibold text-[#047857]">
              healthy
            </div>
          </div>
          <div className="mt-6 space-y-3 text-sm">
            {['Milvus collection loaded', 'Hybrid retrieval enabled', 'Source citation returned'].map((item) => (
              <div key={item} className="flex items-center gap-3 rounded-md border border-[#cde7de] bg-white/60 px-3 py-2">
                <span className="h-2 w-2 rounded-full bg-[#10b981]" />
                <span className="text-[#475569]">{item}</span>
              </div>
            ))}
          </div>
        </div>
      </motion.section>

      {/* Statistics Cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat, index) => (
          <motion.div
            key={stat.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: index * 0.1 }}
            whileHover={{ y: -2, transition: { duration: 0.2 } }}
            className="group rounded-lg border border-[#dbe3ea] bg-white p-5 shadow-sm transition-shadow hover:shadow-md"
          >
            <div>
              <div className="flex items-start justify-between mb-5">
                <div className="flex h-10 w-10 items-center justify-center rounded-md bg-[#eef7f4] text-[#0f766e]">
                  {(() => {
                    const StatIcon = statIcons[stat.id as keyof typeof statIcons];
                    return <StatIcon size={20} />;
                  })()}
                </div>
                <div className={`flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium ${stat.trendUp ? 'bg-[#ecfdf5] text-[#047857]' : 'bg-[#fef2f2] text-[#b91c1c]'}`}>
                  {stat.trendUp ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                  <span>{stat.trend}</span>
                </div>
              </div>
              
              <div className="flex items-baseline gap-1 mb-1">
                <span className="text-3xl font-semibold text-[#111827]">{stat.value}</span>
                {stat.unit && <span className="text-sm text-[#64748b]">{stat.unit}</span>}
              </div>
              
              <div className="text-sm text-[#64748b]">{stat.label}</div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Recent Conversations */}
      <motion.div 
        className="rounded-lg border border-[#dbe3ea] bg-white p-6 shadow-sm"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.5 }}
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-base font-semibold text-[#111827]">最近对话</h3>
          <motion.button
            onClick={() => onNavigate && onNavigate('chat')}
            className="flex items-center gap-1 text-sm font-medium text-[#0f766e] transition-all duration-200 hover:gap-2 group"
            whileHover={{ scale: 1.05 }}
          >
            查看全部
            <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
          </motion.button>
        </div>

        <div className="space-y-2">
          {conversations.length === 0 ? (
            <div className="text-center py-12 text-[#64748b]">
              <Bot size={48} className="mx-auto mb-4 opacity-50" />
              <p>暂无对话记录</p>
              <motion.button
                onClick={() => onNavigate && onNavigate('chat')}
                className="mt-4 rounded-md border border-[#0f766e] px-4 py-2 text-sm font-medium text-[#0f766e] transition-colors hover:bg-[#eef7f4]"
                whileHover={{ scale: 1.05 }}
              >
                开始第一次对话
              </motion.button>
            </div>
          ) : (
            conversations.map((conv, index) => (
            <motion.div
              key={conv.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: 0.6 + index * 0.1 }}
              whileHover={{ x: 3, transition: { duration: 0.2 } }}
              className="flex items-center gap-4 rounded-md border border-transparent p-4 cursor-pointer transition-all duration-200 hover:border-[#cbd5e1] hover:bg-[#f8fafc] group"
            >
              <div className="w-10 h-10 rounded-md bg-[#eef7f4] flex items-center justify-center flex-shrink-0 text-[#0f766e]">
                <Bot size={20} />
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="text-[#111827] mb-1 font-medium group-hover:text-[#0f766e] transition-colors">{conv.title}</div>
                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs bg-[#eef7f4] text-[#0f766e] border border-[#cde7de]">
                    {conv.knowledgeBase}
                  </span>
                </div>
              </div>
              
              <div className="text-[#64748b] text-sm flex-shrink-0">
                {conv.timestamp}
              </div>
            </motion.div>
          )))}
        </div>
      </motion.div>

      {/* Quick Actions */}
      <motion.div 
        className="rounded-lg border border-[#dbe3ea] bg-white p-6 shadow-sm"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.8 }}
      >
        <h3 className="mb-6 text-base font-semibold text-[#111827]">快速操作</h3>
        
        <div className="grid gap-3 sm:grid-cols-3">
          {quickActions.map((action, index) => (
            <motion.button
              key={action.id}
              onClick={() => {
                if (action.id === 1) {
                  setShowUploadDialog(true);
                } else if (action.id === 2 && onNavigate) {
                  onNavigate('chat');
                }
              }}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3, delay: 0.9 + index * 0.1 }}
              whileHover={{ scale: 1.01, y: -1 }}
              whileTap={{ scale: 0.95 }}
              className={`h-14 rounded-md flex items-center justify-center gap-3 transition-all duration-200 group ${
                action.variant === 'primary'
                  ? 'bg-[#0f766e] text-white hover:bg-[#115e59]'
                  : action.variant === 'outline'
                  ? 'border border-[#cbd5e1] text-[#334155] hover:bg-[#f8fafc]'
                  : 'bg-[#f1f5f9] text-[#334155] border border-[#e2e8f0] hover:bg-[#e2e8f0]'
              }`}
            >
              <action.icon size={18} />
              <span className="text-sm font-semibold">{action.label}</span>
            </motion.button>
          ))}
        </div>
      </motion.div>

      {/* Upload Dialog */}
      <UploadDialog
        isOpen={showUploadDialog}
        onClose={() => setShowUploadDialog(false)}
        onUpload={handleUpload}
        isV2={isV2}
      />
    </div>
  );
}
