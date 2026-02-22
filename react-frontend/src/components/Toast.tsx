import { AlertCircle, AlertTriangle, CheckCircle, Info, X } from "lucide-react";
import type React from "react";
import { useCallback, useEffect, useState } from "react";

import "./Toast.css";

export type ToastType = "success" | "error" | "warning" | "info";

export interface ToastMessage {
	id: string;
	message: string;
	type: ToastType;
	duration?: number;
}

interface ToastProps {
	toast: ToastMessage;
	onRemove: (id: string) => void;
}

const Toast: React.FC<ToastProps> = ({ toast, onRemove }) => {
	const [isVisible, setIsVisible] = useState(false);
	const [isRemoving, setIsRemoving] = useState(false);

	const handleRemove = useCallback(() => {
		setIsRemoving(true);
		setTimeout(() => {
			onRemove(toast.id);
		}, 300); // Match CSS animation duration
	}, [onRemove, toast.id]);

	const handleKeyDown = (event: React.KeyboardEvent) => {
		if (event.key === "Enter" || event.key === " ") {
			event.preventDefault();
			handleRemove();
		}
	};

	useEffect(() => {
		// Show toast with animation
		const showTimer = setTimeout(() => setIsVisible(true), 10);

		// Auto-remove after duration (default 3 seconds)
		const duration = toast.duration || 3000;
		const removeTimer = setTimeout(() => {
			handleRemove();
		}, duration);

		return () => {
			clearTimeout(showTimer);
			clearTimeout(removeTimer);
		};
	}, [toast.duration, handleRemove]);

	const getIcon = () => {
		switch (toast.type) {
			case "success":
				return <CheckCircle size={20} />;
			case "error":
				return <AlertCircle size={20} />;
			case "warning":
				return <AlertTriangle size={20} />;
			default:
				return <Info size={20} />;
		}
	};

	return (
		<div
			className={`toast toast-${toast.type} ${isVisible ? "toast-visible" : ""} ${isRemoving ? "toast-removing" : ""}`}
		>
			<div className="toast-icon">{getIcon()}</div>
			<div className="toast-message">{toast.message}</div>
			<button
				type="button"
				className="toast-close"
				onClick={handleRemove}
				onKeyDown={handleKeyDown}
				aria-label="Close notification"
			>
				<X size={16} />
			</button>
		</div>
	);
};

export default Toast;
