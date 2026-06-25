/**
 * Notion风格卡片组件
 * 带有whisper边框和多层阴影
 */

import React from 'react';
import '../styles/notion.css';

const CardNotion = ({
  children,
  className = '',
  size = 'md',  // md, xl
  hoverable = false,
  onClick,
  ...props
}) => {
  const baseClasses = 'card-notion';
  
  const sizeClasses = {
    md: '',
    xl: 'card-notion-xl',
  }[size];

  const hoverClasses = hoverable ? 'cursor-pointer' : '';
  const classes = `${baseClasses} ${sizeClasses} ${hoverClasses} ${className}`.trim();

  const handleClick = (e) => {
    if (hoverable && onClick) {
      onClick(e);
    }
  };

  return (
    <div className={classes} onClick={handleClick} {...props}>
      {children}
    </div>
  );
};

// 卡片标题子组件
export const CardNotionTitle = ({ children, className = '' }) => (
  <h3 className={`text-lg font-semibold mb-3 text-notion-primary ${className}`}>
    {children}
  </h3>
);

// 卡片内容子组件
export const CardNotionBody = ({ children, className = '' }) => (
  <div className={`text-notion-secondary ${className}`}>
    {children}
  </div>
);

export default CardNotion;