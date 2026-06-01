import { FileText, Search, Plus, Trash2, Database } from 'lucide-react';
import { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { ConfirmDialog } from './ConfirmDialog';
import { Toast } from './Toast';
import { config } from '../src/config';
import { safeFetchJSON } from '../src/api';

interface KnowledgeBaseProps {
  onViewDetail: (collectionId: string) => void;
  isV2?: boolean;
}

interface KnowledgeBaseData {
  id: number;
  collection_id: string;  // Milvus collection ID
  name: string;  // 显示名称（中文）
  icon: string;
  iconBg: string;
  documents: number;
  chunks: number | string;
  updated: string;
  storageUsed: number;
}

export function KnowledgeBase({ onViewDetail, isV2 = false }: KnowledgeBaseProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBaseData[]>([]);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newKbName, setNewKbName] = useState('');
  const [loading, setLoading] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<{ show: boolean; id: string; name: string }>({
    show: false,
    id: '',
    name: '',
  });
  const [toast, setToast] = useState<{ show: boolean; message: string; type: 'success' | 'error' | 'info' | 'warning' }>({
    show: false,
    message: '',
    type: 'info',
  });

  // 从Milvus API获取知识库列表
  useEffect(() => {
    fetchKnowledgeBases();
  }, [isV2]);  // ✅ 添加 isV2 依赖，版本切换时重新获取

  const fetchKnowledgeBases = async () => {
    setLoading(true);
    try {
      const result = await safeFetchJSON(`${config.milvusApiUrl}/stats/all`);

      if (result.status === 'success') {
        const collections = result.data.collections || [];

        // ✅ 根据版本过滤知识库
        // V1模式：只显示不带 _v2 后缀的Collection
        // V2模式：只显示带 _v2 后缀的Collection
        const filteredCollections = collections.filter((col: any) => {
          // 修复：检查 collection_name 而不是 collection_id
          // 因为后端生成的 collection_id 格式是 kb_{timestamp}，不包含 _v2
          // 但 collection_name 是用户输入的 display_name，包含 _v2
          const collectionName = col.collection_name || '';
          const isV2Collection = collectionName.endsWith('_v2');
          
          if (isV2) {
            // V2模式：只显示带 _v2 后缀的
            return isV2Collection;
          } else {
            // V1模式：只显示不带 _v2 后缀的
            return !isV2Collection;
          }
        });

        // 图标映射
        const icons = ['📘', '📗', '📙', '📕', '📔', '📓'];
        const iconBgs = ['bg-blue-100', 'bg-green-100', 'bg-orange-100', 'bg-red-100', 'bg-purple-100', 'bg-pink-100'];

        const kbData = filteredCollections.map((col: any, index: number) => {
          // 格式化更新时间
          let updated = '未知';
          if (col.last_updated) {
            const date = new Date(col.last_updated);
            const now = new Date();
            const diffMs = now.getTime() - date.getTime();
            const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
            const diffDays = Math.floor(diffHours / 24);

            if (diffHours < 1) {
              updated = '刚刚';
            } else if (diffHours < 24) {
              updated = `${diffHours}小时前`;
            } else if (diffDays < 7) {
              updated = `${diffDays}天前`;
            } else {
              updated = date.toLocaleDateString('zh-CN');
            }
          }

          // ✅ V2模式：显示名称去掉 _v2 后缀，让用户看到更友好的名称
          let displayName = col.collection_name;
          if (isV2 && displayName.endsWith('_v2')) {
            displayName = displayName.slice(0, -3);  // 去掉 "_v2"
          }

          return {
            id: index + 1,
            collection_id: col.collection_id,  // Milvus内部ID（保留原始ID，包含_v2）
            name: displayName,  // 显示名称（去掉_v2后缀）
            icon: icons[index % icons.length],
            iconBg: iconBgs[index % iconBgs.length],
            documents: col.total_documents || 0,
            chunks: col.total_chunks || 0,
            updated: updated,
            storageUsed: Math.min(95, Math.floor((col.total_chunks || 0) / 100)), // 简单的存储使用率估算
          };
        });

        setKnowledgeBases(kbData);
      }
    } catch (error) {
      console.error('获取知识库列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const showToast = (message: string, type: 'success' | 'error' | 'info' | 'warning' = 'info') => {
    setToast({ show: true, message, type });
  };

  const handleCreateKB = async () => {
    if (!newKbName.trim()) {
      showToast('请输入知识库名称', 'warning');
      return;
    }

    try {
      // ✅ V2模式：自动添加 _v2 后缀
      const actualKbName = isV2 ? `${newKbName}_v2` : newKbName;
      
      const result = await safeFetchJSON(`${config.milvusApiUrl}/knowledge_base/create?display_name=${encodeURIComponent(actualKbName)}`, {
        method: 'POST',
      });

      if (result.status === 'success') {
        showToast(result.message, 'success');
        setShowCreateDialog(false);
        setNewKbName('');
        // 刷新列表
        fetchKnowledgeBases();
      } else {
        showToast(result.message || '创建知识库失败', 'error');
      }
    } catch (error) {
      console.error('创建知识库失败:', error);
      showToast('创建知识库失败: ' + (error instanceof Error ? error.message : String(error)), 'error');
    }
  };

  const confirmDelete = (collectionId: string, displayName: string) => {
    setDeleteConfirm({ show: true, id: collectionId, name: displayName });
  };

  const handleDeleteKB = async () => {
    try {
      const result = await safeFetchJSON(`${config.milvusApiUrl}/knowledge_base/delete`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ collection_id: deleteConfirm.id }),
      });

      if (result.status === 'success') {
        showToast(result.message, 'success');
        // 刷新列表
        fetchKnowledgeBases();
      } else {
        showToast(result.message || '删除知识库失败', 'error');
      }
    } catch (error) {
      console.error('删除知识库失败:', error);
      showToast('删除知识库失败', 'error');
    }
  };

  // 过滤知识库
  const filteredKBs = knowledgeBases.filter(kb =>
    kb.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div 
        className="flex items-center justify-between"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-md bg-[#0f766e] flex items-center justify-center">
            <Database size={21} className="text-white" />
          </div>
          <h2 className="text-lg font-semibold text-[#111827]">知识库管理</h2>
        </div>
        <motion.button
          onClick={() => setShowCreateDialog(true)}
          className="px-4 py-2.5 bg-[#0f766e] text-white rounded-md hover:bg-[#115e59] transition-colors flex items-center gap-2"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Plus size={18} />
          <span className="text-sm font-semibold">新建知识库</span>
        </motion.button>
      </motion.div>

      {/* Stats Summary */}
      {!loading && knowledgeBases.length > 0 && (
        <motion.div
          className="flex items-center gap-6 rounded-lg border border-[#dbe3ea] bg-white p-4 shadow-sm"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <div className="flex items-center gap-2">
            <span className="text-[#64748b] text-sm">总计:</span>
            <span className="text-[#111827] font-medium">{knowledgeBases.length} 个知识库</span>
          </div>
          <div className="w-px h-4 bg-[#dbe3ea]" />
          <div className="flex items-center gap-2">
            <span className="text-[#64748b] text-sm">文档:</span>
            <span className="text-[#0f766e] font-medium">
              {knowledgeBases.reduce((sum, kb) => sum + kb.documents, 0)} 个
            </span>
          </div>
          <div className="w-px h-4 bg-[#dbe3ea]" />
          <div className="flex items-center gap-2">
            <span className="text-[#64748b] text-sm">Chunks:</span>
            <span className="text-[#0f766e] font-medium">
              {knowledgeBases.reduce((sum, kb) => sum + (typeof kb.chunks === 'number' ? kb.chunks : 0), 0)} 个
            </span>
          </div>
        </motion.div>
      )}

      {/* Search Bar */}
      <motion.div
        className="relative"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-[#64748b]" size={20} />
        <input
          type="text"
          placeholder="搜索知识库..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full h-12 pl-12 pr-4 rounded-lg border border-[#cbd5e1] bg-white focus:outline-none focus:ring-2 focus:ring-[#0f766e] focus:border-[#0f766e] text-[#111827] placeholder-[#94a3b8] transition-all duration-200"
        />
      </motion.div>

      {/* Loading State */}
      {loading && (
        <div className="text-center text-[#94a3b8] py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-[#0f766e]"></div>
          <p className="mt-4">加载中...</p>
        </div>
      )}

      {/* Empty State */}
      {!loading && filteredKBs.length === 0 && (
        <div className="text-center text-[#94a3b8] py-12">
          <Database size={48} className="mx-auto mb-4 opacity-50" />
          <p>暂无知识库</p>
        </div>
      )}

      {/* Knowledge Base Cards */}
      <div className="space-y-4">
        {!loading && filteredKBs.map((kb, index) => (
          <motion.div
            key={kb.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.2 + index * 0.1 }}
            whileHover={{ y: -2, transition: { duration: 0.2 } }}
            className="rounded-lg border border-[#dbe3ea] bg-white p-6 shadow-sm transition-shadow cursor-pointer group hover:shadow-md"
          >
            <div className="flex items-start gap-4">
              {/* Icon */}
              <div className="w-12 h-12 rounded-md bg-[#eef7f4] flex items-center justify-center flex-shrink-0 text-[#0f766e]">
                <FileText size={23} />
              </div>

              {/* Content */}
              <div className="flex-1">
                <h3 className="mb-2 text-[#111827] font-semibold group-hover:text-[#0f766e] transition-colors">{kb.name}</h3>
                
                <div className="text-[#64748b] mb-4 text-sm flex items-center gap-3">
                  <span className="px-2.5 py-1 rounded-md bg-[#eef7f4] text-[#0f766e] border border-[#cde7de]">
                    {kb.documents}个文档
                  </span>
                  <span className="px-2.5 py-1 rounded-md bg-[#eef7f4] text-[#0f766e] border border-[#cde7de]">
                    {kb.chunks} chunks
                  </span>
                  <span>更新: {kb.updated}</span>
                </div>

                {/* Progress Bar */}
                <div className="mb-4">
                  <div className="flex items-center justify-between text-xs text-[#64748b] mb-2">
                    <span>存储使用</span>
                    <span className="text-[#0f766e]">{kb.storageUsed}%</span>
                  </div>
                  <div className="h-2 bg-[#e5e7eb] rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${kb.storageUsed}%` }}
                      transition={{ duration: 1, delay: 0.5 + index * 0.1 }}
                      className="h-full bg-[#0f766e]"
                    />
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-2">
                <motion.button
                  onClick={() => onViewDetail(kb.collection_id)}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="px-5 py-2.5 bg-[#0f766e] text-white rounded-md hover:bg-[#115e59] transition-colors"
                >
                  进入
                </motion.button>
                <motion.button
                  onClick={(e) => {
                    e.stopPropagation();
                    confirmDelete(kb.collection_id, kb.name);
                  }}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="px-4 py-2.5 border border-[#ef4444] text-[#dc2626] rounded-md hover:bg-[#fef2f2] transition-colors"
                >
                  <Trash2 size={18} />
                </motion.button>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Create Knowledge Base Dialog */}
      {showCreateDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/35 backdrop-blur-[2px]">
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
            className="w-full max-w-md mx-4 rounded-lg border border-[#dbe3ea] bg-white p-6 shadow-xl"
          >
            <div>
              <h3 className="text-xl font-semibold mb-6 text-[#111827]">新建知识库</h3>

              <div className="mb-6">
                <label className="block text-sm font-medium text-[#334155] mb-2">知识库名称</label>
                <input
                  type="text"
                  value={newKbName}
                  onChange={(e) => setNewKbName(e.target.value)}
                  placeholder="请输入知识库名称（支持中文）"
                  className="w-full rounded-md border border-[#cbd5e1] bg-white px-4 py-3 text-[#111827] placeholder-[#94a3b8] transition-all focus:outline-none focus:ring-2 focus:ring-[#0f766e]"
                  onKeyDown={(e) => e.key === 'Enter' && handleCreateKB()}
                  autoFocus
                />
              </div>

              <div className="flex gap-3">
                <motion.button
                  onClick={handleCreateKB}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="flex-1 rounded-md bg-[#0f766e] px-6 py-3 font-medium text-white transition-colors hover:bg-[#115e59]"
                >
                  创建
                </motion.button>
                <motion.button
                  onClick={() => {
                    setShowCreateDialog(false);
                    setNewKbName('');
                  }}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="flex-1 rounded-md border border-[#cbd5e1] bg-white px-6 py-3 font-medium text-[#334155] transition-colors hover:bg-[#f1f5f9]"
                >
                  取消
                </motion.button>
              </div>
            </div>
          </motion.div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteConfirm.show}
        onClose={() => setDeleteConfirm({ show: false, id: '', name: '' })}
        onConfirm={handleDeleteKB}
        title="确认删除知识库"
        message={`确定要删除知识库 "${deleteConfirm.name}" 吗？\n此操作不可恢复！`}
        type="warning"
        confirmText="删除"
        cancelText="取消"
      />

      {/* Toast Notification */}
      <Toast
        isOpen={toast.show}
        onClose={() => setToast({ ...toast, show: false })}
        message={toast.message}
        type={toast.type}
        duration={3000}
      />
    </div>
  );
}
