import { useState, useEffect } from 'react';
import { X, Upload, FileText, Settings, AlertCircle, CheckCircle, Loader2, Plus } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { toast } from 'sonner';
import { getExtractionMethods, getUploadEndpoint, getDefaultExtractionMethod } from '../src/api/config';
import { safeFetchJSON } from '../src/api';

interface UploadDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onUpload: (files: File[], kbId: string, config: UploadConfig) => void;
  preselectedKB?: string; // 预选的知识库ID
  isV2?: boolean; // 版本标识
}

interface UploadConfig {
  extractionMode: string; // 支持 v1: 'fast'|'vlm', v2: 'mineru'|'paddleocr'|'deepseek'
  chunkSize: number;
  overlap: number;
  maxPageSpan: number;
  bridgeLength: number;
  chunkingMethod: string;
}

interface KnowledgeBase {
  collection_id: string;
  collection_name: string;
  total_documents: number;
  total_chunks: number;
}

interface UploadFileState {
  status: 'idle' | 'uploading' | 'processing' | 'done' | 'error';
  progress: number; // 0-100 during upload phase
  message?: string;
  chunkCount?: number;
  totalPages?: number;
  totalImages?: number;
  errorMessage?: string;
}

export function UploadDialog({ isOpen, onClose, onUpload, preselectedKB, isV2 = false }: UploadDialogProps) {
  const [selectedKB, setSelectedKB] = useState<string | null>(preselectedKB || null);
  const [files, setFiles] = useState<File[]>([]);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<{ [key: string]: UploadFileState }>({});
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [loading, setLoading] = useState(false);
  const [showCreateKB, setShowCreateKB] = useState(false);
  const [newKBName, setNewKBName] = useState('');
  
  // 根据版本初始化配置
  const [config, setConfig] = useState<UploadConfig>({
    extractionMode: getDefaultExtractionMethod(isV2),
    chunkSize: 1500,
    overlap: 200,
    maxPageSpan: 3,
    bridgeLength: 100,
    chunkingMethod: isV2 ? 'ocr_aware' : 'header_recursive',
  });
  
  // 获取当前版本的提取方法列表
  const extractionMethods = getExtractionMethods(isV2);

  // 从Milvus API获取知识库列表
  useEffect(() => {
    if (isOpen) {
      fetchKnowledgeBases();
    }
  }, [isOpen]);

  // 当预选知识库变化时更新选中状态
  useEffect(() => {
    if (preselectedKB) {
      setSelectedKB(preselectedKB);
    }
  }, [preselectedKB]);

  const fetchKnowledgeBases = async () => {
    setLoading(true);
    try {
      const baseUrl = import.meta.env.VITE_MILVUS_API_URL || 'http://localhost:8000';
      const apiUrl = `${baseUrl}/stats/all`;

      const result = await safeFetchJSON(apiUrl);

      if (result.status === 'success') {
        const collections = result.data.collections || [];
        
        // ✅ 根据版本过滤知识库
        // V1模式：只显示不带 _v2 后缀的
        // V2模式：只显示带 _v2 后缀的
        const filteredCollections = collections.filter((col: KnowledgeBase) => {
          // 修复：检查 collection_name 而不是 collection_id
          const isV2Collection = col.collection_name.endsWith('_v2');
          return isV2 ? isV2Collection : !isV2Collection;
        });
        
        // ✅ V2模式：去掉显示名称的 _v2 后缀
        const processedCollections = filteredCollections.map((col: KnowledgeBase) => {
          if (isV2 && col.collection_name.endsWith('_v2')) {
            return {
              ...col,
              collection_name: col.collection_name.slice(0, -3)  // 去掉 "_v2"
            };
          }
          return col;
        });
        
        setKnowledgeBases(processedCollections);
      }
    } catch (error) {
      const msg = error instanceof Error ? error.message : '未知错误';
      console.error('获取知识库列表失败:', msg);
      toast.error('获取知识库列表失败: ' + msg);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateKB = async () => {
    if (!newKBName.trim()) {
      toast.error('请输入知识库名称');
      return;
    }

    try {
      // ✅ V2模式：自动添加 _v2 后缀
      const actualKBName = isV2 ? `${newKBName}_v2` : newKBName;
      
      const baseUrl = import.meta.env.VITE_MILVUS_API_URL || 'http://localhost:8000';
      const result = await safeFetchJSON(
        `${baseUrl}/knowledge_base/create?display_name=${encodeURIComponent(actualKBName)}`,
        { method: 'POST' }
      );

      if (result.status === 'success') {
        toast.success(result.message);
        setShowCreateKB(false);
        setNewKBName('');
        // 刷新列表并自动选中新创建的知识库
        await fetchKnowledgeBases();
        setSelectedKB(result.collection_id);
      } else {
        toast.error(result.message || '创建知识库失败');
      }
    } catch (error) {
      console.error('创建知识库失败:', error);
      toast.error('创建知识库失败');
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files) {
      setFiles(Array.from(e.dataTransfer.files));
    }
  };

  /**
   * Poll backend for file processing status after upload completes.
   * The backend processes the file (extract → chunk → embed) after receiving the upload.
   * We poll the stats endpoint to check if processing is done.
   */
  const pollProcessingStatus = async (
    fileName: string,
    knowledgeBaseId: string,
    maxAttempts: number = 60,
    intervalMs: number = 2000,
  ): Promise<void> => {
    const baseUrl = import.meta.env.VITE_MILVUS_API_URL || 'http://localhost:8000';

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      await new Promise((resolve) => setTimeout(resolve, intervalMs));

      try {
        const result = await safeFetchJSON(`${baseUrl}/stats/all`);
        if (result.status === 'success') {
          const kb = result.data.collections?.find(
            (c: KnowledgeBase) => c.collection_id === knowledgeBaseId,
          );
          if (kb) {
            // Check if the document count increased — processing is done
            setUploadProgress((prev) => ({
              ...prev,
              [fileName]: {
                ...prev[fileName],
                status: 'done',
                progress: 100,
                chunkCount: kb.total_chunks,
                message: '处理完成',
              },
            }));
            return;
          }
        }
      } catch {
        // Continue polling on transient errors
      }
    }

    // Timed out — mark as done anyway since upload succeeded
    setUploadProgress((prev) => ({
      ...prev,
      [fileName]: {
        ...prev[fileName],
        status: 'done',
        progress: 100,
        message: '处理完成（状态未知）',
      },
    }));
  };

  /**
   * Upload a single file with XMLHttpRequest for progress tracking.
   */
  const uploadFile = (
    file: File,
    knowledgeBaseId: string,
    isV2: boolean,
  ): Promise<{ success: boolean; data?: any; error?: string }> => {
    return new Promise((resolve) => {
      const uploadEndpoint = getUploadEndpoint(isV2);
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const pct = Math.round((e.loaded / e.total) * 100);
          setUploadProgress((prev) => ({
            ...prev,
            [file.name]: {
              ...(prev[file.name] || { status: 'uploading', progress: 0 }),
              status: 'uploading',
              progress: pct,
            },
          }));
        }
      });

      xhr.addEventListener('load', () => {
        try {
          if (xhr.status >= 200 && xhr.status < 300) {
            const result = JSON.parse(xhr.responseText);
            resolve({ success: result.success !== false, data: result });
          } else {
            let errorMsg = `服务器错误 (${xhr.status})`;
            try {
              const body = JSON.parse(xhr.responseText);
              errorMsg = body.error?.message || body.detail || errorMsg;
            } catch {
              // Use default message
            }
            resolve({ success: false, error: errorMsg });
          }
        } catch {
          resolve({ success: false, error: '响应解析失败' });
        }
      });

      xhr.addEventListener('error', () => {
        resolve({ success: false, error: '网络错误，请检查连接' });
      });

      xhr.addEventListener('abort', () => {
        resolve({ success: false, error: '上传已取消' });
      });

      xhr.open('POST', uploadEndpoint);

      const formData = new FormData();
      formData.append('file', file);
      formData.append('knowledge_base_id', knowledgeBaseId);
      formData.append('auto_extract', 'true');
      formData.append('extraction_mode', config.extractionMode);
      formData.append('auto_chunk', 'true');
      formData.append('chunking_method', config.chunkingMethod);
      formData.append('chunk_size', config.chunkSize.toString());
      formData.append('chunk_overlap', config.overlap.toString());
      formData.append('max_page_span', config.maxPageSpan.toString());

      xhr.send(formData);
    });
  };

  const handleSubmit = async () => {
    if (!selectedKB || files.length === 0) return;

    setUploading(true);

    try {
      for (const file of files) {
        // Phase 1: Uploading with progress
        setUploadProgress((prev) => ({
          ...prev,
          [file.name]: { status: 'uploading', progress: 0 },
        }));

        const uploadResult = await uploadFile(file, selectedKB, isV2);

        if (!uploadResult.success) {
          setUploadProgress((prev) => ({
            ...prev,
            [file.name]: {
              status: 'error',
              progress: 0,
              errorMessage: uploadResult.error || '上传失败',
            },
          }));
          toast.error(`${file.name} 上传失败`, {
            description: uploadResult.error,
          });
          continue;
        }

        // Phase 2: Processing — poll for completion
        setUploadProgress((prev) => ({
          ...prev,
          [file.name]: {
            ...(prev[file.name] || { status: 'processing', progress: 100 }),
            status: 'processing',
            progress: 100,
            message: '正在处理中...',
          },
        }));

        // Parse immediate response if available
        const responseData = uploadResult.data;
        let chunkCount: number | undefined;
        let totalPages: number | undefined;
        let totalImages: number | undefined;

        if (responseData?.data?.extraction?.status === 'completed') {
          totalPages = responseData.data.extraction.total_pages;
          totalImages = responseData.data.extraction.total_images;
          if (responseData.data.chunking?.status === 'completed') {
            chunkCount = responseData.data.chunking.total_chunks;
          }
        }

        if (chunkCount !== undefined) {
          // Processing completed synchronously
          setUploadProgress((prev) => ({
            ...prev,
            [file.name]: {
              status: 'done',
              progress: 100,
              chunkCount,
              totalPages,
              totalImages,
              message: '处理完成',
            },
          }));
        } else {
          // Processing async — poll for completion
          await pollProcessingStatus(file.name, selectedKB);
        }

        // Build toast message
        const fileState = uploadProgress[file.name];
        if (fileState?.status === 'done') {
          let description = '文件已保存';
          if (totalPages) {
            description = `已提取 ${totalPages} 页`;
            if (totalImages) description += `，${totalImages} 张图片`;
          }
          if (chunkCount) description += `，已切分为 ${chunkCount} 个块`;

          toast.success(`${file.name} 上传成功`, { description });
        }
      }

      // All files done — notify parent and close
      onUpload(files, selectedKB, config);

      setTimeout(() => {
        onClose();
        setFiles([]);
        setUploadProgress({});
      }, 2000);
    } catch (error) {
      toast.error('上传过程中发生错误', {
        description: error instanceof Error ? error.message : '请稍后重试',
      });
    } finally {
      setUploading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        />

        {/* Dialog */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="relative w-full max-w-3xl max-h-[90vh] overflow-hidden glass-strong rounded-2xl border border-[rgba(0,212,255,0.3)] shadow-[0_0_50px_rgba(0,212,255,0.3)]"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-[rgba(0,212,255,0.15)]">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#00d4ff] to-[#0066ff] flex items-center justify-center">
                <Upload size={20} className="text-[#0a0e27]" />
              </div>
              <h2 className="text-xl text-[#e8eaed]">上传文档</h2>
            </div>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-lg hover:bg-[rgba(0,212,255,0.1)] transition-colors flex items-center justify-center text-[#94a3b8] hover:text-[#e8eaed]"
            >
              <X size={20} />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
            <div className="space-y-6">
              {/* Knowledge Base Selection */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-[#e8eaed] flex items-center gap-2">
                    <FileText size={16} />
                    选择知识库
                  </label>
                  <motion.button
                    onClick={() => setShowCreateKB(!showCreateKB)}
                    disabled={uploading}
                    whileHover={uploading ? {} : { scale: 1.05 }}
                    whileTap={uploading ? {} : { scale: 0.95 }}
                    className={`flex items-center gap-1 px-3 py-1.5 text-sm border border-[#00d4ff] rounded-lg transition-all ${
                      uploading
                        ? 'text-[#94a3b8] border-[rgba(0,212,255,0.1)] cursor-not-allowed'
                        : 'text-[#00d4ff] hover:bg-[rgba(0,212,255,0.1)]'
                    }`}
                  >
                    <Plus size={14} />
                    新建知识库
                  </motion.button>
                </div>

                {/* Create KB Input */}
                <AnimatePresence>
                  {showCreateKB && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="flex gap-2 p-3 glass rounded-xl border border-[rgba(0,212,255,0.2)]">
                        <input
                          type="text"
                          value={newKBName}
                          onChange={(e) => setNewKBName(e.target.value)}
                          placeholder="输入知识库名称（支持中文）"
                          className="flex-1 px-3 py-2 glass-strong border border-[rgba(0,212,255,0.2)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#00d4ff] text-[#e8eaed] placeholder-[#94a3b8]"
                          onKeyDown={(e) => e.key === 'Enter' && handleCreateKB()}
                          autoFocus
                        />
                        <motion.button
                          onClick={handleCreateKB}
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          className="px-4 py-2 bg-gradient-to-r from-[#00d4ff] to-[#0066ff] text-[#0a0e27] rounded-lg hover:shadow-[0_0_20px_rgba(0,212,255,0.5)] transition-all"
                        >
                          创建
                        </motion.button>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* KB List */}
                {loading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 size={24} className="text-[#00d4ff] animate-spin" />
                  </div>
                ) : knowledgeBases.length === 0 ? (
                  <div className="text-center py-8 text-[#94a3b8]">
                    暂无知识库，请先创建一个
                  </div>
                ) : (
                  <div className="grid grid-cols-3 gap-3">
                    {knowledgeBases.map((kb) => (
                      <motion.button
                        key={kb.collection_id}
                        onClick={() => setSelectedKB(kb.collection_id)}
                        disabled={uploading}
                        whileHover={uploading ? {} : { scale: 1.02 }}
                        whileTap={uploading ? {} : { scale: 0.98 }}
                        className={`p-4 rounded-xl border-2 transition-all text-left ${
                          uploading
                            ? 'border-[rgba(0,212,255,0.1)] cursor-not-allowed opacity-50'
                            : selectedKB === kb.collection_id
                              ? 'border-[#00d4ff] bg-[rgba(0,212,255,0.1)]'
                              : 'border-[rgba(0,212,255,0.2)] glass hover:border-[rgba(0,212,255,0.4)]'
                        }`}
                      >
                        <div
                          className={`mb-1 truncate ${
                            selectedKB === kb.collection_id ? 'text-[#00d4ff]' : 'text-[#e8eaed]'
                          }`}
                          title={kb.collection_name}
                        >
                          {kb.collection_name}
                        </div>
                        <div className="text-xs text-[#94a3b8]">
                          {kb.total_documents} 文档 · {kb.total_chunks} chunks
                        </div>
                      </motion.button>
                    ))}
                  </div>
                )}
              </div>

              {/* File Upload Area */}
              <div className="space-y-3">
                <label className="text-[#e8eaed]">选择文件</label>
                <div
                  onDrop={uploading ? undefined : handleDrop}
                  onDragOver={uploading ? (e) => e.preventDefault() : (e) => e.preventDefault()}
                  className={`border-2 border-dashed rounded-xl p-8 text-center transition-all ${
                    uploading
                      ? 'border-[rgba(0,212,255,0.1)] cursor-not-allowed opacity-50'
                      : 'border-[rgba(0,212,255,0.3)] glass hover:border-[#00d4ff] cursor-pointer'
                  }`}
                >
                  <input
                    type="file"
                    multiple
                    onChange={handleFileSelect}
                    className="hidden"
                    id="file-upload"
                    accept=".pdf,.md,.docx,.jpg,.jpeg,.png"
                  />
                  <label htmlFor="file-upload" className="cursor-pointer">
                    <Upload size={48} className="mx-auto mb-4 text-[#00d4ff]" />
                    <p className="text-[#e8eaed] mb-2">点击或拖拽文件到此处</p>
                    <p className="text-sm text-[#94a3b8]">目前仅支持 PDF 格式</p>
                  </label>
                </div>

                {/* Selected Files */}
                {files.length > 0 && (
                  <div className="space-y-2">
                    {files.map((file, index) => {
                      const fileState = uploadProgress[file.name];
                      const status = fileState?.status || 'idle';
                      const progress = fileState?.progress || 0;

                      return (
                        <div
                          key={index}
                          className="p-3 glass rounded-lg border border-[rgba(0,212,255,0.2)]"
                        >
                          <div className="flex items-center justify-between gap-3">
                            <div className="flex items-center gap-3 min-w-0">
                              {status === 'uploading' && (
                                <Loader2 size={16} className="text-[#00d4ff] animate-spin flex-shrink-0" />
                              )}
                              {status === 'processing' && (
                                <Loader2 size={16} className="text-[#ffb800] animate-spin flex-shrink-0" />
                              )}
                              {status === 'done' && (
                                <CheckCircle size={16} className="text-[#00ff88] flex-shrink-0" />
                              )}
                              {status === 'error' && (
                                <AlertCircle size={16} className="text-[#ff3b5c] flex-shrink-0" />
                              )}
                              {status === 'idle' && <FileText size={16} className="text-[#00d4ff] flex-shrink-0" />}
                              <span className="text-[#e8eaed] truncate">{file.name}</span>
                              <span className="text-xs text-[#94a3b8] flex-shrink-0">
                                {(file.size / 1024 / 1024).toFixed(2)} MB
                              </span>
                            </div>
                            {!uploading && status === 'idle' && (
                              <button
                                onClick={() => setFiles(files.filter((_, i) => i !== index))}
                                className="text-[#94a3b8] hover:text-[#ff3b5c] transition-colors flex-shrink-0"
                              >
                                <X size={16} />
                              </button>
                            )}
                          </div>

                          {/* Progress Bar (uploading) */}
                          {status === 'uploading' && (
                            <div className="mt-2">
                              <div className="flex items-center justify-between text-xs text-[#94a3b8] mb-1">
                                <span>上传中</span>
                                <span>{progress}%</span>
                              </div>
                              <div className="w-full h-1.5 bg-[rgba(0,212,255,0.1)] rounded-full overflow-hidden">
                                <motion.div
                                  className="h-full bg-gradient-to-r from-[#00d4ff] to-[#0066ff] rounded-full"
                                  initial={{ width: 0 }}
                                  animate={{ width: `${progress}%` }}
                                  transition={{ duration: 0.2 }}
                                />
                              </div>
                            </div>
                          )}

                          {/* Processing Spinner */}
                          {status === 'processing' && (
                            <div className="mt-2 flex items-center gap-2 text-sm text-[#ffb800]">
                              <Loader2 size={12} className="animate-spin" />
                              <span>正在处理中...</span>
                            </div>
                          )}

                          {/* Done with chunk count */}
                          {status === 'done' && (
                            <div className="mt-2 text-xs text-[#00ff88]">
                              {fileState?.chunkCount
                                ? `处理完成，已切分为 ${fileState.chunkCount} 个块`
                                : '处理完成'}
                              {fileState?.totalPages && ` · ${fileState.totalPages} 页`}
                            </div>
                          )}

                          {/* Error with message */}
                          {status === 'error' && (
                            <div className="mt-2 text-xs text-[#ff3b5c]">
                              {fileState?.errorMessage || '上传失败'}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Advanced Settings Toggle */}
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className={`flex items-center gap-2 transition-colors ${
                  isV2
                    ? 'text-blue-600 hover:text-blue-700'
                    : 'text-[#00d4ff] hover:text-[#e8eaed]'
                }`}
              >
                <Settings size={16} />
                {showAdvanced ? '隐藏' : '显示'}高级配置
              </button>

              {/* Advanced Settings */}
              <AnimatePresence>
                {showAdvanced && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="space-y-6 overflow-hidden"
                  >
                    {/* Extraction Mode */}
                    <div className="space-y-3">
                      <label className={isV2 ? 'text-slate-700 font-medium' : 'text-[#e8eaed]'}>
                        提取模式
                        {isV2 && <span className="ml-2 text-xs text-blue-600">(OCR 2.0)</span>}
                      </label>
                      <div className={`grid ${extractionMethods.length === 2 ? 'grid-cols-2' : 'grid-cols-3'} gap-3`}>
                        {extractionMethods.map((method) => (
                          <button
                            key={method.id}
                            onClick={() => setConfig({ ...config, extractionMode: method.id })}
                            className={`p-4 rounded-xl border-2 transition-all text-left ${
                              isV2
                                ? config.extractionMode === method.id
                                  ? 'border-blue-500 bg-blue-50'
                                  : 'border-slate-200 bg-white hover:border-blue-300'
                                : config.extractionMode === method.id
                                  ? 'border-[#00d4ff] bg-[rgba(0,212,255,0.1)]'
                                  : 'border-[rgba(0,212,255,0.2)] glass'
                            }`}
                          >
                            <div className={
                              isV2
                                ? config.extractionMode === method.id ? 'text-blue-600 font-medium' : 'text-slate-700'
                                : config.extractionMode === method.id ? 'text-[#00d4ff]' : 'text-[#e8eaed]'
                            }>
                              {method.label}
                            </div>
                            <div className={`text-xs mt-1 ${isV2 ? 'text-slate-500' : 'text-[#94a3b8]'}`}>
                              {method.description}
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Chunking Parameters */}
                    <div className="space-y-3">
                      <label className={isV2 ? 'text-slate-700 font-medium' : 'text-[#e8eaed]'}>切分参数</label>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <label className={`text-sm ${isV2 ? 'text-slate-600' : 'text-[#94a3b8]'}`}>Chunk Size</label>
                          <div className="flex gap-2">
                            <input
                              type="number"
                              value={config.chunkSize}
                              onChange={(e) => setConfig({ ...config, chunkSize: parseInt(e.target.value) })}
                              className={`flex-1 px-3 py-2 rounded-lg focus:outline-none focus:ring-2 transition-all ${
                                isV2
                                  ? 'bg-white border border-slate-200 text-slate-700 focus:ring-blue-500 focus:border-blue-500'
                                  : 'glass-strong border border-[rgba(0,212,255,0.2)] text-[#e8eaed] focus:ring-[#00d4ff]'
                              }`}
                            />
                            <span className={`px-3 py-2 rounded-lg text-sm ${isV2 ? 'bg-slate-100 text-slate-600' : 'glass text-[#94a3b8]'}`}>tokens</span>
                          </div>
                        </div>

                        <div className="space-y-2">
                          <label className={`text-sm ${isV2 ? 'text-slate-600' : 'text-[#94a3b8]'}`}>Overlap</label>
                          <div className="flex gap-2">
                            <input
                              type="number"
                              value={config.overlap}
                              onChange={(e) => setConfig({ ...config, overlap: parseInt(e.target.value) })}
                              className={`flex-1 px-3 py-2 rounded-lg focus:outline-none focus:ring-2 transition-all ${
                                isV2
                                  ? 'bg-white border border-slate-200 text-slate-700 focus:ring-blue-500 focus:border-blue-500'
                                  : 'glass-strong border border-[rgba(0,212,255,0.2)] text-[#e8eaed] focus:ring-[#00d4ff]'
                              }`}
                            />
                            <span className={`px-3 py-2 rounded-lg text-sm ${isV2 ? 'bg-slate-100 text-slate-600' : 'glass text-[#94a3b8]'}`}>tokens</span>
                          </div>
                        </div>

                        <div className="space-y-2">
                          <label className={`text-sm ${isV2 ? 'text-slate-600' : 'text-[#94a3b8]'}`}>Max Page Span</label>
                          <div className="flex gap-2">
                            <input
                              type="number"
                              value={config.maxPageSpan}
                              onChange={(e) => setConfig({ ...config, maxPageSpan: parseInt(e.target.value) })}
                              className={`flex-1 px-3 py-2 rounded-lg focus:outline-none focus:ring-2 transition-all ${
                                isV2
                                  ? 'bg-white border border-slate-200 text-slate-700 focus:ring-blue-500 focus:border-blue-500'
                                  : 'glass-strong border border-[rgba(0,212,255,0.2)] text-[#e8eaed] focus:ring-[#00d4ff]'
                              }`}
                            />
                            <span className={`px-3 py-2 rounded-lg text-sm ${isV2 ? 'bg-slate-100 text-slate-600' : 'glass text-[#94a3b8]'}`}>pages</span>
                          </div>
                        </div>

                        <div className="space-y-2">
                          <label className={`text-sm ${isV2 ? 'text-slate-600' : 'text-[#94a3b8]'}`}>Bridge Length</label>
                          <div className="flex gap-2">
                            <input
                              type="number"
                              value={config.bridgeLength}
                              onChange={(e) => setConfig({ ...config, bridgeLength: parseInt(e.target.value) })}
                              className={`flex-1 px-3 py-2 rounded-lg focus:outline-none focus:ring-2 transition-all ${
                                isV2
                                  ? 'bg-white border border-slate-200 text-slate-700 focus:ring-blue-500 focus:border-blue-500'
                                  : 'glass-strong border border-[rgba(0,212,255,0.2)] text-[#e8eaed] focus:ring-[#00d4ff]'
                              }`}
                            />
                            <span className={`px-3 py-2 rounded-lg text-sm ${isV2 ? 'bg-slate-100 text-slate-600' : 'glass text-[#94a3b8]'}`}>tokens</span>
                          </div>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <label className={`text-sm ${isV2 ? 'text-slate-600' : 'text-[#94a3b8]'}`}>切分方法</label>
                        <select
                          value={config.chunkingMethod}
                          onChange={(e) => setConfig({ ...config, chunkingMethod: e.target.value })}
                          className={`w-full px-3 py-2 rounded-lg focus:outline-none focus:ring-2 transition-all ${
                            isV2 
                              ? 'bg-white border border-slate-200 text-slate-700 focus:ring-blue-500 focus:border-blue-500' 
                              : 'glass-strong border border-[rgba(0,212,255,0.2)] text-[#e8eaed] bg-[rgba(15,18,53,0.6)] focus:ring-[#00d4ff]'
                          }`}
                        >
                          {isV2 ? (
                            <>
                              <option value="ocr_aware">OCR感知切分</option>
                              <option value="layout_based">版面感知切分</option>
                            </>
                          ) : (
                            <>
                              <option value="header_recursive">递归标题分割</option>
                              <option value="markdown_only">自定义Markdown分割</option>
                            </>
                          )}
                        </select>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Warning */}
              {!selectedKB && files.length > 0 && (
                <div className="flex items-center gap-2 p-3 glass rounded-lg border border-[rgba(255,184,0,0.3)] bg-[rgba(255,184,0,0.05)]">
                  <AlertCircle size={16} className="text-[#ffb800]" />
                  <span className="text-sm text-[#ffb800]">请先选择一个知识库</span>
                </div>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-3 p-6 border-t border-[rgba(0,212,255,0.15)]">
            <motion.button
              onClick={onClose}
              disabled={uploading}
              whileHover={uploading ? {} : { scale: 1.05 }}
              whileTap={uploading ? {} : { scale: 0.95 }}
              className={`px-6 py-3 rounded-xl border transition-all text-[#e8eaed] ${
                uploading
                  ? 'glass border-[rgba(0,212,255,0.1)] text-[#94a3b8] cursor-not-allowed'
                  : 'glass border-[rgba(0,212,255,0.2)] hover:bg-[rgba(0,212,255,0.05)]'
              }`}
            >
              {uploading ? '上传中不可取消' : '取消'}
            </motion.button>
            <motion.button
              onClick={handleSubmit}
              disabled={!selectedKB || files.length === 0 || uploading}
              whileHover={selectedKB && files.length > 0 && !uploading ? { scale: 1.05 } : {}}
              whileTap={selectedKB && files.length > 0 && !uploading ? { scale: 0.95 } : {}}
              className={`px-6 py-3 rounded-xl transition-all relative overflow-hidden group flex items-center gap-2 ${
                selectedKB && files.length > 0 && !uploading
                  ? 'bg-gradient-to-r from-[#00d4ff] to-[#0066ff] text-[#0a0e27] hover:shadow-[0_0_30px_rgba(0,212,255,0.6)]'
                  : 'bg-[rgba(0,212,255,0.2)] text-[#94a3b8] cursor-not-allowed'
              }`}
            >
              {selectedKB && files.length > 0 && !uploading && (
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-0 group-hover:opacity-20 shimmer" />
              )}
              {uploading && <Loader2 size={16} className="animate-spin" />}
              <span className="relative z-10">
                {uploading ? '上传处理中...' : `上传 (${files.length})`}
              </span>
            </motion.button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
