import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { Dashboard } from './components/Dashboard';
import { KnowledgeBase } from './components/KnowledgeBase';
import { KnowledgeBaseDetail } from './components/KnowledgeBaseDetail';
import { DocumentViewer } from './components/DocumentViewer';
import { Chat } from './components/Chat';
import { RetrievalTest } from './components/RetrievalTest';
import { Settings } from './components/Settings';
import { Toaster } from './components/ui/sonner';
import { toast } from 'sonner';

export default function App() {
  const [activeView, setActiveView] = useState('dashboard');
  const [selectedKnowledgeBase, setSelectedKnowledgeBase] = useState<string | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<string | null>(null);
  
  // 从localStorage读取版本状态，默认v1.0
  const [isV2, setIsV2] = useState(() => {
    const saved = localStorage.getItem('rag_version');
    return saved === 'v2';
  });

  // 移动端侧边栏折叠状态
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleToggleVersion = () => {
    const newVersion = !isV2;
    setIsV2(newVersion);
    // 保存到localStorage
    localStorage.setItem('rag_version', newVersion ? 'v2' : 'v1');
    // 显示切换提示
    toast.success(`已切换到 ${newVersion ? 'v2.0 (OCR增强版)' : 'v1.0'}`, {
      description: newVersion 
        ? '支持 MinerU、DeepSeek-OCR、PaddleOCR-VL' 
        : '支持快速模式和精确模式(VLM)',
      duration: 3000,
    });
  };

  const getHeaderTitle = () => {
    switch (activeView) {
      case 'dashboard':
        return '仪表盘';
      case 'knowledge':
        return selectedKnowledgeBase ? '知识库详情' : '知识库管理';
      case 'chat':
        return '对话';
      case 'retrieval':
        return '检索测试';
      case 'settings':
        return '设置';
      default:
        return '仪表盘';
    }
  };

  const handleNavigate = (view: string) => {
    setActiveView(view);
    setSelectedKnowledgeBase(null);
    setSelectedDocument(null);
  };

  const handleViewKnowledgeBaseDetail = (collectionId: string) => {
    setSelectedKnowledgeBase(collectionId);
  };

  const handleBackToKnowledgeBase = () => {
    setSelectedKnowledgeBase(null);
    setSelectedDocument(null);
  };

  const handleViewDocument = (fileId: string) => {
    setSelectedDocument(fileId);
  };

  const handleBackToDetail = () => {
    // 只清除文档选择，保留知识库选择，返回到知识库详情页
    setSelectedDocument(null);
    // selectedKnowledgeBase 保持不变，这样就返回到知识库详情页
  };

  const renderContent = () => {
    if (activeView === 'knowledge') {
      if (selectedDocument) {
        return <DocumentViewer fileId={selectedDocument} onBack={handleBackToDetail} />;
      }
      if (selectedKnowledgeBase) {
        return (
          <KnowledgeBaseDetail
            collectionId={selectedKnowledgeBase}
            onBack={handleBackToKnowledgeBase}
            onViewDocument={handleViewDocument}
            isV2={isV2}
          />
        );
      }
      return <KnowledgeBase onViewDetail={handleViewKnowledgeBaseDetail} isV2={isV2} />;
    }

    switch (activeView) {
      case 'dashboard':
        return <Dashboard onNavigate={handleNavigate} isV2={isV2} />;
      case 'chat':
        return <Chat isV2={isV2} />;  {/* ✅ 传递 isV2 属性 */}
      case 'retrieval':
        return <RetrievalTest />;
      case 'settings':
        return <Settings />;
      default:
        return <Dashboard onNavigate={handleNavigate} />;
    }
  };

  return (
    <div className={`professional-app min-h-screen bg-[#f4f6f8] text-[#111827] ${isV2 ? 'theme-v2' : ''}`}>
      <Sidebar
        activeView={activeView}
        onNavigate={(view) => { handleNavigate(view); setSidebarOpen(false); }}
        isV2={isV2}
        onToggleVersion={handleToggleVersion}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
      />

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <div className="app-content transition-all duration-300">
        <Header title={getHeaderTitle()} onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />

        <main className="min-h-screen" style={{
          paddingTop: (activeView === 'chat' || (activeView === 'knowledge' && selectedDocument)) ? '64px' : '80px',
        }}>
          <div className={(activeView === 'chat' || (activeView === 'knowledge' && selectedDocument)) ? '' : 'max-w-[1440px] mx-auto px-4 py-5 sm:px-6 lg:px-8'}>
            <AnimatePresence mode="wait">
              <motion.div
                key={activeView + (selectedKnowledgeBase || '') + (selectedDocument || '')}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.18, ease: "easeOut" }}
              >
                {renderContent()}
              </motion.div>
            </AnimatePresence>
          </div>
        </main>
      </div>

      <Toaster 
        theme="light"
        position="top-right"
        toastOptions={{
          style: {
            background: 'white',
            color: '#111827',
            border: '1px solid #dbe3ea',
            boxShadow: '0 18px 50px rgba(15, 23, 42, 0.12)',
          },
        }}
      />
    </div>
  );
}
