import { Eye, EyeOff, Check, X, Cpu, FileText, Target, Settings2 } from 'lucide-react';
import { useState } from 'react';
import { motion } from 'motion/react';
import { toast } from 'sonner';
import { Slider } from './ui/slider';
import { Switch } from './ui/switch';

export function Settings() {
  const [activeTab, setActiveTab] = useState('model');
  const [showApiKey, setShowApiKey] = useState(false);
  const [temperature, setTemperature] = useState([0.7]);
  const [maxTokens, setMaxTokens] = useState([2000]);
  const [topK, setTopK] = useState([5]);
  const [similarityThreshold, setSimilarityThreshold] = useState([0.7]);
  const [enableRerank, setEnableRerank] = useState(true);
  const [extractionMode, setExtractionMode] = useState('fast');
  const [searchMode, setSearchMode] = useState('hybrid');
  const [chunkSize, setChunkSize] = useState(512);
  const [overlap, setOverlap] = useState(50);
  const [connectionStatus, setConnectionStatus] = useState<'success' | 'error' | null>(null);

  const handleSaveSettings = () => {
    const settings = {
      temperature: temperature[0],
      maxTokens: maxTokens[0],
      topK: topK[0],
      scoreThreshold: similarityThreshold[0],
      enableRerank,
      extractionMode,
      searchMode,
      chunkSize,
      overlap,
    };
    localStorage.setItem('app_settings', JSON.stringify(settings));
    toast.success('设置已保存');
  };

  const handleResetSettings = () => {
    localStorage.removeItem('app_settings');
    setTemperature([0.7]);
    setMaxTokens([2000]);
    setTopK([5]);
    setSimilarityThreshold([0.7]);
    setEnableRerank(true);
    setExtractionMode('fast');
    setSearchMode('hybrid');
    setChunkSize(512);
    setOverlap(50);
    toast.info('已恢复默认设置');
  };

  const tabs = [
    { id: 'model', label: '模型配置', icon: Cpu },
    { id: 'extraction', label: '提取配置', icon: FileText },
    { id: 'retrieval', label: '检索配置', icon: Target },
    { id: 'general', label: '通用设置', icon: Settings2 },
  ];

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <motion.div 
        className="bg-card border border-border rounded-2xl overflow-hidden"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="border-b border-[rgba(20,184,166,0.1)]">
          <div className="flex">
            {tabs.map((tab, index) => {
              const Icon = tab.icon;
              return (
                <motion.button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className={`flex-1 px-6 py-4 transition-all relative flex items-center justify-center gap-2 group ${
                    activeTab === tab.id
                      ? 'text-primary'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  {activeTab === tab.id && (
                    <motion.div
                      layoutId="activeSettingsTab"
                      className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary"
                      transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                    />
                  )}
                  <Icon size={18} className={activeTab === tab.id ? 'text-primary' : 'group-hover:text-primary transition-colors'} />
                  <span>{tab.label}</span>
                </motion.button>
              );
            })}
          </div>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {/* Model Configuration Tab */}
          {activeTab === 'model' && (
            <motion.div 
              className="space-y-8"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3 }}
            >
              {/* Embedding Model */}
              <div className="space-y-4">
                <div className="flex items-center gap-2 pb-3 border-b border-[rgba(20,184,166,0.1)]">
                  <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                    <span className="text-primary-foreground">🔤</span>
                  </div>
                  <h3 className="text-foreground">Embedding模型</h3>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-muted-foreground">提供商</label>
                    <select className="w-full px-4 py-3 bg-card border border-border border border-[rgba(20,184,166,0.15)] rounded-xl focus:outline-none focus:ring-2 focus:ring-primary text-foreground bg-secondary">
                      <option>Jina AI</option>
                      <option>OpenAI</option>
                      <option>Cohere</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-muted-foreground">模型</label>
                    <select className="w-full px-4 py-3 bg-card border border-border border border-[rgba(20,184,166,0.15)] rounded-xl focus:outline-none focus:ring-2 focus:ring-primary text-foreground bg-secondary">
                      <option>jina-embeddings-v4</option>
                      <option>jina-embeddings-v3</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-muted-foreground">维度</label>
                  <input
                    type="text"
                    value="2048"
                    disabled
                    className="w-full px-4 py-3 bg-card border border-border rounded-xl bg-secondary/80 text-muted-foreground border border-[rgba(20,184,166,0.08)]"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-muted-foreground">API Key</label>
                  <div className="flex gap-3">
                    <div className="flex-1 relative">
                      <input
                        type={showApiKey ? 'text' : 'password'}
                        defaultValue="your-api-key"
                        className="w-full px-4 py-3 pr-12 bg-card border border-border border border-[rgba(20,184,166,0.15)] rounded-xl focus:outline-none focus:ring-2 focus:ring-primary text-foreground"
                      />
                      <button
                        onClick={() => setShowApiKey(!showApiKey)}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-primary transition-colors"
                      >
                        {showApiKey ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                    <motion.button
                      onClick={() => setConnectionStatus('success')}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className="px-6 py-3 border border-primary text-primary rounded-xl hover:bg-primary/10 transition-all"
                    >
                      测试连接
                    </motion.button>
                  </div>
                  {connectionStatus === 'success' && (
                    <motion.div 
                      className="flex items-center gap-2 text-success text-sm px-3 py-2 bg-card border border-border rounded-lg border border-success/20"
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                    >
                      <Check size={16} />
                      连接成功
                    </motion.div>
                  )}
                  {connectionStatus === 'error' && (
                    <motion.div 
                      className="flex items-center gap-2 text-[#ff3b5c] text-sm px-3 py-2 bg-card border border-border rounded-lg border border-[rgba(255,59,92,0.2)]"
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                    >
                      <X size={16} />
                      连接失败
                    </motion.div>
                  )}
                </div>
              </div>

              {/* LLM Model */}
              <div className="space-y-4">
                <div className="flex items-center gap-2 pb-3 border-b border-[rgba(20,184,166,0.1)]">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-chart-5 to-chart-5 flex items-center justify-center">
                    <span className="text-white">🤖</span>
                  </div>
                  <h3 className="text-foreground">LLM模型</h3>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-muted-foreground">提供商</label>
                    <select className="w-full px-4 py-3 bg-card border border-border border border-[rgba(20,184,166,0.15)] rounded-xl focus:outline-none focus:ring-2 focus:ring-primary text-foreground bg-secondary">
                      <option>OpenAI</option>
                      <option>Claude</option>
                      <option>Qwen</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-muted-foreground">模型</label>
                    <select className="w-full px-4 py-3 bg-card border border-border border border-[rgba(20,184,166,0.15)] rounded-xl focus:outline-none focus:ring-2 focus:ring-primary text-foreground bg-secondary">
                      <option>gpt-4-turbo</option>
                      <option>gpt-3.5-turbo</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="text-muted-foreground">Temperature</label>
                      <span className="text-primary px-3 py-1 rounded-lg bg-[rgba(20,184,166,0.08)] border border-[rgba(20,184,166,0.15)]">{temperature[0]}</span>
                    </div>
                    <Slider
                      value={temperature}
                      onValueChange={setTemperature}
                      min={0}
                      max={1}
                      step={0.1}
                      className="w-full"
                    />
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="text-muted-foreground">Max Tokens</label>
                      <span className="text-primary px-3 py-1 rounded-lg bg-[rgba(20,184,166,0.08)] border border-[rgba(20,184,166,0.15)]">{maxTokens[0]}</span>
                    </div>
                    <Slider
                      value={maxTokens}
                      onValueChange={setMaxTokens}
                      min={500}
                      max={4000}
                      step={100}
                      className="w-full"
                    />
                  </div>
                </div>
              </div>

              {/* Rerank Model */}
              <div className="space-y-4">
                <div className="flex items-center gap-2 pb-3 border-b border-[rgba(20,184,166,0.1)]">
                  <div className="w-8 h-8 rounded-lg bg-success flex items-center justify-center">
                    <span className="text-primary-foreground">⚡</span>
                  </div>
                  <h3 className="text-foreground">Rerank模型</h3>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-muted-foreground">提供商</label>
                    <select className="w-full px-4 py-3 bg-card border border-border border border-[rgba(20,184,166,0.15)] rounded-xl focus:outline-none focus:ring-2 focus:ring-primary text-foreground bg-secondary">
                      <option>Cohere</option>
                      <option>Jina</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-muted-foreground">模型</label>
                    <select className="w-full px-4 py-3 bg-card border border-border border border-[rgba(20,184,166,0.15)] rounded-xl focus:outline-none focus:ring-2 focus:ring-primary text-foreground bg-secondary">
                      <option>rerank-v3</option>
                      <option>rerank-v2</option>
                    </select>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-4 bg-card border border-border rounded-xl border border-[rgba(20,184,166,0.15)]">
                  <Switch checked={enableRerank} onCheckedChange={setEnableRerank} />
                  <label className="text-foreground">启用重排序</label>
                </div>
              </div>
            </motion.div>
          )}

          {/* Extraction Configuration Tab */}
          {activeTab === 'extraction' && (
            <motion.div 
              className="space-y-8"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3 }}
            >
              {/* Default Mode */}
              <div className="space-y-4">
                <h3 className="text-foreground">默认提取模式</h3>

                <div className="grid grid-cols-2 gap-4">
                  <motion.button
                    onClick={() => setExtractionMode('fast')}
                    whileHover={{ scale: 1.02, y: -2 }}
                    whileTap={{ scale: 0.98 }}
                    className={`p-6 rounded-2xl border-2 transition-all text-left relative overflow-hidden group ${
                      extractionMode === 'fast'
                        ? 'border-primary bg-[rgba(20,184,166,0.08)] shadow-[0_0_15px_rgba(20,184,166,0.15)]'
                        : 'border-[rgba(20,184,166,0.15)] bg-card border border-border hover:border-[rgba(20,184,166,0.25)]'
                    }`}
                  >
                    {extractionMode === 'fast' && (
                      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-[rgba(20,184,166,0.08)] to-transparent" />
                    )}
                    <div className="flex items-center gap-3 mb-3 relative z-10">
                      <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${extractionMode === 'fast' ? 'border-primary' : 'border-[var(--muted-foreground)]'}`}>
                        {extractionMode === 'fast' && <div className="w-3 h-3 rounded-full bg-primary" />}
                      </div>
                      <span className={`text-lg ${extractionMode === 'fast' ? 'text-primary' : 'text-foreground'}`}>
                        快速模式(PyMuPDF4LLM)
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground relative z-10">
                      使用PyMuPDF进行快速文档提取，适合简单文档
                    </p>
                  </motion.button>

                  <motion.button
                    onClick={() => setExtractionMode('vlm')}
                    whileHover={{ scale: 1.02, y: -2 }}
                    whileTap={{ scale: 0.98 }}
                    className={`p-6 rounded-2xl border-2 transition-all text-left relative overflow-hidden group ${
                      extractionMode === 'vlm'
                        ? 'border-primary bg-[rgba(20,184,166,0.08)] shadow-[0_0_15px_rgba(20,184,166,0.15)]'
                        : 'border-[rgba(20,184,166,0.15)] bg-card border border-border hover:border-[rgba(20,184,166,0.25)]'
                    }`}
                  >
                    {extractionMode === 'vlm' && (
                      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-[rgba(20,184,166,0.08)] to-transparent" />
                    )}
                    <div className="flex items-center gap-3 mb-3 relative z-10">
                      <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${extractionMode === 'vlm' ? 'border-primary' : 'border-[var(--muted-foreground)]'}`}>
                        {extractionMode === 'vlm' && <div className="w-3 h-3 rounded-full bg-primary" />}
                      </div>
                      <span className={`text-lg ${extractionMode === 'vlm' ? 'text-primary' : 'text-foreground'}`}>
                        精确模式(VLM)
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground relative z-10">
                      使用视觉语言模型进行精确提取，支持复杂布局
                    </p>
                  </motion.button>
                </div>
              </div>

              {/* Chunking Parameters */}
              <div className="space-y-4">
                <h3 className="text-foreground">切分参数</h3>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-muted-foreground">Chunk Size</label>
                    <div className="flex gap-2">
                      <input
                        type="number"
                        value={chunkSize}
                        onChange={(e) => setChunkSize(parseInt(e.target.value))}
                        className="flex-1 px-4 py-3 bg-card border border-border border border-[rgba(20,184,166,0.15)] rounded-xl focus:outline-none focus:ring-2 focus:ring-primary text-foreground"
                      />
                      <span className="px-4 py-3 bg-card border border-border rounded-xl border border-[rgba(20,184,166,0.15)] text-muted-foreground">
                        tokens
                      </span>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="text-muted-foreground">Overlap</label>
                    <div className="flex gap-2">
                      <input
                        type="number"
                        value={overlap}
                        onChange={(e) => setOverlap(parseInt(e.target.value))}
                        className="flex-1 px-4 py-3 bg-card border border-border border border-[rgba(20,184,166,0.15)] rounded-xl focus:outline-none focus:ring-2 focus:ring-primary text-foreground"
                      />
                      <span className="px-4 py-3 bg-card border border-border rounded-xl border border-[rgba(20,184,166,0.15)] text-muted-foreground">
                        tokens
                      </span>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="text-muted-foreground">Max Page Span</label>
                    <div className="flex gap-2">
                      <input
                        type="number"
                        defaultValue={2}
                        className="flex-1 px-4 py-3 bg-card border border-border border border-[rgba(20,184,166,0.15)] rounded-xl focus:outline-none focus:ring-2 focus:ring-primary text-foreground"
                      />
                      <span className="px-4 py-3 bg-card border border-border rounded-xl border border-[rgba(20,184,166,0.15)] text-muted-foreground">
                        页
                      </span>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="text-muted-foreground">Bridge Length</label>
                    <div className="flex gap-2">
                      <input
                        type="number"
                        defaultValue={100}
                        className="flex-1 px-4 py-3 bg-card border border-border border border-[rgba(20,184,166,0.15)] rounded-xl focus:outline-none focus:ring-2 focus:ring-primary text-foreground"
                      />
                      <span className="px-4 py-3 bg-card border border-border rounded-xl border border-[rgba(20,184,166,0.15)] text-muted-foreground">
                        tokens
                      </span>
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-muted-foreground">切分方法</label>
                  <select className="w-full px-4 py-3 bg-card border border-border border border-[rgba(20,184,166,0.15)] rounded-xl focus:outline-none focus:ring-2 focus:ring-primary text-foreground bg-secondary">
                    <option>递归字符分割</option>
                    <option>固定大小分割</option>
                    <option>语义分割</option>
                  </select>
                </div>
              </div>
            </motion.div>
          )}

          {/* Retrieval Configuration Tab */}
          {activeTab === 'retrieval' && (
            <motion.div 
              className="space-y-8"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3 }}
            >
              {/* Default Parameters */}
              <div className="space-y-4">
                <h3 className="text-foreground">默认检索参数</h3>

                <div className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="text-muted-foreground">Top K</label>
                      <span className="text-primary px-3 py-1 rounded-lg bg-[rgba(20,184,166,0.08)] border border-[rgba(20,184,166,0.15)]">{topK[0]}</span>
                    </div>
                    <Slider
                      value={topK}
                      onValueChange={setTopK}
                      min={1}
                      max={20}
                      step={1}
                      className="w-full"
                    />
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="text-muted-foreground">相似度阈值</label>
                      <span className="text-primary px-3 py-1 rounded-lg bg-[rgba(20,184,166,0.08)] border border-[rgba(20,184,166,0.15)]">{similarityThreshold[0]}</span>
                    </div>
                    <Slider
                      value={similarityThreshold}
                      onValueChange={setSimilarityThreshold}
                      min={0}
                      max={1}
                      step={0.05}
                      className="w-full"
                    />
                  </div>
                </div>

                <div className="flex items-center gap-3 p-4 bg-card border border-border rounded-xl border border-[rgba(20,184,166,0.15)]">
                  <Switch checked={enableRerank} onCheckedChange={setEnableRerank} />
                  <label className="text-foreground">启用重排序</label>
                </div>

                {enableRerank && (
                  <motion.div 
                    className="space-y-2 ml-4 pl-4 border-l-2 border-[rgba(20,184,166,0.15)]"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                  >
                    <label className="text-muted-foreground">Rerank Top K</label>
                    <input
                      type="number"
                      defaultValue={3}
                      className="w-full px-4 py-3 bg-card border border-border border border-[rgba(20,184,166,0.15)] rounded-xl focus:outline-none focus:ring-2 focus:ring-primary text-foreground"
                    />
                  </motion.div>
                )}
              </div>

              {/* Search Mode */}
              <div className="space-y-4">
                <h3 className="text-foreground">搜索模式</h3>

                <div className="grid grid-cols-3 gap-4">
                  {[
                    { id: 'vector', label: '向量搜索', icon: '🔵', desc: '基于语义相似度' },
                    { id: 'hybrid', label: '混合搜索', icon: '⚫', desc: '结合向量和关键词' },
                    { id: 'keyword', label: '关键词搜索', icon: '⚪', desc: '基于关键词匹配' },
                  ].map((mode) => (
                    <motion.button
                      key={mode.id}
                      onClick={() => setSearchMode(mode.id)}
                      whileHover={{ scale: 1.05, y: -2 }}
                      whileTap={{ scale: 0.95 }}
                      className={`p-6 rounded-2xl border-2 transition-all text-center relative overflow-hidden group ${
                        searchMode === mode.id
                          ? 'border-primary bg-[rgba(20,184,166,0.08)] shadow-[0_0_15px_rgba(20,184,166,0.15)]'
                          : 'border-[rgba(20,184,166,0.15)] bg-card border border-border hover:border-[rgba(20,184,166,0.25)]'
                      }`}
                    >
                      {searchMode === mode.id && (
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-[rgba(20,184,166,0.08)] to-transparent" />
                      )}
                      <div className="relative z-10">
                        <div className="text-3xl mb-3">{mode.icon}</div>
                        <div className={`mb-2 ${searchMode === mode.id ? 'text-primary' : 'text-foreground'}`}>
                          {mode.label}
                        </div>
                        <div className="text-xs text-muted-foreground">{mode.desc}</div>
                      </div>
                    </motion.button>
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {/* General Settings Tab */}
          {activeTab === 'general' && (
            <motion.div 
              className="space-y-6"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3 }}
            >
              <div className="space-y-2">
                <label className="text-muted-foreground">语言</label>
                <select className="w-full px-4 py-3 bg-card border border-border border border-[rgba(20,184,166,0.15)] rounded-xl focus:outline-none focus:ring-2 focus:ring-primary text-foreground bg-secondary">
                  <option>🇨🇳 简体中文</option>
                  <option>🇺🇸 English</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-muted-foreground">最大文件大小</label>
                <div className="flex gap-2">
                  <input
                    type="number"
                    defaultValue={100}
                    className="flex-1 px-4 py-3 bg-card border border-border border border-[rgba(20,184,166,0.15)] rounded-xl focus:outline-none focus:ring-2 focus:ring-primary text-foreground"
                  />
                  <select className="px-4 py-3 bg-card border border-border border border-[rgba(20,184,166,0.15)] rounded-xl focus:outline-none focus:ring-2 focus:ring-primary text-foreground bg-secondary">
                    <option>MB</option>
                    <option>GB</option>
                  </select>
                </div>
              </div>

              <div className="space-y-3">
                <label className="text-muted-foreground">允许的文件类型</label>
                <div className="flex flex-wrap gap-2">
                  {['PDF', 'Markdown', 'Word', 'Image', 'Audio'].map((type) => (
                    <motion.button
                      key={type}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className="px-4 py-2 bg-[rgba(20,184,166,0.08)] text-primary rounded-xl hover:bg-primary/20 transition-all border border-[rgba(20,184,166,0.15)]"
                    >
                      {type}
                    </motion.button>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-muted-foreground">上传文件夹路径</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    defaultValue="/uploads/documents"
                    className="flex-1 px-4 py-3 bg-card border border-border border border-[rgba(20,184,166,0.15)] rounded-xl focus:outline-none focus:ring-2 focus:ring-primary text-foreground"
                  />
                  <motion.button 
                    className="px-6 py-3 bg-card border border-border border border-[rgba(20,184,166,0.15)] rounded-xl hover:bg-[rgba(20,184,166,0.04)] transition-all text-foreground"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    浏览
                  </motion.button>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </motion.div>

      {/* Bottom Action Bar */}
      <motion.div 
        className="flex items-center justify-between"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <motion.button
          onClick={handleResetSettings}
          className="text-primary hover:underline"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          恢复默认设置
        </motion.button>

        <div className="flex gap-3">
          <motion.button
            onClick={handleSaveSettings}
            className="px-6 py-3 bg-card border border-border border border-[rgba(20,184,166,0.15)] rounded-xl hover:bg-[rgba(20,184,166,0.04)] transition-all text-foreground"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            重置
          </motion.button>
          <motion.button
            onClick={handleSaveSettings}
            className="px-6 py-3 bg-primary text-primary-foreground rounded-xl hover:shadow-[0_0_20px_rgba(20,184,166,0.2)] transition-all relative overflow-hidden group"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-0 group-hover:opacity-20" />
            <span className="relative z-10">保存设置</span>
          </motion.button>
        </div>
      </motion.div>
    </div>
  );
}
