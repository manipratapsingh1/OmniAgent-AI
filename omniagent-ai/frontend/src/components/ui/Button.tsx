/**
 * Button Component - Professional & Accessible
 * Supports multiple variants, sizes, and states
 */

import React, { ButtonHTMLAttributes, forwardRef } from 'react';
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import { THEME } from '../../theme';

type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'success' | 'outline' | 'ghost';
type ButtonSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  fullWidth?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  disabled?: boolean;
  ariaLabel?: string;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    'bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white border border-blue-400/30 shadow-lg hover:shadow-glow-md',
  secondary:
    'bg-slate-700/50 hover:bg-slate-600/50 text-white border border-slate-600/50 shadow-md',
  danger:
    'bg-red-600/20 hover:bg-red-600/30 text-red-300 border border-red-600/30 shadow-md',
  success:
    'bg-green-600/20 hover:bg-green-600/30 text-green-300 border border-green-600/30 shadow-md',
  outline:
    'bg-transparent border border-blue-500/50 text-blue-300 hover:bg-blue-600/10 hover:border-blue-500 shadow-md',
  ghost: 'bg-transparent text-slate-300 hover:bg-slate-700/30 hover:text-white border-none shadow-none',
};

const sizeClasses: Record<ButtonSize, string> = {
  xs: 'px-2 py-1 text-xs',
  sm: 'px-3 py-2 text-sm',
  md: 'px-4 py-2.5 text-base',
  lg: 'px-6 py-3 text-lg',
  xl: 'px-8 py-4 text-xl',
};

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      isLoading = false,
      fullWidth = false,
      icon,
      iconPosition = 'left',
      disabled = false,
      ariaLabel,
      className = '',
      children,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || isLoading;

    return (
      <button
        ref={ref}
        disabled={isDisabled}
        aria-label={ariaLabel || undefined}
        {...(isLoading && { 'aria-busy': 'true' })}
        className={`
          font-medium rounded-lg transition duration-300 
          flex items-center justify-center gap-2
          disabled:opacity-60 disabled:cursor-not-allowed
          active:scale-95 focus:outline-none focus:ring-2 focus:ring-blue-500/50
          ${variantClasses[variant]}
          ${sizeClasses[size]}
          ${fullWidth ? 'w-full' : ''}
          ${className}
        `}
        {...props}
      >
        {icon && iconPosition === 'left' && !isLoading && (
          <span className="flex items-center">{icon}</span>
        )}
        {isLoading && (
          <span className="inline-block animate-spin">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          </span>
        )}
        {children}
        {icon && iconPosition === 'right' && !isLoading && (
          <span className="flex items-center">{icon}</span>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';

export default Button;
