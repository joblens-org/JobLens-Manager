type ExtractedNode = { prefix: string; num: number; rawNum: string }

/**
 * 将节点名称列表压缩为紧凑格式，便于运维定位节点
 *
 * 输入: ["lsw001", "lsw002", "lsw003", "lsw012", "lsw033", "lss001", "lss002"]
 * 输出: "lsw[001-003,012,033],lss[001,002]"
 *
 * 规则：
 * 1. 按前缀（字母/下划线/横线部分）分组
 * 2. 每组内按编号排序，连续编号合并为区间（如 001-003）
 * 3. 不连续的编号单独列出，保留原始数字格式（含前导零）
 */
export function compactNodeNames(names: string[]): string {
  if (!names.length) return ''

  const extracted: ExtractedNode[] = names.map((name) => {
    const m = name.match(/^(.+?)(\d+)$/)
    if (m) {
      return { prefix: m[1] ?? name, num: parseInt(m[2] ?? '0', 10), rawNum: m[2] ?? '' }
    }
    return { prefix: name, num: -1, rawNum: '' }
  })

  const groups = new Map<string, ExtractedNode[]>()
  for (const item of extracted) {
    const list = groups.get(item.prefix)
    if (list) {
      list.push(item)
    } else {
      groups.set(item.prefix, [item])
    }
  }

  const parts: string[] = []
  for (const [prefix, items] of groups) {
    items.sort((a, b) => a.num - b.num)

    if (items.length === 0) {
      parts.push(prefix)
      continue
    }
    if (items[0]!.num === -1) {
      parts.push(prefix)
      continue
    }

    const ranges: string[] = []
    const first = items[0]!
    let start = first
    let end = first

    for (let i = 1; i < items.length; i++) {
      const current = items[i]!
      if (current.num === end.num + 1) {
        end = current
      } else {
        ranges.push(start.num === end.num ? start.rawNum : `${start.rawNum}-${end.rawNum}`)
        start = current
        end = current
      }
    }
    ranges.push(start.num === end.num ? start.rawNum : `${start.rawNum}-${end.rawNum}`)

    parts.push(`${prefix}[${ranges.join(',')}]`)
  }

  return parts.join(',')
}
