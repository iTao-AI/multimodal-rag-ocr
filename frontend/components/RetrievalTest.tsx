import { Search, Download, Save, GitCompare, Eye, Sparkles, Loader2 } from 'lucide-react';
import { useState } from 'react';
import { motion } from 'motion/react';
import { toast } from 'sonner';
import { Slider } from './ui/slider';
import { config } from '../src/config';
import { safeFetchJSON } from '../src/api';

interface SearchResult {
  id: number;
  rank: number;
  similarity: number;
  rerank?: number;
  source: string;
  page: number;
  content: string;
}

export function RetrievalTest() {
  const [query, setQuery] = useState('');
  const [collectionName, setCollectionName] = useState('');
  const [topK, setTopK] = useState([5]);
  const [similarityThreshold, setSimilarityThreshold] = useState(0.7);
  const [enableRerank, setEnableRerank] = useState(true);
  const [searchMode, setSearchMode] = useState('hybrid');
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);

  const handleSearch = async () => {
    if (!query.trim()) {
      toast.warning('请输入搜索关键词');
      return;
    }
    if (!collectionName.trim()) {
      toast.warning('请输入知识库名称');
      return;
    }
    setSearching(true);
    setResults([]);
    try {
      const data = await safeFetchJSON(`${config.milvusApiUrl}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          collection_name: collectionName.trim(),
          query_text: query.trim(),
          top_k: topK[0],
        }),
      });
      if (data.status === 'success' && data.results) {
        const mappedResults: SearchResult[] = data.results.map((r: any, i: number) => ({
          id: i + 1,
          rank: i + 1,
          similarity: r.score || 0,
          source: r.filename || '未知',
          page: r.metadata?.page_start || 0,
          content: r.chunk_text?.slice(0, 200) || '',
        }));
        setResults(mappedResults);
        toast.success(`检索完成，找到 ${mappedResults.length} 个结果`);
      } else {
        toast.error(data.detail || '检索失败');
      }
    } catch (error) {
      console.error('检索失败:', error);
      toast.error(`检索失败: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setSearching(false);
    }
  };

  const highlightKeywords = (text: string, keywords: string[]) => {
    let highlighted = text;
    keywords.forEach((keyword) => {
      const regex = new RegExp(`(${keyword})`, 'gi');
      highlighted = highlighted.replace(regex, '<mark class="bg-[rgba(0,212,255,0.3)] text-primary px-1 rounded">$1</mark>');
    });
    return highlighted;
  };

  return (
    <div className="space-y-6">
      {/* Query Input */}
      <motion.div 
        className="bg-card border border-border rounded-2xl p-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="mb-4">
          <label className="text-sm text-muted-foreground mb-2 block">知识库名称</label>
          <input
            type="text"
            value={collectionName}
            onChange={(e) => setCollectionName(e.target.value)}
            placeholder="例如: my_knowledge_base"
            className="w-full px-4 py-3 bg-card border border-border border border-[rgba(0,212,255,0.2)] rounded-xl focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary text-foreground placeholder-muted-foreground transition-all duration-300"
          />
        </div>
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="💬 输入测试问题... 例如: 'RAG系统的主要用途是什么？'"
              className="w-full min-h-[100px] px-5 py-4 bg-card border border-border border border-[rgba(0,212,255,0.2)] rounded-xl focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary resize-none text-foreground placeholder-muted-foreground transition-all duration-300"
            />
          </div>
          <motion.button
            onClick={handleSearch}
            disabled={searching}
            className="w-40 h-12 bg-primary text-primary-foreground rounded-xl hover:shadow-[0_0_30px_rgba(0,212,255,0.6)] transition-all flex items-center justify-center gap-2 self-end relative overflow-hidden group disabled:opacity-50 disabled:cursor-not-allowed"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-0 group-hover:opacity-20 shimmer" />
            {searching ? <Loader2 size={20} className="animate-spin relative z-10" /> : <Search size={20} className="relative z-10" />}
            <span className="relative z-10">{searching ? '检索中...' : '检索'}</span>
          </motion.button>
        </div>
      </motion.div>

      {/* Configuration Panel */}
      <motion.div 
        className="bg-card border border-border rounded-2xl p-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center shadow-lg">
            <Sparkles size={20} className="text-primary-foreground" />
          </div>
          <h3 className="text-foreground">检索参数</h3>
        </div>

        {/* Parameters */}
        <div className="grid grid-cols-2 gap-6 mb-6">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-muted-foreground">Top K</label>
              <span className="text-primary px-3 py-1 rounded-lg bg-[rgba(0,212,255,0.1)] border border-[rgba(0,212,255,0.2)]">{topK[0]}</span>
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

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-muted-foreground">相似度阈值</label>
              <input
                type="number"
                value={similarityThreshold}
                onChange={(e) => setSimilarityThreshold(parseFloat(e.target.value))}
                min={0}
                max={1}
                step={0.05}
                className="w-24 px-3 py-1 bg-card border border-border border border-[rgba(0,212,255,0.2)] rounded-lg text-center focus:outline-none focus:ring-2 focus:ring-primary text-foreground"
              />
            </div>
          </div>
        </div>

        {/* Rerank Checkbox */}
        <div className="mb-6">
          <label className="flex items-center gap-3 cursor-pointer group">
            <div className="relative">
              <input
                type="checkbox"
                checked={enableRerank}
                onChange={(e) => setEnableRerank(e.target.checked)}
                className="w-5 h-5 rounded border-[rgba(0,212,255,0.3)] text-primary focus:ring-2 focus:ring-primary bg-[rgba(15,18,53,0.6)] cursor-pointer"
              />
            </div>
            <span className="text-foreground group-hover:text-primary transition-colors">启用Rerank</span>
          </label>
        </div>

        {/* Search Mode */}
        <div className="space-y-3">
          <label className="text-muted-foreground">搜索模式</label>
          <div className="grid grid-cols-3 gap-4">
            {[
              { id: 'vector', label: '向量', icon: '🔵', desc: '语义搜索' },
              { id: 'hybrid', label: '混合', icon: '⚫', desc: '最佳效果' },
              { id: 'keyword', label: '关键词', icon: '⚪', desc: '精确匹配' },
            ].map((mode) => (
              <motion.button
                key={mode.id}
                onClick={() => setSearchMode(mode.id)}
                whileHover={{ scale: 1.05, y: -2 }}
                whileTap={{ scale: 0.95 }}
                className={`p-4 rounded-xl border-2 transition-all flex flex-col items-center justify-center gap-2 relative overflow-hidden group ${
                  searchMode === mode.id
                    ? 'border-primary bg-[rgba(0,212,255,0.1)] shadow-[0_0_20px_rgba(0,212,255,0.3)]'
                    : 'border-[rgba(0,212,255,0.2)] bg-card border border-border hover:border-[rgba(0,212,255,0.4)]'
                }`}
              >
                {searchMode === mode.id && (
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-[rgba(0,212,255,0.2)] to-transparent shimmer" />
                )}
                <span className="text-2xl relative z-10">{mode.icon}</span>
                <span className={`relative z-10 ${searchMode === mode.id ? 'text-primary' : 'text-foreground'}`}>
                  {mode.label}
                </span>
                <span className="text-xs text-muted-foreground relative z-10">{mode.desc}</span>
              </motion.button>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Results Section */}
      <motion.div 
        className="bg-card border border-border rounded-2xl p-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-foreground flex items-center gap-2">
            <span className="text-2xl">📊</span>
            检索结果
          </h3>
          <span className="text-muted-foreground px-4 py-2 rounded-lg bg-card border border-border border border-[rgba(0,212,255,0.2)]">
            (共{results.length}个)
          </span>
        </div>

        {results.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <Search size={48} className="mx-auto mb-4 opacity-50" />
            <p>输入问题后点击"检索"按钮查看结果</p>
          </div>
        ) : (
        <div className="space-y-4">
          {results.map((result, index) => (
            <motion.div
              key={result.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 + index * 0.1 }}
              whileHover={{ y: -2 }}
              className="bg-card border border-border border border-[rgba(0,212,255,0.2)] rounded-xl p-6 hover:border-[rgba(0,212,255,0.4)] hover:shadow-[0_0_20px_rgba(0,212,255,0.2)] transition-all relative overflow-hidden group"
            >
              {/* Hover effect */}
              <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500">
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-[rgba(0,212,255,0.05)] to-transparent shimmer" />
              </div>

              {/* Rank Badge */}
              <div className="absolute top-4 left-4 w-10 h-10 bg-primary text-primary-foreground rounded-xl flex items-center justify-center shadow-lg z-10">
                #{result.rank}
              </div>

              <div className="ml-14 relative z-10">
                {/* Score Visualization */}
                <div className="mb-4 space-y-3">
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-muted-foreground w-20">相似度:</span>
                    <div className="flex-1 h-2.5 bg-[rgba(15,18,53,0.8)] rounded-full overflow-hidden border border-[rgba(0,212,255,0.2)]">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${result.similarity * 100}%` }}
                        transition={{ duration: 1, delay: 0.5 + index * 0.1 }}
                        className="h-full bg-primary relative overflow-hidden"
                      >
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-30 shimmer" />
                      </motion.div>
                    </div>
                    <span className="text-sm text-primary w-14 text-right">{result.similarity}</span>
                  </div>

                  {enableRerank && result.rerank !== undefined && (
                    <div className="flex items-center gap-4">
                      <span className="text-sm text-muted-foreground w-20">重排序:</span>
                      <div className="flex-1 h-2.5 bg-[rgba(15,18,53,0.8)] rounded-full overflow-hidden border border-success/20">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${result.rerank * 100}%` }}
                          transition={{ duration: 1, delay: 0.6 + index * 0.1 }}
                          className="h-full bg-success relative overflow-hidden"
                        >
                          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-30 shimmer" />
                        </motion.div>
                      </div>
                      <span className="text-sm text-success w-14 text-right">{result.rerank}</span>
                    </div>
                  )}
                </div>

                {/* Source Info */}
                <div className="mb-3 text-foreground flex items-center gap-2">
                  <span>📄</span>
                  <span>{result.source}</span>
                  <span className="text-muted-foreground">- 第{result.page}页</span>
                </div>

                {/* Content Preview */}
                <div className="bg-card border border-border rounded-xl p-4 mb-4 text-sm text-muted-foreground max-h-[120px] overflow-auto">
                  <div dangerouslySetInnerHTML={{ __html: highlightKeywords(result.content, ['RAG', 'retrieval', 'generation']) }} />
                </div>

                {/* Action Buttons */}
                <div className="flex gap-3">
                  <motion.button 
                    className="px-4 py-2 border border-primary text-primary rounded-xl hover:bg-primary/10 transition-all flex items-center gap-2"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <Eye size={16} />
                    查看完整Chunk
                  </motion.button>
                  <motion.button 
                    className="px-4 py-2 border border-primary text-primary rounded-xl hover:bg-primary/10 transition-all"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    查看原始页面
                  </motion.button>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
        )}
      </motion.div>

      {/* Bottom Action Bar */}
      <motion.div 
        className="flex gap-4"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
      >
        <motion.button 
          className="flex-1 px-6 py-4 bg-card border border-border border border-[rgba(0,212,255,0.2)] rounded-xl hover:bg-[rgba(0,212,255,0.05)] hover:border-[rgba(0,212,255,0.4)] transition-all flex items-center justify-center gap-2 text-foreground group"
          whileHover={{ scale: 1.02, y: -2 }}
          whileTap={{ scale: 0.98 }}
        >
          <Download size={18} className="group-hover:text-primary transition-colors" />
          <span>导出结果</span>
        </motion.button>
        <motion.button 
          className="flex-1 px-6 py-4 bg-card border border-border border border-[rgba(0,212,255,0.2)] rounded-xl hover:bg-[rgba(0,212,255,0.05)] hover:border-[rgba(0,212,255,0.4)] transition-all flex items-center justify-center gap-2 text-foreground group"
          whileHover={{ scale: 1.02, y: -2 }}
          whileTap={{ scale: 0.98 }}
        >
          <Save size={18} className="group-hover:text-primary transition-colors" />
          <span>保存测试案例</span>
        </motion.button>
        <motion.button 
          className="flex-1 px-6 py-4 bg-primary text-primary-foreground rounded-xl hover:shadow-[0_0_30px_rgba(0,212,255,0.6)] transition-all flex items-center justify-center gap-2 relative overflow-hidden group"
          whileHover={{ scale: 1.02, y: -2 }}
          whileTap={{ scale: 0.98 }}
        >
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-0 group-hover:opacity-20 shimmer" />
          <GitCompare size={18} className="relative z-10" />
          <span className="relative z-10">对比不同参数</span>
        </motion.button>
      </motion.div>
    </div>
  );
}
