/**
 * API 配置 — 方法驱动端点自动路由
 *
 * 不再有全局 isV2 版本切换。用户直接选择提取方法/分块方法，
 * 端点根据所选方法自动确定。
 */

export type ExtractionMode = 'fast' | 'vlm' | 'mineru' | 'deepseek' | 'paddleocr_vl';
export type ChunkMethod = 'header_recursive' | 'markdown_only' | 'ocr_aware' | 'layout_based';

export interface ExtractionMethod {
  id: ExtractionMode;
  label: string;
  description: string;
  /** 该方法对应的上传端点 */
  endpoint: string;
}

/** 全部 5 个提取方法，各自带端点路由 */
const ALL_EXTRACTION_METHODS: ExtractionMethod[] = [
  {
    id: 'fast',
    label: '快速模式 (PyMuPDF4LLM)',
    description: '适合简单文档，速度快',
    endpoint: '/api/v1/files/upload',
  },
  {
    id: 'vlm',
    label: '精确模式 (VLM)',
    description: '支持复杂布局，使用视觉语言模型',
    endpoint: '/api/v1/files/upload',
  },
  {
    id: 'mineru',
    label: 'MinerU',
    description: '高质量 PDF 解析，支持复杂版面结构',
    endpoint: '/api/v2/files/upload',
  },
  {
    id: 'deepseek',
    label: 'DeepSeek-OCR',
    description: 'AI 驱动 OCR，支持复杂场景和多语言',
    endpoint: '/api/v2/files/upload',
  },
  {
    id: 'paddleocr_vl',
    label: 'PaddleOCR-VL',
    description: '视觉语言模型 OCR，高精度文字识别',
    endpoint: '/api/v2/files/upload',
  },
];

/** 全部 4 个分块方法 */
const ALL_CHUNK_METHODS: ChunkMethod[] = [
  'header_recursive',
  'markdown_only',
  'ocr_aware',
  'layout_based',
];

/** 返回全部提取方法（无参数） */
export const getAllExtractionMethods = (): ExtractionMethod[] => {
  return ALL_EXTRACTION_METHODS;
};

/** 返回全部提取方法（向后兼容旧调用方，无参数） */
export const getExtractionMethods = (): ExtractionMethod[] => {
  return getAllExtractionMethods();
};

/** 根据方法 ID 返回正确上传端点 */
export const getUploadEndpointByMethod = (method: string): string => {
  const found = ALL_EXTRACTION_METHODS.find(m => m.id === method);
  return found?.endpoint ?? '/api/v1/files/upload';
};

/** 返回默认提取方法 ID（无参数） */
export const getDefaultExtractionMethod = (): string => {
  return 'fast';
};

/** 返回全部分块方法（无参数） */
export const getChunkMethods = (): ChunkMethod[] => {
  return ALL_CHUNK_METHODS;
};
