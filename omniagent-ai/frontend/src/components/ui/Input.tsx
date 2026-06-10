/**
 * Input Component - Professional & Accessible
 * Includes label, error handling, and proper ARIA attributes
 */

import React, { InputHTMLAttributes, forwardRef } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  icon?: React.ReactNode;
  fullWidth?: boolean;
  required?: boolean;
  disabled?: boolean;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      helperText,
      icon,
      fullWidth = true,
      required = false,
      disabled = false,
      className = '',
      id,
      ...props
    },
    ref
  ) => {
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
    const hasError = !!error;

    return (
      <div className={fullWidth ? 'w-full' : ''}>
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-slate-200 mb-2"
          >
            {label}
            {required && <span className="text-red-400 ml-1">*</span>}
          </label>
        )}
        
        <div className="relative">
          {icon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
              {icon}
            </div>
          )}
          
          <input
            ref={ref}
            id={inputId}
            disabled={disabled}
            required={required}
            {...(hasError && { 'aria-invalid': 'true' })}
            aria-describedby={hasError ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined}
            className={`
              w-full px-4 py-3 rounded-lg
              bg-slate-800/50 border border-slate-700/50
              text-white placeholder-zinc-500
              focus:outline-none focus:border-blue-500/70 focus:bg-slate-800/70 
              focus:ring-2 focus:ring-blue-500/20
              disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-slate-800/30
              transition duration-300 shadow-sm
              ${icon ? 'pl-10' : ''}
              ${hasError ? 'border-red-600/70 focus:border-red-500' : ''}
              ${className}
            `}
            {...props}
          />
        </div>

        {hasError && (
          <p id={`${inputId}-error`} className="text-red-400 text-sm mt-2 flex items-center gap-1">
            <span>⚠️</span> {error}
          </p>
        )}
        
        {helperText && !hasError && (
          <p id={`${inputId}-helper`} className="text-slate-400 text-sm mt-2">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;
