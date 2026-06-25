/**
 * Notion风格徽章组件
 * 轻量级标签，用于状态显示
 */

import React from 'react';
import '../styles/notion.css';

const BadgeNotion = ({
  children,
  variant = 'default',  // default, primary, success, warning, error
  className = '',
  ...props
}) => {
  const baseClasses = 'badge-notion';
  
  const variantClasses = {
    default: '',
    primary: 'badge-notion-primary',
    success: 'badge-notion-success',
    warning: 'badge-notion-warning',
    error: 'badge-notion-error',
  }[variant];

  return (
    <span className={`${baseClasses} ${variantClasses} ${className}`} {...props}>
      {children}
    </span>
  );
};

export default BadgeNotion;