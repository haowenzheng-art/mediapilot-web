from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class HotTopic(Base):
    """热点话题模型"""
    __tablename__ = 'hot_topics'

    id = Column(String, primary_key=True)
    title = Column(String(200), nullable=False)
    summary = Column(Text, nullable=True)
    source = Column(String(50), nullable=False)  # 来源：百度热搜、微博热搜、知乎热榜等
    source_url = Column(String(500), nullable=True)  # 原文链接
    category = Column(String(50), nullable=True)  # 分类：科技、娱乐、生活、商业等
    heat_value = Column(Float, nullable=True)  # 热度值
    trend_direction = Column(String(10), nullable=True)  # 趋势：up/down/same
    published_at = Column(DateTime, nullable=True)  # 发布时间
    crawled_at = Column(DateTime, nullable=False)  # 爬取时间
    keywords = Column(Text, nullable=True)  # 相关关键词，JSON数组
    image_url = Column(String(500), nullable=True)  # 配图URL
    is_processed = Column(Integer, default=0)  # 是否已处理（生成文案）

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'summary': self.summary,
            'source': self.source,
            'sourceUrl': self.source_url,
            'category': self.category,
            'heatValue': self.heat_value,
            'trendDirection': self.trend_direction,
            'publishedAt': self.published_at.isoformat() if self.published_at else None,
            'crawledAt': self.crawled_at.isoformat() if self.crawled_at else None,
            'keywords': self.keywords,
            'imageUrl': self.image_url,
            'isProcessed': self.is_processed
        }


class HotTopicSubscription(Base):
    """热点订阅模型"""
    __tablename__ = 'hot_topic_subscriptions'

    id = Column(String, primary_key=True)
    name = Column(String(100), nullable=False)
    keywords = Column(Text, nullable=True)  # 搜索关键词，JSON数组
    update_frequency = Column(String(20), nullable=False)  # daily/every3days
    last_updated_at = Column(DateTime, nullable=True)
    is_active = Column(Integer, default=1)
    user_id = Column(String, nullable=False)  # 关联用户


class HotTopicPush(Base):
    """热点推送记录模型"""
    __tablename__ = 'hot_topic_pushes'

    id = Column(String, primary_key=True)
    subscription_id = Column(String, nullable=False)  # 关联订阅ID
    hot_topic_id = Column(String, nullable=False)  # 关联热点ID
    pushed_at = Column(DateTime, nullable=False)
    is_read = Column(Integer, default=0)
