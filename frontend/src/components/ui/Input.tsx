import React from 'react';
import { cn } from '../../lib/utils';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string;
  label?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, error, label, id, ...props }, ref) => {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', width: '100%' }}>
        {label && (
          <label
            htmlFor={id}
            style={{
              fontSize: '0.875rem',
              fontWeight: 500,
              color: 'rgb(var(--foreground))',
              textAlign: 'left',
            }}
          >
            {label}
          </label>
        )}
        <input ref={ref} id={id} className={cn('input', className)} {...props} />
        {error && (
          <span style={{ fontSize: '0.75rem', color: 'rgb(var(--danger))', textAlign: 'left' }}>
            {error}
          </span>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
