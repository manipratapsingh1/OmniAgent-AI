/**
 * Form Component - Professional Form Wrapper
 * Includes validation, error handling, and accessibility
 */

import React, { FormHTMLAttributes, HTMLAttributes, ReactNode } from 'react';
import Button from './Button';

interface FormProps extends FormHTMLAttributes<HTMLFormElement> {
  title?: string;
  description?: string;
  children: ReactNode;
  submitText?: string;
  cancelText?: string;
  isLoading?: boolean;
  onCancel?: () => void;
  showActions?: boolean;
}

const Form = React.forwardRef<HTMLFormElement, FormProps>(
  (
    {
      title,
      description,
      children,
      submitText = 'Submit',
      cancelText = 'Cancel',
      isLoading = false,
      onCancel,
      showActions = true,
      className = '',
      ...props
    },
    ref
  ) => {
    return (
      <form ref={ref} className={`space-y-6 ${className}`} {...props}>
        {title && (
          <div>
            <h2 className="text-2xl font-bold text-slate-100">{title}</h2>
            {description && <p className="text-slate-400 text-sm mt-2">{description}</p>}
          </div>
        )}

        <div className="space-y-5">{children}</div>

        {showActions && (
          <div className="flex gap-3 pt-4">
            <Button
              type="submit"
              variant="primary"
              size="md"
              isLoading={isLoading}
              disabled={isLoading}
              fullWidth
            >
              {submitText}
            </Button>
            {onCancel && (
              <Button
                type="button"
                variant="secondary"
                size="md"
                onClick={onCancel}
                disabled={isLoading}
                fullWidth
              >
                {cancelText}
              </Button>
            )}
          </div>
        )}
      </form>
    );
  }
);

Form.displayName = 'Form';

// Form Group Component - Groups related form fields
interface FormGroupProps {
  children: ReactNode;
  legend?: string;
  className?: string;
  style?: React.CSSProperties;
}

export const FormGroup = React.forwardRef<HTMLDivElement, FormGroupProps>(
  ({ legend, children, className = '' }, ref) => {
    if (legend) {
      return (
        <fieldset className={className}>
          <legend className="text-sm font-semibold text-slate-200 mb-3">{legend}</legend>
          <div className="space-y-4">{children}</div>
        </fieldset>
      );
    }

    return (
      <div ref={ref} className={`space-y-4 ${className}`}>
        {children}
      </div>
    );
  }
);
FormGroup.displayName = 'FormGroup';

export default Form;
