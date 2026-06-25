/**
 * 内容库页面
 */
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useContentLibrary } from '../../hooks/use-content-library'
import ContentCard from '../../components/content/ContentCard'
import ContentDetailModal from '../../components/content/ContentDetailModal'

function ContentLibraryPage() {
  const {
    contents,
    total,
    stats,
    loading,
    error,
    setError,
    fetchContents,
    fetchContentDetail,
    fetchRelatedContents,
    deleteContent,
    fetchStats,
    contentTypes
  } = useContentLibrary()

  const [viewMode, setViewMode] = useState('grid') // 'grid' or 'list'
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(12)
  const [selectedContent, setSelectedContent] = useState(null)
  const [relatedContents, setRelatedContents] = useState([])
  const [showDetailModal, setShowDetailModal] = useState(false)
  const [copySuccess, setCopySuccess] = useState(false)

  // 筛选条件
  const [filters, setFilters] = useState({
    content_type: '',
    topic: '',
    start_date: '',
    end_date: '',
    search: ''
  })

  // 加载数据
  useEffect(() => {
    fetchContents(filters, currentPage, pageSize)
    fetchStats()
  }, [])

  // 应用筛选
  const handleApplyFilters = () => {
    setCurrentPage(1)
    fetchContents(filters, 1, pageSize)
  }

  // 重置筛选
  const handleResetFilters = () => {
    const resetFilters = {
      content_type: '',
      topic: '',
      start_date: '',
      end_date: '',
      search: ''
    }
    setFilters(resetFilters)
    setCurrentPage(1)
    fetchContents(resetFilters, 1, pageSize)
  }

  // 搜索
  const handleSearch = (e) => {
    e.preventDefault()
    handleApplyFilters()
  }

  // 查看详情
  const handleViewDetail = async (contentId) => {
    const detail = await fetchContentDetail(contentId)
    if (detail) {
      setSelectedContent(detail)
      setShowDetailModal(true)

      // 获取关联内容
      const related = await fetchRelatedContents(contentId)
      setRelatedContents(related)
    }
  }

  // 复制成功提示
  const handleCopySuccess = (success) => {
    setCopySuccess(success)
    if (success) {
      setTimeout(() => setCopySuccess(false), 2000)
    }
  }

  // 删除内容
  const handleDelete = async (contentId) => {
    if (!confirm('确定要删除这条内容吗？')) return
    const success = await deleteContent(contentId)
    if (success) {
      fetchContents(filters, currentPage, pageSize)
      fetchStats()
    }
  }

  // 分页处理
  const totalPages = Math.ceil(total / pageSize)

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* 页面标题 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            内容库
          </h1>
          <p className="text-gray-600">
            管理您创作的内容，追踪话题关联
          </p>
        </div>

        {/* 统计卡片 */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-white rounded-xl p-4 shadow">
            <div className="text-2xl font-bold text-purple-600">{stats.total || 0}</div>
            <div className="text-sm text-gray-600">全部内容</div>
          </div>
          <div className="bg-white rounded-xl p-4 shadow">
            <div className="text-2xl font-bold text-blue-600">{stats.scripts || 0}</div>
            <div className="text-sm text-gray-600">拍摄脚本</div>
          </div>
          <div className="bg-white rounded-xl p-4 shadow">
            <div className="text-2xl font-bold text-green-600">{stats.copywritings || 0}</div>
            <div className="text-sm text-gray-600">口播文案</div>
          </div>
          <div className="bg-white rounded-xl p-4 shadow">
            <div className="text-2xl font-bold text-orange-600">{stats.videos || 0}</div>
            <div className="text-sm text-gray-600">视频</div>
          </div>
          <div className="bg-white rounded-xl p-4 shadow">
            <div className="text-2xl font-bold text-pink-600">{stats.audios || 0}</div>
            <div className="text-sm text-gray-600">音频</div>
          </div>
        </div>

        {/* 筛选工具栏 */}
        <div className="bg-white rounded-xl shadow p-4 mb-6">
          <form onSubmit={handleSearch}>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              {/* 搜索框 */}
              <div className="md:col-span-2">
                <div className="relative">
                  <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">🔍</span>
                  <input
                    type="text"
                    value={filters.search}
                    onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                    placeholder="搜索内容..."
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>
              </div>

              {/* 内容类型筛选 */}
              <div>
                <select
                  value={filters.content_type}
                  onChange={(e) => setFilters({ ...filters, content_type: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  {contentTypes.map((type) => (
                    <option key={type.id} value={type.id}>{type.name}</option>
                  ))}
                </select>
              </div>

              {/* 开始日期 */}
              <div>
                <input
                  type="date"
                  value={filters.start_date}
                  onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>

              {/* 结束日期 */}
              <div>
                <input
                  type="date"
                  value={filters.end_date}
                  onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="flex items-center justify-between mt-4">
              <div className="flex items-center gap-2">
                <button
                  type="submit"
                  className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                >
                  🔍 搜索
                </button>
                <button
                  type="button"
                  onClick={handleResetFilters}
                  className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  重置
                </button>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => fetchContents(filters, currentPage, pageSize)}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  title="刷新"
                >
                  {loading ? '🔄' : '🔄'}
                </button>

                <div className="flex items-center gap-1 border-l pl-2">
                  <button
                    type="button"
                    onClick={() => setViewMode('grid')}
                    className={`p-2 rounded-lg transition-colors ${viewMode === 'grid' ? 'bg-purple-100 text-purple-600' : 'hover:bg-gray-100'}`}
                  >
                    🔲
                  </button>
                  <button
                    type="button"
                    onClick={() => setViewMode('list')}
                    className={`p-2 rounded-lg transition-colors ${viewMode === 'list' ? 'bg-purple-100 text-purple-600' : 'hover:bg-gray-100'}`}
                  >
                    📋
                  </button>
                </div>
              </div>
            </div>
          </form>
        </div>

        {/* 内容列表 */}
        <div className="mb-4">
          {total > 0 && (
            <p className="text-gray-600">
              共 {total} 条内容
            </p>
          )}
        </div>

        {contents.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-xl shadow">
            <p className="text-gray-500">暂无内容</p>
          </div>
        ) : (
          <div className={`grid gap-4 ${viewMode === 'grid' ? 'md:grid-cols-3 lg:grid-cols-4' : 'grid-cols-1'}`}>
            {contents.map((content, idx) => (
              <motion.div
                key={content.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                onClick={() => handleViewDetail(content.id)}
              >
                <ContentCard
                  content={content}
                  onViewDetail={handleViewDetail}
                  onDelete={handleDelete}
                />
              </motion.div>
            ))}
          </div>
        )}

        {/* 分页 */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 mt-6">
            <button
              onClick={() => {
                if (currentPage > 1) {
                  setCurrentPage(currentPage - 1)
                  fetchContents(filters, currentPage - 1, pageSize)
                }
              }}
              disabled={currentPage === 1}
              className="px-4 py-2 bg-white rounded-lg shadow hover:shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              上一页
            </button>

            <div className="flex items-center gap-1">
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => {
                if (page === 1 || page === totalPages || (page >= currentPage - 1 && page <= currentPage + 1)) {
                  return (
                    <button
                      key={page}
                      onClick={() => {
                        setCurrentPage(page)
                        fetchContents(filters, page, pageSize)
                      }}
                      className={`px-4 py-2 rounded-lg transition-all ${
                        page === currentPage
                          ? 'bg-purple-600 text-white shadow'
                          : 'bg-white hover:shadow-md'
                      }`}
                    >
                      {page}
                    </button>
                  )
                }
                if (page === currentPage - 2 || page === currentPage + 2) {
                  return <span key={page} className="px-2">...</span>
                }
                return null
              })}
            </div>

            <button
              onClick={() => {
                if (currentPage < totalPages) {
                  setCurrentPage(currentPage + 1)
                  fetchContents(filters, currentPage + 1, pageSize)
                }
              }}
              disabled={currentPage === totalPages}
              className="px-4 py-2 bg-white rounded-lg shadow hover:shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              下一页
            </button>
          </div>
        )}

        {/* 错误提示 */}
        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-600">{error}</p>
          </div>
        )}

        {/* 复制成功提示 */}
        {copySuccess && (
          <div className="fixed bottom-6 right-6 flex items-center gap-2 px-4 py-3 bg-green-600 text-white rounded-lg shadow-lg">
            ✅ 复制成功
          </div>
        )}

        {/* 详情弹窗 */}
        {showDetailModal && (
          <ContentDetailModal
            content={selectedContent}
            relatedContents={relatedContents}
            onClose={() => {
              setShowDetailModal(false)
              setSelectedContent(null)
              setRelatedContents([])
            }}
            onCopy={handleCopySuccess}
          />
        )}
      </div>
    </div>
  )
}

export default ContentLibraryPage