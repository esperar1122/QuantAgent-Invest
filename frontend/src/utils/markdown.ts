import { marked } from 'marked'
import DOMPurify from 'dompurify'

/**
 * 安全渲染 Markdown 文本为 HTML
 * 统一集成 marked 解析与 DOMPurify XSS 净化，防止恶意脚本注入
 */
export function renderMarkdown(content: string | undefined | null): string {
  if (!content) return ''
  try {
    const rawHtml = String(marked.parse(content))
    return DOMPurify.sanitize(rawHtml, {
      ADD_ATTR: ['target', 'rel'],
      USE_PROFILES: { html: true }
    })
  } catch (err) {
    console.error('Markdown 渲染异常:', err)
    return `<pre style="white-space: pre-wrap; font-family: inherit;">${DOMPurify.sanitize(content)}</pre>`
  }
}

export default renderMarkdown
