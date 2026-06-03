import { motion, AnimatePresence } from 'motion/react';
import { CheckCircle, XCircle, Info, AlertTriangle } from 'lucide-react';
import { useEffect } from 'react';

interface ToastProps {
  isOpen: boolean;
  onClose: () => void;
  message: string;
  type?: 'success' | 'error' | 'info' | 'warning';
  duration?: number;
}

export function Toast({
  isOpen,
  onClose,
  message,
  type = 'info',
  duration = 3000,
}: ToastProps) {
  useEffect(() => {
    if (isOpen && duration > 0) {
      const timer = setTimeout(onClose, duration);
      return () => clearTimeout(timer);
    }
  }, [isOpen, duration, onClose]);

  const getIcon = () => {
    switch (type) {
      case 'success':
        return <CheckCircle size={24} className="text-success" />;
      case 'error':
        return <XCircle size={24} className="text-[#ff3b5c]" />;
      case 'warning':
        return <AlertTriangle size={24} className="text-warning" />;
      case 'info':
        return <Info size={24} className="text-primary" />;
    }
  };

  const getGradient = () => {
    switch (type) {
      case 'success':
        return 'from-success to-success';
      case 'error':
        return 'from-[#ff3b5c] to-[#ff1744]';
      case 'warning':
        return 'from-[#ffb800] to-[#ff8c00]';
      case 'info':
        return 'from-primary to-primary';
    }
  };

  const getBorderColor = () => {
    switch (type) {
      case 'success':
        return 'border-success';
      case 'error':
        return 'border-[#ff3b5c]';
      case 'warning':
        return 'border-[#ffb800]';
      case 'info':
        return 'border-primary';
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0, y: -50, x: '-50%' }}
          animate={{ opacity: 1, y: 0, x: '-50%' }}
          exit={{ opacity: 0, y: -50, x: '-50%' }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          className="fixed top-8 left-1/2 z-50 max-w-md"
        >
          <div className={`bg-card/95 backdrop-blur-xl rounded-xl p-4 flex items-center gap-4 border-2 ${getBorderColor()} relative overflow-hidden`}>
            {/* Background glow */}
            <div className="absolute inset-0 opacity-10">
              <div className={`absolute inset-0 bg-gradient-to-r ${getGradient()} blur-xl`} />
            </div>

            {/* Content */}
            <div className="relative z-10 flex items-center gap-4">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.1, type: 'spring', stiffness: 200 }}
              >
                {getIcon()}
              </motion.div>
              <p className="text-foreground flex-1">{message}</p>
            </div>

            {/* Progress bar */}
            {duration > 0 && (
              <motion.div
                initial={{ scaleX: 1 }}
                animate={{ scaleX: 0 }}
                transition={{ duration: duration / 1000, ease: 'linear' }}
                className={`absolute bottom-0 left-0 h-1 bg-gradient-to-r ${getGradient()} origin-left`}
              />
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
