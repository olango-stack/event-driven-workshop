import type React from "react";

import Toast, { type ToastMessage } from "./Toast";
import "./ToastContainer.css";

interface ToastContainerProps {
	toasts: ToastMessage[];
	onRemoveToast: (id: string) => void;
}

const ToastContainer: React.FC<ToastContainerProps> = ({
	toasts,
	onRemoveToast,
}) => {
	if (toasts.length === 0) return null;

	return (
		<div className="toast-container">
			{toasts.map((toast) => (
				<Toast key={toast.id} toast={toast} onRemove={onRemoveToast} />
			))}
		</div>
	);
};

export default ToastContainer;
