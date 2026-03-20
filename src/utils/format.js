// AI输出格式化工具 - 增强版
export function formatAIOutput(text) {
  if (!text) return text

  let formatted = text

  // 0. 先清理乱码（比如用户例子中的乱码字符）
  formatted = formatted.replace(/[�]/g, '')

  // 1. 在标题前后加换行
  formatted = formatted.replace(/(^|\n)(#{1,6}\s+.+?)(\n)(?!\n)/g, '$1$2\n$3')

  // 2. 处理"---"分隔符，前后加空行
  formatted = formatted.replace(/(^|\n)-{3,}(\n)/g, '$1\n---\n$2')

  // 3. 处理数字列表（1. 2. 3.）- 确保每个列表项后有换行
  formatted = formatted.replace(/(^|\n)(\d+[.、]\s*.+?)(?=\n\d+[.、]|\n---|\n##|\n$)/g, '$1$2\n')

  // 4. 处理带*的列表项
  formatted = formatted.replace(/(^|\n)(\*\s*.+?)(?=\n\*|\n---|\n##|\n$)/g, '$1$2\n')

  // 5. 处理emoji标题（🔥 📊 💡 ✍️）
  formatted = formatted.replace(/(^|\n)([🔥📊💡✍️📋🎣📖🎓🎙️⭐🎬👑🎯📈]+)(\s*.+?)(?=\n[🔥📊💡✍️📋🎣📖🎓🎙️⭐🎬👑🎯📈]|\n---|\n##|\n$)/g, '$1$2 $3\n\n')

  // 6. 处理"#### 选题"这样的标题
  formatted = formatted.replace(/(^|\n)(#{4,}\s*.+?)(\n)/g, '$1$2\n$3')

  // 7. 清理多余的空行（最多2个）
  formatted = formatted.replace(/\n{4,}/g, '\n\n\n')

  // 8. 确保标点符号后有适当的空格
  formatted = formatted.replace(/([，。！？；：])([^\s\n])/g, '$1 $2')

  // 9. 处理"选题 1："这种格式
  formatted = formatted.replace(/(选题\s*\d+[：:])/g, '\n$1 ')

  // 10. 处理"文案范例："这种格式
  formatted = formatted.replace(/(文案范例[：:])/g, '\n$1\n')

  // 11. 处理"> "这种引用格式，确保前后有空行
  formatted = formatted.replace(/(^|\n)(>\s*.+?)(\n)(?!>)/g, '$1$2\n$3')

  // 12. 处理括号内的内容，比如"（如保证4%-5%的利息）"
  formatted = formatted.replace(/（([^）]+)）/g, '（$1）')

  return formatted.trim()
}

// 更智能的格式化 - 专门处理用户例子中的情况
export function intelligentFormat(text) {
  if (!text) return text

  let formatted = text

  // 步骤1: 清理乱码
  formatted = formatted.replace(/[^\S\r\n]*[�]+[^\S\r\n]*/g, ' ')

  // 步骤2: 在每个主要部分之间加空行
  // 识别"热点概述"、"趋势分析"、"选题建议"、"文案模板"这些部分
  const sectionHeaders = ['热点概述', '趋势分析', '选题建议', '文案模板', '核心逻辑']
  sectionHeaders.forEach(header => {
    const regex = new RegExp(`(${header})`, 'g')
    formatted = formatted.replace(regex, '\n\n$1')
  })

  // 步骤3: 处理数字列表 - 在"1."、"2."等前面加换行
  formatted = formatted.replace(/(\D)(\d+[.、])/g, '$1\n$2')

  // 步骤4: 处理"选题 1"、"选题 2"
  formatted = formatted.replace(/(选题\s*\d+)/g, '\n$1')

  // 步骤5: 处理"---"分隔符，前后加空行
  formatted = formatted.replace(/(\n?)-{3,}(\n?)/g, '\n\n---\n\n')

  // 步骤6: 清理多余的空行
  formatted = formatted.replace(/\n{4,}/g, '\n\n\n')

  // 步骤7: 确保标题后面有空格
  formatted = formatted.replace(/(^|\n)(#{1,6})([^\s#])/g, '$1$2 $3')

  // 步骤8: 处理emoji后面加空格
  formatted = formatted.replace(/([🔥📊💡✍️📋🎣📖🎓🎙️⭐🎬👑🎯📈📝🎯💬📱📍]+)([^\s])/g, '$1 $2')

  return formatted.trim()
}

// 最简单的格式化 - 保证基本可读性
export function simpleFormat(text) {
  if (!text) return text

  let formatted = text

  // 1. 清理乱码
  formatted = formatted.replace(/[�]/g, '')

  // 2. 在数字列表前加换行
  formatted = formatted.replace(/([^\d\n])(\d+[.、])/g, '$1\n$2')

  // 3. 在emoji后加空格
  formatted = formatted.replace(/([🔥📊💡✍️📋🎣📖🎓🎙️⭐🎬👑🎯📈]+)([^\s])/g, '$1 $2')

  // 4. 确保标题后有空格
  formatted = formatted.replace(/(^|\n)(#{1,6})([^\s#])/g, '$1$2 $3')

  // 5. 清理多余空行
  formatted = formatted.replace(/\n{3,}/g, '\n\n')

  return formatted
}
