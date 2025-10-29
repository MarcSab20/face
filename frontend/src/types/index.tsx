import React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

// Loading Spinner
export function LoadingSpinner({ className }: { className?: string }) {
  return (
    <div className={cn('flex items-center justify-center', className)}>
      <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
    </div>
  );
}

// Full Page Loading
export function PageLoading({ message = 'Chargement...' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-96">
      <LoadingSpinner className="mb-4" />
      <p className="text-gray-600 dark:text-gray-400">{message}</p>
    </div>
  );
}

// Empty State
interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  action?: React.ReactNode;
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="card text-center py-12">
      {icon && <div className="text-6xl mb-4">{icon}</div>}
      <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">{title}</h3>
      <p className="text-gray-600 dark:text-gray-400 mb-6">{description}</p>
      {action && <div>{action}</div>}
    </div>
  );
}

// Error State
interface ErrorStateProps {
  title?: string;
  message: string;
  retry?: () => void;
}

export function ErrorState({
  title = 'Une erreur est survenue',
  message,
  retry,
}: ErrorStateProps) {
  return (
    <div className="card text-center py-12">
      <div className="text-6xl mb-4">⚠️</div>
      <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">{title}</h3>
      <p className="text-gray-600 dark:text-gray-400 mb-6">{message}</p>
      {retry && (
        <button onClick={retry} className="btn btn-primary">
          Réessayer
        </button>
      )}
    </div>
  );
}

// Modal
interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export function Modal({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = 'md',
}: ModalProps) {
  if (!isOpen) return null;

  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 animate-fade-in">
      <div
        className={cn(
          'bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-h-[90vh] overflow-y-auto',
          sizeClasses[size]
        )}
      >
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">{title}</h2>
        </div>
        <div className="p-6">{children}</div>
        {footer && (
          <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end space-x-3">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}

// Confirm Dialog
interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'primary';
}

export function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = 'Confirmer',
  cancelLabel = 'Annuler',
  variant = 'primary',
}: ConfirmDialogProps) {
  if (!isOpen) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      size="sm"
      footer={
        <>
          <button onClick={onClose} className="btn btn-secondary">
            {cancelLabel}
          </button>
          <button
            onClick={() => {
              onConfirm();
              onClose();
            }}
            className={cn('btn', variant === 'danger' ? 'btn-danger' : 'btn-primary')}
          >
            {confirmLabel}
          </button>
        </>
      }
    >
      <p className="text-gray-700 dark:text-gray-300">{message}</p>
    </Modal>
  );
}

// Badge
interface BadgeProps {
  children: React.ReactNode;
  variant?: 'primary' | 'success' | 'danger' | 'warning' | 'info';
  size?: 'sm' | 'md' | 'lg';
}

export function Badge({ children, variant = 'primary', size = 'md' }: BadgeProps) {
  const variantClasses = {
    primary: 'badge-primary',
    success: 'badge-success',
    danger: 'badge-danger',
    warning: 'badge-warning',
    info: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  };

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-3 py-1',
    lg: 'text-base px-4 py-1.5',
  };

  return (
    <span className={cn('badge', variantClasses[variant], sizeClasses[size])}>
      {children}
    </span>
  );
}

// Tooltip
interface TooltipProps {
  content: string;
  children: React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
}

export function Tooltip({ content, children, position = 'top' }: TooltipProps) {
  const positionClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  };

  return (
    <div className="relative group inline-block">
      {children}
      <div
        className={cn(
          'absolute z-10 px-3 py-2 text-sm font-medium text-white bg-gray-900 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all whitespace-nowrap',
          positionClasses[position]
        )}
      >
        {content}
      </div>
    </div>
  );
}

// Card with Hover Effect
interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  hoverable?: boolean;
}

export function Card({ children, className, onClick, hoverable = false }: CardProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        'card',
        hoverable && 'hover:shadow-xl transition-shadow cursor-pointer',
        className
      )}
    >
      {children}
    </div>
  );
}

// Progress Bar
interface ProgressBarProps {
  value: number;
  max?: number;
  showLabel?: boolean;
  color?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function ProgressBar({
  value,
  max = 100,
  showLabel = false,
  color = '#667eea',
  size = 'md',
}: ProgressBarProps) {
  const percentage = Math.min((value / max) * 100, 100);

  const sizeClasses = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3',
  };

  return (
    <div className="w-full">
      <div className={cn('w-full bg-gray-200 dark:bg-gray-700 rounded-full', sizeClasses[size])}>
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: `${percentage}%`,
            backgroundColor: color,
          }}
        />
      </div>
      {showLabel && (
        <div className="text-xs text-gray-600 dark:text-gray-400 mt-1 text-right">
          {value} / {max}
        </div>
      )}
    </div>
  );
}

// Skeleton Loader
interface SkeletonProps {
  className?: string;
  count?: number;
}

export function Skeleton({ className, count = 1 }: SkeletonProps) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={cn(
            'animate-pulse bg-gray-200 dark:bg-gray-700 rounded',
            className || 'h-4 w-full mb-2'
          )}
        />
      ))}
    </>
  );
}

// Alert
interface AlertProps {
  type?: 'info' | 'success' | 'warning' | 'error';
  title?: string;
  children: React.ReactNode;
  icon?: React.ReactNode;
  onClose?: () => void;
}

export function Alert({ type = 'info', title, children, icon, onClose }: AlertProps) {
  const typeStyles = {
    info: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 text-blue-900 dark:text-blue-200',
    success:
      'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800 text-green-900 dark:text-green-200',
    warning:
      'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800 text-yellow-900 dark:text-yellow-200',
    error:
      'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-900 dark:text-red-200',
  };

  return (
    <div className={cn('border rounded-lg p-4', typeStyles[type])}>
      <div className="flex items-start space-x-3">
        {icon && <div className="flex-shrink-0 mt-0.5">{icon}</div>}
        <div className="flex-1">
          {title && <p className="font-medium mb-1">{title}</p>}
          <div className="text-sm">{children}</div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="flex-shrink-0 ml-4 hover:opacity-75 transition-opacity"
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
}

// Tabs
interface Tab {
  id: string;
  label: string;
  icon?: React.ElementType;
}

interface TabsProps {
  tabs: Tab[];
  activeTab: string;
  onChange: (tabId: string) => void;
}

export function Tabs({ tabs, activeTab, onChange }: TabsProps) {
  return (
    <div className="border-b border-gray-200 dark:border-gray-700">
      <nav className="-mb-px flex space-x-8">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className={cn(
              'flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors',
              activeTab === tab.id
                ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
            )}
          >
            {tab.icon && <tab.icon className="w-5 h-5" />}
            <span>{tab.label}</span>
          </button>
        ))}
      </nav>
    </div>
  );
}