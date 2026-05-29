/**
 * 统一的 fetch 错误处理工具
 * 宪法原则 II: No Silent Failures
 * 前端原则 VI: 所有 fetch() 必须检查 response.ok
 */

export async function safeFetch(url: string, options?: RequestInit): Promise<Response> {
  const response = await fetch(url, options);
  if (!response.ok) {
    const errorText = await response.text().catch(() => "无法获取错误详情");
    throw new Error(`API 错误 (${response.status}): ${errorText}`);
  }
  return response;
}

export async function safeFetchJSON<T = any>(url: string, options?: RequestInit): Promise<T> {
  const response = await safeFetch(url, options);
  return response.json();
}
