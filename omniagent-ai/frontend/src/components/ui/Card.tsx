/**
 * Card Component - Flexible Container for Content
 * Supports multiple layouts and glass-morphism effect
 */

import React, { HTMLAttributes } from 'react';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'premium' | 'outline';
  interactive?: boolean;
  children: React.ReactNode;
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ variant = 'default', interactive = false, className = '', children, ...props }, ref) => {
    const variantClasses = {
      default: 'bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-slate-700/50',
      premium: 'bg-gradient-to-br from-slate-800/50 via-blue-950/20 to-slate-900/50 backdrop-blur-xl border border-blue-600/30 shadow-2xl',
      outline: 'bg-transparent border-2 border-slate-700/50 backdrop-blur-sm',
    };

    return (
      <div
        ref={ref}
        className={`
          rounded-xl p-4 transition duration-300
          ${variantClasses[variant]}
          ${interactive ? 'hover:shadow-lg hover:border-blue-500/30 cursor-pointer hover:-translate-y-1' : ''}
          ${className}
        `}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';

// Card Header Component
interface CardHeaderProps extends HTMLAttributes<HTMLDivElement> {
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
}

export const CardHeader = React.forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ title, subtitle, action, className = '', ...props }, ref) => (
    <div ref={ref} className={`px-0 pb-4 border-b border-slate-700/50 flex items-start justify-between ${className}`} {...props}>
      <div>
        {title && <h3 className="text-lg font-semibold text-slate-100">{title}</h3>}
        {subtitle && <p className="text-sm text-slate-400 mt-1">{subtitle}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  )
);
CardHeader.displayName = 'CardHeader';

// Card Body Component
interface CardBodyProps extends HTMLAttributes<HTMLDivElement> {}

export const CardBody = React.forwardRef<HTMLDivElement, CardBodyProps>(
  ({ className = '', children, ...props }, ref) => (
    <div ref={ref} className={`py-4 ${className}`} {...props}>
      {children}
    </div>
  )
);
CardBody.displayName = 'CardBody';

// Card Footer Component
interface CardFooterProps extends HTMLAttributes<HTMLDivElement> {}

export const CardFooter = React.forwardRef<HTMLDivElement, CardFooterProps>(
  ({ className = '', children, ...props }, ref) => (
    <div ref={ref} className={`pt-4 border-t border-slate-700/50 flex items-center justify-between ${className}`} {...props}>
      {children}
    </div>
  )
);
CardFooter.displayName = 'CardFooter';

export default Card;
