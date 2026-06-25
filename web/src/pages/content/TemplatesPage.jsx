import { useTemplates } from '../../hooks/use-templates'

function TemplatesPage() {
  const {
    selectedCategory, setSelectedCategory,
    customTopic, setCustomTopic,
    generatedTemplate, selectedTemplate,
    isGenerating,
    useTemplate, generateCustomTemplate, copyTemplate,
    aiEnabled, filteredTemplates, categories,
  } = useTemplates()

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <span>📋</span> AI模板
      </h2>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* 左侧 - 模板选择 */}
        <div className="lg:col-span-2 space-y-6">
          {/* 分类标签 */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2"><span>📂</span> 模板分类</h3>
            <div className="flex flex-wrap gap-2">
              {categories.map(cat => (
                <button key={cat.id} onClick={() => setSelectedCategory(cat.id)}
                  className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-all ${selectedCategory === cat.id ? 'bg-primary text-white' : 'bg-bg-light hover:bg-bg-light/80'}`}>
                  <span>{cat.icon}</span><span>{cat.name}</span>
                </button>
              ))}
            </div>
          </div>

          {/* 模板列表 */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2"><span>📝</span> 预设模板</h3>
            <div className="grid md:grid-cols-2 gap-4">
              {filteredTemplates.map(template => (
                <div key={template.id}
                  className={`p-4 rounded-lg border border-border cursor-pointer transition-all hover:border-primary ${selectedTemplate?.id === template.id ? 'border-primary bg-primary/5' : ''}`}
                  onClick={() => useTemplate(template)}>
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-semibold">{template.name}</h4>
                      <p className="text-sm text-secondary mt-1">{template.description}</p>
                    </div>
                    <button onClick={(e) => { e.stopPropagation(); useTemplate(template) }} className="btn btn-primary text-sm px-3 py-1.5">使用</button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 自定义模板生成 */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2"><span>✨</span> 生成自定义模板</h3>
            <p className="text-secondary text-sm mb-4">输入你的主题，AI为你生成专属模板</p>
            <div className="flex gap-4">
              <input type="text" placeholder="例如：产品测评、知识科普、情感励志..." value={customTopic}
                onChange={(e) => setCustomTopic(e.target.value)}
                className="flex-1 px-4 py-3 bg-bg-light border border-border rounded-lg focus:outline-none focus:border-primary" disabled={isGenerating} />
              {aiEnabled ? (
                <button onClick={generateCustomTemplate} disabled={isGenerating || !customTopic.trim()} className="btn btn-primary whitespace-nowrap">
                  {isGenerating ? <span className="animate-pulse">生成中...</span> : '生成模板'}
                </button>
              ) : (
                <div className="px-4 py-3 bg-yellow-500/20 border border-yellow-500/30 rounded-lg text-center">
                  <p className="text-yellow-400 text-sm">🔧 AI 暂未开放</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 右侧 - 模板预览 */}
        <div className="space-y-6">
          <div className="card sticky top-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold flex items-center gap-2"><span>👁️</span> 模板预览</h3>
              {generatedTemplate && (
                <button onClick={copyTemplate} className="btn btn-secondary text-sm px-3 py-1.5">📋 复制</button>
              )}
            </div>
            {generatedTemplate ? (
              <div className="p-4 bg-bg-light rounded-lg border border-border">
                <pre className="whitespace-pre-wrap text-sm leading-relaxed font-mono">{generatedTemplate}</pre>
              </div>
            ) : (
              <div className="text-center py-12 text-secondary">
                <p className="text-4xl mb-4">📝</p>
                <p>选择一个模板或生成新模板</p>
                <p className="text-sm mt-2">模板将在这里显示</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default TemplatesPage
