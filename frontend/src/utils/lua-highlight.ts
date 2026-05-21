import { LRLanguage, LanguageSupport } from '@codemirror/language'
import { styleTags, tags as t } from '@lezer/highlight'
import { parser } from 'lezer-lua'

// 创建Lua语言
const luaLanguage = LRLanguage.define({
  name: 'lua',
  parser: parser.configure({
    props: [
      styleTags({
        Identifier: t.variableName,
        String: t.string,
        Number: t.number,
        Comment: t.comment,
        Keyword: t.keyword,
        Function: t.variableName,
        Operator: t.operator,
        Property: t.propertyName,
        Nil: t.null,
        Boolean: t.bool,
      }),
    ],
  }),
})

// 导出Lua语言支持
export function lua() {
  return new LanguageSupport(luaLanguage)
}