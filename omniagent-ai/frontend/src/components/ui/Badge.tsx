/**
 * Badge Component - Status and Label Indicators
 * Professional styling with multiple variants
 */

import React, { HTMLAttributes } from 'react';

type BadgeVariant = 'default' | 'success' | 'error' | 'warning' | 'info' | 'processing';
type BadgeSize = 'sm' | 'md' | 'lg';

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: BadgeSize;
  icon?: React.ReactNode;
  dot?: boolean;
  children: React.ReactNode;
}

const variantClasses: Record<BadgeVariant, string> = {
  default: 'bg-slate-700/40 text-slate-200 border border-slate-600/60',
  success: 'bg-green-900/40 text-green-300 border border-green-800/60',
  error: 'bg-red-900/40 text-red-300 border border-red-800/60',
  warning: 'bg-yellow-900/40 text-yellow-300 border border-yellow-800/60',
  info: 'bg-blue-900/40 text-blue-300 border border-blue-800/60',
  processing: 'bg-purple-900/40 text-purple-300 border border-purple-800/60',
};

const sizeClasses: Record<BadgeSize, string> = {
  sm: 'px-2.5 py-1 text-xs',
  md: 'px-3 py-1.5 text-sm',
  lg: 'px-4 py-2 text-base',
};

const dotColorClasses: Record<BadgeVariant, string> = {
  default: 'bg-slate-400',
  success: 'bg-green-400',
  error: 'bg-red-400',
  warning: 'bg-yellow-400',
  info: 'bg-blue-400',
  processing: 'bg-purple-400',
};

const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  (
    {
      variant = 'default',
      size = 'md',
      icon,
      dot = false,
      className = '',
      children,
      ...props
    },
    ref
  ) => {
    return (
      <span
        ref={ref}
        className={`
          inline-flex items-center gap-2 rounded-full font-medium 
          transition duration-200 hover:shadow-md
          ${variantClasses[variant]}
          ${sizeClasses[size]}
          ${className}
        `}
        {...props}
      >
        {dot && (
          <span
            className={`inline-block w-2 h-2 rounded-full ${dotColorClasses[variant]}`}
            aria-hidden="true"
          />
        )}
        {icon && <span className="flex items-center">{icon}</span>}
        {children}
      </span>
    );
  }
);

Badge.displayName = 'Badge';

export default Badge;
