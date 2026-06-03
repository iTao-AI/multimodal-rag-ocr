import { describe, it, expect } from 'vitest';
import {
  getExtractionMethods,
  getUploadEndpointByMethod,
  getDefaultExtractionMethod,
  getChunkMethods,
  getAllExtractionMethods,
} from '../config';

describe('getAllExtractionMethods', () => {
  it('返回全部 5 个提取方法，不接收任何参数', () => {
    const methods = getAllExtractionMethods();
    expect(methods).toHaveLength(5);
    const ids = methods.map(m => m.id);
    expect(ids).toContain('fast');
    expect(ids).toContain('vlm');
    expect(ids).toContain('mineru');
    expect(ids).toContain('deepseek');
    expect(ids).toContain('paddleocr_vl');
  });

  it('每个方法都有 id, label, description, endpoint 字段', () => {
    const methods = getAllExtractionMethods();
    for (const m of methods) {
      expect(m).toHaveProperty('id');
      expect(m).toHaveProperty('label');
      expect(m).toHaveProperty('description');
      expect(m).toHaveProperty('endpoint');
      expect(['/api/v1/files/upload', '/api/v2/files/upload']).toContain(m.endpoint);
    }
  });

  it('fast 和 vlm 路由到 v1 端点', () => {
    const methods = getAllExtractionMethods();
    for (const m of methods.filter(m => m.id === 'fast' || m.id === 'vlm')) {
      expect(m.endpoint).toBe('/api/v1/files/upload');
    }
  });

  it('mineru, deepseek, paddleocr_vl 路由到 v2 端点', () => {
    const methods = getAllExtractionMethods();
    for (const m of methods.filter(m => ['mineru', 'deepseek', 'paddleocr_vl'].includes(m.id))) {
      expect(m.endpoint).toBe('/api/v2/files/upload');
    }
  });
});

describe('getExtractionMethods', () => {
  it('无参数调用返回全部 5 个方法（向后兼容旧接口）', () => {
    expect(getExtractionMethods()).toHaveLength(5);
  });
});

describe('getUploadEndpointByMethod', () => {
  it('fast → /api/v1/files/upload', () => {
    expect(getUploadEndpointByMethod('fast')).toBe('/api/v1/files/upload');
  });

  it('mineru → /api/v2/files/upload', () => {
    expect(getUploadEndpointByMethod('mineru')).toBe('/api/v2/files/upload');
  });

  it('未知方法返回默认 v1 端点', () => {
    expect(getUploadEndpointByMethod('unknown')).toBe('/api/v1/files/upload');
  });
});

describe('getDefaultExtractionMethod', () => {
  it('无参数返回 fast', () => {
    expect(getDefaultExtractionMethod()).toBe('fast');
  });
});

describe('getChunkMethods', () => {
  it('无参数返回全部 4 个分块方法', () => {
    const methods = getChunkMethods();
    expect(methods).toHaveLength(4);
    expect(methods).toContain('header_recursive');
    expect(methods).toContain('markdown_only');
    expect(methods).toContain('ocr_aware');
    expect(methods).toContain('layout_based');
  });
});
