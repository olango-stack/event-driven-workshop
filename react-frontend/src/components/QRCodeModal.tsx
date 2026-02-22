import { X } from "lucide-react";

import QRCode from "qrcode";
import type React from "react";
import { useEffect, useRef, useState } from "react";

import "./QRCodeModal.css";

interface QRCodeModalProps {
	isOpen: boolean;
	onClose: () => void;
}

const QRCodeModal: React.FC<QRCodeModalProps> = ({ isOpen, onClose }) => {
	const canvasRef = useRef<HTMLCanvasElement>(null);
	const [currentUrl, setCurrentUrl] = useState("");

	// Lock body scroll when modal is open
	useEffect(() => {
		if (isOpen) {
			document.body.classList.add("modal-open");
		} else {
			document.body.classList.remove("modal-open");
		}

		return () => {
			document.body.classList.remove("modal-open");
		};
	}, [isOpen]);

	useEffect(() => {
		if (isOpen && canvasRef.current) {
			const url = window.location.href;
			setCurrentUrl(url);

			// Generate QR code
			QRCode.toCanvas(
				canvasRef.current,
				url,
				{
					width: 256,
					margin: 2,
					color: {
						dark: "#4c1d95", // Mystical purple theme
						light: "#ffffff",
					},
				},
				(error) => {
					if (error) {
						console.error("Error generating QR code:", error?.message || "Unknown error");
					}
				},
			);
		}
	}, [isOpen]);

	const handleOverlayClick = (e: React.MouseEvent) => {
		if (e.target === e.currentTarget) {
			onClose();
		}
	};

	const copyToClipboard = async () => {
		try {
			await navigator.clipboard.writeText(currentUrl);
			// You could add a toast notification here if desired
		} catch (error) {
			console.error("Failed to copy URL:", error instanceof Error ? error.message : "Unknown error");
		}
	};

	const handleKeyDown = (event: React.KeyboardEvent, action: () => void) => {
		if (event.key === "Enter" || event.key === " ") {
			event.preventDefault();
			action();
		}
	};

	if (!isOpen) return null;

	return (
		<div
			className="qr-modal-overlay"
			onClick={handleOverlayClick}
			onKeyDown={(e) => {
				if (e.key === "Escape") {
					onClose();
				}
			}}
			role="dialog"
			aria-modal="true"
			aria-labelledby="qr-modal-title"
			tabIndex={-1}
		>
			<div className="qr-modal-content" role="document">
				<div className="qr-modal-header">
					<h2 id="qr-modal-title">Share This Magical Store</h2>
					<button
						type="button"
						className="qr-modal-close"
						onClick={onClose}
						onKeyDown={(e) => handleKeyDown(e, onClose)}
						aria-label="Close QR code modal"
					>
						<X size={24} />
					</button>
				</div>

				<div className="qr-modal-body">
					<div className="qr-code-container">
						<canvas ref={canvasRef} />
					</div>

					<div className="qr-modal-info">
						<p className="qr-description">
							Scan this QR code to share the Unicorn Dreams Store with friends!
						</p>

						<div className="url-container">
							<input
								type="text"
								value={currentUrl}
								readOnly
								className="url-input"
							/>
							<button
								type="button"
								onClick={copyToClipboard}
								onKeyDown={(e) => handleKeyDown(e, copyToClipboard)}
								className="copy-button"
								title="Copy URL"
								aria-label="Copy URL to clipboard"
							>
								📋
							</button>
						</div>
					</div>
				</div>
			</div>
		</div>
	);
};

export default QRCodeModal;
