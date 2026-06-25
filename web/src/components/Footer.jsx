import { useState } from 'react'

function Footer() {
  const [showContactModal, setShowContactModal] = useState(false)

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handlePageClick = (page) => {
    alert(`即将跳转到：${page}\n\n（演示模式，实际需要创建完整页面）`)
  }

  return (
    <>
      <footer className="footer">
        <div className="footer-content">
          <div className="footer-grid">
            {/* 品牌信息 */}
            <div className="footer-brand">
              <div className="footer-logo">
                <span className="footer-logo-icon">🚀</span>
                <span className="footer-logo-text">MediaPilot</span>
              </div>
              <p className="footer-desc">
                在AI的时代里，营销自己成为了最重要的能力。
              </p>
              <div className="footer-social">
                <a href="#" className="social-icon" title="微信">💬</a>
                <a href="#" className="social-icon" title="微博">📱</a>
                <a href="#" className="social-icon" title="抖音">🎵</a>
                <a href="#" className="social-icon" title="GitHub">💻</a>
              </div>
            </div>

            {/* 产品 */}
            <div className="footer-section">
              <h4 className="footer-title">产品</h4>
              <ul className="footer-links">
                <li><a href="#" onClick={(e) => { e.preventDefault(); handlePageClick('功能介绍') }}>功能介绍</a></li>
                <li><a href="#" onClick={(e) => { e.preventDefault(); handlePageClick('更新日志') }}>更新日志</a></li>
                <li><a href="#" onClick={(e) => { e.preventDefault(); handlePageClick('定价方案') }}>定价方案</a></li>
                <li><a href="#" onClick={(e) => { e.preventDefault(); handlePageClick('API文档') }}>API文档</a></li>
              </ul>
            </div>

            {/* 资源 */}
            <div className="footer-section">
              <h4 className="footer-title">资源</h4>
              <ul className="footer-links">
                <li><a href="#" onClick={(e) => { e.preventDefault(); handlePageClick('帮助中心') }}>帮助中心</a></li>
                <li><a href="#" onClick={(e) => { e.preventDefault(); handlePageClick('使用教程') }}>使用教程</a></li>
                <li><a href="#" onClick={(e) => { e.preventDefault(); handlePageClick('案例展示') }}>案例展示</a></li>
                <li><a href="#" onClick={(e) => { e.preventDefault(); handlePageClick('合作伙伴') }}>合作伙伴</a></li>
              </ul>
            </div>

            {/* 公司 */}
            <div className="footer-section">
              <h4 className="footer-title">公司</h4>
              <ul className="footer-links">
                <li><a href="#" onClick={(e) => { e.preventDefault(); handlePageClick('关于我们') }}>关于我们</a></li>
                <li><a href="#" onClick={(e) => { e.preventDefault(); handlePageClick('新闻动态') }}>新闻动态</a></li>
                <li><a href="#" onClick={(e) => { e.preventDefault(); handlePageClick('加入我们') }}>加入我们</a></li>
                <li><a href="#" onClick={(e) => { e.preventDefault(); setShowContactModal(true) }}>联系我们</a></li>
              </ul>
            </div>

            {/* 法律 */}
            <div className="footer-section">
              <h4 className="footer-title">法律</h4>
              <ul className="footer-links">
                <li><a href="#" onClick={(e) => { e.preventDefault(); handlePageClick('用户协议') }}>用户协议</a></li>
                <li><a href="#" onClick={(e) => { e.preventDefault(); handlePageClick('隐私政策') }}>隐私政策</a></li>
                <li><a href="#" onClick={(e) => { e.preventDefault(); handlePageClick('服务条款') }}>服务条款</a></li>
                <li><a href="#" onClick={(e) => { e.preventDefault(); handlePageClick('Cookie政策') }}>Cookie政策</a></li>
              </ul>
            </div>
          </div>

          <div className="footer-bottom">
            <div className="footer-bottom-left">
              <p>© 2026 MediaPilot. All rights reserved.</p>
            </div>
            <div className="footer-bottom-right">
              <button onClick={scrollToTop} className="back-to-top" title="回到顶部">
                ↑ 回到顶部
              </button>
            </div>
          </div>
        </div>
      </footer>

      {/* 联系我们弹窗 */}
      {showContactModal && (
        <div className="modal-overlay" onClick={() => setShowContactModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>📬 联系我们</h3>
              <button onClick={() => setShowContactModal(false)} className="modal-close">✕</button>
            </div>
            <div className="modal-body">
              <div className="contact-info">
                <div className="contact-item">
                  <span className="contact-icon">📧</span>
                  <div>
                    <p className="contact-label">邮箱</p>
                    <p className="contact-value">contact@mediapilot.com</p>
                  </div>
                </div>
                <div className="contact-item">
                  <span className="contact-icon">💬</span>
                  <div>
                    <p className="contact-label">官方客服</p>
                    <p className="contact-value">微信：MediaPilot_Support</p>
                  </div>
                </div>
                <div className="contact-item">
                  <span className="contact-icon">📱</span>
                  <div>
                    <p className="contact-label">电话</p>
                    <p className="contact-value">400-888-8888</p>
                  </div>
                </div>
                <div className="contact-item">
                  <span className="contact-icon">📍</span>
                  <div>
                    <p className="contact-label">地址</p>
                    <p className="contact-value">北京市朝阳区科技园区</p>
                  </div>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button onClick={() => setShowContactModal(false)} className="btn btn-primary">
                知道了
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default Footer
