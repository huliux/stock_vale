import { marked } from 'marked';
import DOMPurify from 'dompurify';

/**
 * 将Markdown文本渲染为HTML
 * @param text Markdown文本
 * @returns 安全的HTML字符串
 */
export function renderMarkdown(text: string): string {
  if (!text) return '';
  
  // 使用marked将Markdown转换为HTML
  const html = marked(text);
  
  // 使用DOMPurify清理HTML，防止XSS攻击
  return DOMPurify.sanitize(html);
}
