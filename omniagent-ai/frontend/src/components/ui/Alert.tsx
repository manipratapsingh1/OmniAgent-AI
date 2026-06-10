/**
 * Alert Component - User Feedback & Information
 * Professional styling with multiple severity levels
 */

import React, { HTMLAttributes } from 'react';

type AlertVariant = 'info' | 'success' | 'warning' | 'error';

interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  variant?: AlertVariant;
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  onClose?: () => void;
  closeable?: boolean;
  children?: React.ReactNode;
}

const variantClasses: Record<AlertVariant, { bg: string; border: string; text: string; icon: string }> = {
  info: {
    bg: 'bg-blue-900/20',
    border: 'border-blue-800/50',
    text: 'text-blue-200',
    icon: 'text-blue-400',
  },
  success: {
    bg: 'bg-green-900/20',
    border: 'border-green-800/50',
    text: 'text-green-200',
    icon: 'text-green-400',
  },
  warning: {
    bg: 'bg-yellow-900/20',
    border: 'border-yellow-800/50',
    text: 'text-yellow-200',
    icon: 'text-yellow-400',
  },
  error: {
    bg: 'bg-red-900/20',
    border: 'border-red-800/50',
    text: 'text-red-200',
    icon: 'text-red-400',
  },
};

const defaultIcons: Record<AlertVariant, React.ReactNode> = {
  info: '✓',
  success: '✓',
  warning: '⚠️',
  error: '✕',
};

const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
  (
    {
      variant = 'info',
      title,
      description,
      icon,
      onClose,
      closeable = false,
      className = '',
      children,
      ...props
    },
    ref
  ) => {
    const classes = variantClasses[variant];
    const displayIcon = icon || defaultIcons[variant];

    return (
      <div
        ref={ref}
        role="alert"
        className={`
          rounded-lg border backdrop-blur-sm
          p-4 flex gap-3
          transition duration-300
          ${classes.bg}
          ${classes.border}
          ${classes.text}
          ${className}
        `}
        {...props}
      >
        {displayIcon && (
          <div className={`flex-shrink-0 flex items-start pt-0.5 ${classes.icon}`}>
            {typeof displayIcon === 'string' ? (
              <span className="text-lg">{displayIcon}</span>
            ) : (
              displayIcon
            )}
          </div>
        )}

        <div className="flex-1">
          {title && <h3 className="font-semibold text-sm mb-1">{title}</h3>}
          {description || children ? (
            <div className="text-sm opacity-90">
              {description || children}
            </div>
          ) : null}
        </div>

        {closeable && onClose && (
          <button
            onClick={onClose}
            aria-label="Close alert"
            className="flex-shrink-0 opacity-60 hover:opacity-100 transition duration-200 text-lg leading-none"
          >
            ✕
          </button>
        )}
      </div>
    );
  }
);

Alert.displayName = 'Alert';

export default Alert;
