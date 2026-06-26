import { useState, useEffect } from 'react'
import { useContentLibrary } from '../../hooks/use-content-library'
import PageContainer from '../../components/common/PageContainer'
import ContentCard from '../../components/content/ContentCard'
import ContentDetailModal from '../../components/content/ContentDetailModal'

const inputStyle = {
  flex: 1,
  padding: '10px 14px',
  fontSize: '13px',
  border: '1px solid var(--border-color)',
  borderRadius: '8px',
  background: 'var(--bg-secondary)',
  color: 'var(--text-primary)',
  outline: 'none',
}

const btnPrimary = {
  padding: '10px 18px',
  background: 'var(--accent-primary)',
  color: 'var(--bg-primary)',
  border: 'none',
  borderRadius: '8px',
  fontSize: '13px',
  fontWeight: '500',
  cursor: 'pointer',
}

const btnGhost = {
  padding: '10px 14px',
  background: 'transparent',
  color: 'var(--text-secondary)',
  border: '1px solid var(--border-color)',
  borderRadius: '8px',
  fontSize: '13px',
  cursor: 'pointer',
}

const statCardStyle = {
  padding: '16px 20px',
  background: 'var(--card-bg)',
  borderRadius: '10px',
  border: '1px solid var(--border-color)',
}

function StatCard({ value, label }) {
  return (
    <div style={statCardStyle}>
      <div style={{ fontSize: '22px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '4px' }}>
        {value}
      </div>
      <div style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>{label}</div>
    </div>
  )
}

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

  const [currentPage, setCurrentPage] = useState(1)
  const pageSize = 12
  const [selectedContent, setSelectedContent] = useState(null)
  const [relatedContents, setRelatedContents] = useState([])
  const [showDetailModal, setShowDetailModal] = useState(false)
  const [copySuccess, setCopySuccess] = useState(false)

  const [filters, setFilters] = useState({
    content_type: '',
    topic: '',
    start_date: '',
    end_date: '',
    search: ''
  })

  useEffect(() => {
    fetchContents(filters, currentPage, pageSize)
    fetchStats()
  }, [])

  const handleApplyFilters = () => {
    setCurrentPage(1)
    fetchContents(filters, 1, pageSize)
  }

  const handleResetFilters = () => {
    const resetFilters = { content_type: '', topic: '', start_date: '', end_date: '', search: '' }
    setFilters(resetFilters)
    setCurrentPage(1)
    fetchContents(resetFilters, 1, pageSize)
  }

  const handleSearch = (e) => {
    e.preventDefault()
    handleApplyFilters()
  }

  const handleViewDetail = async (contentId) => {
    const detail = await fetchContentDetail(contentId)
    if (detail) {
      setSelectedContent(detail)
      setShowDetailModal(true)
      const related = await fetchRelatedContents(contentId)
      setRelatedContents(related)
    }
  }

  const handleCopySuccess = (success) => {
    setCopySuccess(success)
    if (success) setTimeout(() => setCopySuccess(false), 2000)
  }

  const handleDelete = async (contentId) => {
    if (!confirm('确定要删除这条内容吗？')) return
    const success = await deleteContent(contentId)
    if (success) {
      fetchContents(filters, currentPage, pageSize)
      fetchStats()
    }
  }

  const totalPages = Math.ceil(total / pageSize)
  const handlePageChange = (page) => {
    setCurrentPage(page)
    fetchContents(filters, page, pageSize)
  }

  return (
    <PageContainer
      title="内容库"
      description="管理您创作的内容，追踪话题关联"
    >
      {/* 统计卡片 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
        gap: '12px',
        marginBottom: '24px',
      }}>
        <StatCard value={stats.total || 0} label="全部内容" />
        <StatCard value={stats.scripts || 0} label="拍摄脚本" />
        <StatCard value={stats.copywritings || 0} label="口播文案" />
        <StatCard value={stats.videos || 0} label="视频" />
        <StatCard value={stats.audios || 0} label="音频" />
      </div>

      {/* 筛选工具栏 */}
      <div style={{
        padding: '20px',
        background: 'var(--card-bg)',
        borderRadius: '12px',
        border: '1px solid var(--border-color)',
        marginBottom: '20px',
      }}>
        <form onSubmit={handleSearch}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '12px',
          }}>
            <div style={{ position: 'relative' }}>
              <input
                type="text"
                value={filters.search}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                placeholder="搜索内容..."
                style={{ ...inputStyle, paddingLeft: '36px' }}
              />
              <span style={{
                position: 'absolute',
                left: '12px',
                top: '50%',
                transform: 'translateY(-50%)',
                fontSize: '13px',
                color: 'var(--text-tertiary)',
              }}>🔍</span>
            </div>

            <select
              value={filters.content_type}
              onChange={(e) => setFilters({ ...filters, content_type: e.target.value })}
              style={inputStyle}
            >
              {contentTypes.map((type) => (
                <option key={type.id} value={type.id}>{type.name}</option>
              ))}
            </select>

            <input
              type="date"
              value={filters.start_date}
              onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
              style={inputStyle}
            />
            <input
              type="date"
              value={filters.end_date}
              onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
              style={inputStyle}
            />
          </div>

          <div style={{
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '8px',
            marginTop: '14px',
          }}>
            <button type="submit" style={btnPrimary}>🔍 搜索</button>
            <button type="button" onClick={handleResetFilters} style={btnGhost}>重置</button>
            <button
              type="button"
              onClick={() => fetchContents(filters, currentPage, pageSize)}
              style={btnGhost}
              title="刷新"
            >
              {loading ? '⏳' : '🔄'}
            </button>
          </div>
        </form>
      </div>

      {/* 内容列表 */}
      {total > 0 && (
        <div style={{ marginBottom: '14px', fontSize: '13px', color: 'var(--text-tertiary)' }}>
          共 {total} 条内容
        </div>
      )}

      {contents.length === 0 ? (
        <div style={{
          padding: '60px 24px',
          textAlign: 'center',
          background: 'var(--card-bg)',
          borderRadius: '12px',
          border: '1px solid var(--border-color)',
          color: 'var(--text-tertiary)',
        }}>
          <div style={{ fontSize: '36px', marginBottom: '12px' }}>📭</div>
          <div style={{ fontSize: '14px' }}>暂无内容</div>
          <div style={{ fontSize: '12px', marginTop: '4px', color: 'var(--text-tertiary)' }}>
            生成口播文案或拍摄脚本后，内容会自动出现在这里
          </div>
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
          gap: '16px',
        }}>
          {contents.map((content) => (
            <ContentCard
              key={content.id}
              content={content}
              onViewDetail={handleViewDetail}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {/* 分页 */}
      {totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px', marginTop: '32px' }}>
          <button
            onClick={() => currentPage > 1 && handlePageChange(currentPage - 1)}
            disabled={currentPage === 1}
            style={{
              ...btnGhost,
              opacity: currentPage === 1 ? 0.4 : 1,
              cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
            }}
          >
            上一页
          </button>

          {Array.from({ length: totalPages }, (_, i) => i + 1)
            .filter((page) => page === 1 || page === totalPages || Math.abs(page - currentPage) <= 1)
            .map((page, idx, arr) => (
              <div key={page} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                {idx > 0 && arr[idx - 1] !== page - 1 && <span style={{ color: 'var(--text-tertiary)', padding: '0 4px' }}>…</span>}
                <button
                  onClick={() => handlePageChange(page)}
                  style={{
                    padding: '8px 14px',
                    background: page === currentPage ? 'var(--accent-primary)' : 'var(--card-bg)',
                    color: page === currentPage ? 'var(--bg-primary)' : 'var(--text-primary)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px',
                    fontSize: '13px',
                    cursor: 'pointer',
                    fontWeight: page === currentPage ? '600' : '400',
                  }}
                >
                  {page}
                </button>
              </div>
            ))}

          <button
            onClick={() => currentPage < totalPages && handlePageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            style={{
              ...btnGhost,
              opacity: currentPage === totalPages ? 0.4 : 1,
              cursor: currentPage === totalPages ? 'not-allowed' : 'pointer',
            }}
          >
            下一页
          </button>
        </div>
      )}

      {/* 错误提示 */}
      {error && (
        <div style={{
          marginTop: '16px',
          padding: '12px 16px',
          background: 'rgba(220, 38, 38, 0.05)',
          border: '1px solid rgba(220, 38, 38, 0.2)',
          borderRadius: '8px',
          color: '#dc2626',
          fontSize: '13px',
        }}>
          {error}
        </div>
      )}

      {/* 复制成功提示 */}
      {copySuccess && (
        <div style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          padding: '12px 18px',
          background: 'var(--accent-primary)',
          color: 'var(--bg-primary)',
          borderRadius: '8px',
          fontSize: '13px',
          fontWeight: '500',
          boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
          zIndex: 1000,
        }}>
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
    </PageContainer>
  )
}

export default ContentLibraryPage
