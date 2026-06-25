/**
 * Notion风格按钮组件
 * 提供多种按钮变体：primary, secondary, ghost, pill
 */

import React from 'react';
import '../styles/notion.css';

const ButtonNotion = ({
  children,
  variant = 'primary', // primary, secondary, ghost, pill
  size = 'md',      // sm, md, lg
  disabled = false,
  onClick,
  className = '',
  type = 'button',
  loading = false,
  ...props
}) => {
  const baseClasses = 'btn-notion';
  
  // 变体类
  const variantClasses = {
    primary: 'btn-notion-primary',
    secondary: 'btn-notion-secondary',
    ghost: 'btn-notion-ghost',
    pill: 'btn-notion-pill',
  }[variant];

  // 尺寸类
  const sizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  }[size];

  const handleClick = (e) => {
    if (!disabled && !loading && onClick) {
      onClick(e);
    }
  };

  return (
    <button
      type={type}
      className={`${baseClasses} ${variantClasses} ${sizeClasses} ${className}`.trim()}
      disabled={disabled || loading}
      onClick={handleClick}
      {...props}
    >
      {loading ? (
        <span className="loading-spinner" />
      ) : (
        children
      )}
    </button>
  );
};

export default ButtonNotion;