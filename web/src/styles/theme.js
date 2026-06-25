// MediaPilot Notion风格主题配置
// 基于 Notion 设计系统：温暖极简、内容友好

export const notionTheme = {
  // ==================== 颜色系统 ====================
  colors: {
    // 主要颜色
    bg: '#ffffff',                    // 纯白背景
    bgAlt: '#f6f5f4',               // 温暖白背景（交替使用）
    text: 'rgba(0,0,0,0.95)',       // 近黑文字（95%不透明度，微暖）
    textSecondary: '#615d59',         // 次要文字（温暖灰）
    textMuted: '#a39e98',            // 暗淡文字（占位符、禁用状态）
    
    // 品牌色 - Notion Blue是唯一饱和色
    primary: '#0075de',               // Notion Blue（主CTA、链接）
    primaryHover: '#005bab',          // 按钮悬停/激活状态
    primaryActive: '#004a8f',         // 按钮按下状态
    primaryLight: '#f2f9ff',          // 徽章背景（浅蓝）
    primaryText: '#097fe8',           // 徽章文字（深蓝）
    focus: '#097fe8',                // 键盘焦点圈颜色
    
    // 语义色
    success: '#1aae39',              // 绿色（成功、完成）
    warning: '#dd5b00',              // 橙色（警告、注意）
    error: '#dc2626',                // 红色（错误、失败）
    info: '#2a9d99',                // 青色（信息、提示）
    
    // 边框和阴影
    border: 'rgba(0,0,0,0.1)',      // 超细边框（whisper border）
    divider: 'rgba(0,0,0,0.1)',     // 分隔线
    placeholder: 'rgba(163,158,152,0.8)', // 输入框占位符
    
    // 阴影（多层叠加）
    shadowCard: 'rgba(0,0,0,0.04) 0px 4px 18px, rgba(0,0,0,0.027) 0px 2.025px 7.85px, rgba(0,0,0,0.02) 0px 0.8px 2.93px, rgba(0,0,0,0.01) 0px 0.175px 1.04px',
    shadowDeep: 'rgba(0,0,0,0.01) 0px 1px 3px, rgba(0,0,0,0.02) 0px 3px 7px, rgba(0,0,0,0.02) 0px 7px 15px, rgba(0,0,0,0.04) 0px 14px 28px, rgba(0,0,0,0.05) 0px 23px 52px',
    shadowHover: 'rgba(0,0,0,0.06) 0px 6px 20px, rgba(0,0,0,0.04) 0px 3px 10px',
  },

  // ==================== 圆角系统 ====================
  borderRadius: {
    xs: '4px',       // 微小（按钮、输入框）
    sm: '5px',       // 小（链接、列表项）
    md: '8px',       // 中等（小卡片）
    lg: '12px',      // 大（标准卡片）
    xl: '16px',      // 超大（特色卡片、hero）
    pill: '9999px',  // 全药丸（徽章、状态标签）
    circle: '50%',   // 圆形（头像、指示器）
  },

  // ==================== 字体系统 ====================
  fontFamily: {
    // Inter字体系列（替代NotionInter）
    primary: "'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
    mono: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace",
  },

  fontSize: {
    // Notion字重：400(正文) / 500(UI) / 600(强调) / 700(标题)
    // 显示字体的负字间距随大小变化
    display: {
      hero: {
        size: '64px',
        weight: 700,
        lineHeight: 1.00,
        letterSpacing: '-2.125px', // 显示字体压缩
      },
      secondary: {
        size: '54px',
        weight: 700,
        lineHeight: 1.04,
        letterSpacing: '-1.875px',
      },
      section: {
        size: '48px',
        weight: 700,
        lineHeight: 1.00,
        letterSpacing: '-1.5px',
      },
    },
    subHeading: {
      large: {
        size: '40px',
        weight: 700,
        lineHeight: 1.50,
        letterSpacing: 'normal',
      },
      normal: {
        size: '26px',
        weight: 700,
        lineHeight: 1.23,
        letterSpacing: '-0.625px',
      },
    },
    cardTitle: {
      size: '22px',
      weight: 700,
      lineHeight: 1.27,
      letterSpacing: '-0.25px',
    },
    body: {
      large: {
        size: '20px',
        weight: 600,
        lineHeight: 1.40,
        letterSpacing: '-0.125px',
      },
      normal: {
        size: '16px',
        weight: 400,
        lineHeight: 1.50,
        letterSpacing: 'normal',
      },
      medium: {
        size: '16px',
        weight: 500,
        lineHeight: 1.50,
        letterSpacing: 'normal',
      },
      semibold: {
        size: '16px',
        weight: 600,
        lineHeight: 1.50,
        letterSpacing: 'normal',
      },
      bold: {
        size: '16px',
        weight: 700,
        lineHeight: 1.50,
        letterSpacing: 'normal',
      },
    },
    navButton: {
      size: '15px',
      weight: 600,
      lineHeight: 1.33,
      letterSpacing: 'normal',
    },
    caption: {
      size: '14px',
      weight: 500,
      lineHeight: 1.43,
      letterSpacing: 'normal',
    },
    captionLight: {
      size: '14px',
      weight: 400,
      lineHeight: 1.43,
      letterSpacing: 'normal',
    },
    badge: {
      size: '12px',
      weight: 600,
      lineHeight: 1.33,
      letterSpacing: '0.125px', // 徽章正字间距（唯一的）
    },
    micro: {
      size: '12px',
      weight: 400,
      lineHeight: 1.33,
      letterSpacing: '0.125px',
    },
  },

  // ==================== 间距系统 ====================
  spacing: {
    // 基本单位：8px
    xs: '4px',
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '24px',
    '2xl': '32px',
    '3xl': '48px',
    '4xl': '64px',
    '5xl': '80px',
    '6xl': '120px',
  },

  // ==================== 过渡和动画 ====================
  transitions: {
    fast: '150ms ease-in-out',
    normal: '200ms ease-in-out',
    slow: '300ms ease-in-out',
  },

  // ==================== 交互状态 ====================
  interactions: {
    hover: 'scale-105',        // 悬停时放大
    active: 'scale-95',        // 按下时缩小
    focus: 'outline-2 outline-blue-500 outline-offset-2', // 焦点圈
  },

  // ==================== Z-index层级 ====================
  zIndex: {
    dropdown: 1000,
    modal: 1100,
    toast: 1200,
  },
};

// Tailwind自定义配置映射
export const tailwindConfig = {
  theme: {
    extend: {
      colors: {
        notion: {
          bg: notionTheme.colors.bg,
          bgAlt: notionTheme.colors.bgAlt,
          text: notionTheme.colors.text,
          textSecondary: notionTheme.colors.textSecondary,
          textMuted: notionTheme.colors.textMuted,
          primary: notionTheme.colors.primary,
          primaryHover: notionTheme.colors.primaryHover,
          primaryActive: notionTheme.colors.primaryActive,
          primaryLight: notionTheme.colors.primaryLight,
          primaryText: notionTheme.colors.primaryText,
          success: notionTheme.colors.success,
          warning: notionTheme.colors.warning,
          error: notionTheme.colors.error,
          info: notionTheme.colors.info,
          border: notionTheme.colors.border,
          placeholder: notionTheme.colors.placeholder,
        },
      },
      borderRadius: {
        notion: notionTheme.borderRadius.lg,
        pill: notionTheme.borderRadius.pill,
      },
      boxShadow: {
        notionCard: notionTheme.colors.shadowCard,
        notionDeep: notionTheme.colors.shadowDeep,
        notionHover: notionTheme.colors.shadowHover,
      },
      fontFamily: {
        sans: notionTheme.fontFamily.primary,
        mono: notionTheme.fontFamily.mono,
      },
      spacing: {
        notion: notionTheme.spacing.lg,
      },
    },
  },
};