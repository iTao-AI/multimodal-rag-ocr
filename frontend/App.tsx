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
    <div className={`min-h-screen ${isV2 ? 'theme-v2' : ''}`}>
      {/* Animated Background Grid - 仅在v1.0显示 */}
      {!isV2 && (
        <div className="fixed inset-0 pointer-events-none" style={{ zIndex: 0 }}>
          <div className="absolute inset-0 bg-[linear-gradient(rgba(0,212,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(0,212,255,0.03)_1px,transparent_1px)] bg-[size:50px_50px]" />
          
          {/* Floating Orbs */}
          <motion.div
            className="absolute w-[500px] h-[500px] rounded-full bg-[#00d4ff] opacity-10 blur-[120px]"
            animate={{
              x: [0, 100, 0],
              y: [0, -100, 0],
            }}
            transition={{
              duration: 20,
              repeat: Infinity,
              ease: "easeInOut",
            }}
            style={{ top: '10%', left: '20%' }}
          />
          <motion.div
            className="absolute w-[400px] h-[400px] rounded-full bg-[#0066ff] opacity-10 blur-[120px]"
            animate={{
              x: [0, -80, 0],
              y: [0, 80, 0],
            }}
            transition={{
              duration: 15,
              repeat: Infinity,
              ease: "easeInOut",
            }}
            style={{ bottom: '10%', right: '20%' }}
          />
        </div>
      )}
      
      {/* v2.0 简洁背景 */}
      {isV2 && (
        <div className="fixed inset-0 pointer-events-none" style={{ zIndex: 0 }}>
          <div className="absolute inset-0 bg-gradient-to-br from-gray-50 via-white to-blue-50/30" />
        </div>
      )}

      <Sidebar 
        activeView={activeView} 
        onNavigate={handleNavigate}
        isV2={isV2}
        onToggleVersion={handleToggleVersion}
      />

      <div style={{ marginLeft: '260px', position: 'relative', zIndex: 10, minHeight: '100vh' }}>
        <Header title={getHeaderTitle()} />

        <main style={{
          paddingTop: (activeView === 'chat' || (activeView === 'knowledge' && selectedDocument)) ? '64px' : '80px',
          minHeight: 'calc(100vh - 64px)'
        }}>
          <div className={(activeView === 'chat' || (activeView === 'knowledge' && selectedDocument)) ? '' : 'max-w-[1440px] mx-auto p-6'}>
            <AnimatePresence mode="wait">
              <motion.div
                key={activeView + (selectedKnowledgeBase || '') + (selectedDocument || '')}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3, ease: "easeOut" }}
              >
                {renderContent()}
              </motion.div>
            </AnimatePresence>
          </div>
        </main>
      </div>

      <Toaster 
        theme={isV2 ? 'light' : 'dark'}
        position="top-right"
        toastOptions={{
          style: isV2 ? {
            background: 'white',
            color: '#1e293b',
            border: '1px solid #e2e8f0',
          } : {
            background: 'rgba(10, 14, 39, 0.95)',
            color: '#e8eaed',
            border: '1px solid rgba(0, 212, 255, 0.3)',
          },
        }}
      />
    </div>
  );
}