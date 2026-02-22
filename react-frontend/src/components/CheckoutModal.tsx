import { faker } from "@faker-js/faker";

import {
	CheckCircle,
	CreditCard,
	Lock,
	MapPin,
	ShoppingBag,
	Shuffle,
	User,
	X,
} from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";
import { cartService, formatCurrency } from "../services/cartService";
import type { CartItem, CheckoutRequest, OrderData } from "../types";
import "./CheckoutModal.css";

interface CheckoutModalProps {
	items: CartItem[];
	totalPrice: number;
	userId: string;
	onClose: () => void;
	onCheckoutComplete: () => void;
	showError?: (message: string) => void;
	// TODO: Lab 4a.6 - Add onOrderSubmitted prop for async checkout flow
}

const CheckoutModal: React.FC<CheckoutModalProps> = ({
	items,
	totalPrice,
	userId,
	onClose,
	onCheckoutComplete,
	showError,
}) => {
	const [loading, setLoading] = useState(false);
	const [orderComplete, setOrderComplete] = useState(false);
	const [orderData, setOrderData] = useState<OrderData | null>(null);

	// Lock body scroll when modal is open
	useEffect(() => {
		document.body.classList.add("modal-open");
		return () => {
			document.body.classList.remove("modal-open");
		};
	}, []);

	// Generate random expiry month and year
	const generateRandomExpiry = () => {
		const currentYear = new Date().getFullYear();
		const randomMonth = Math.floor(Math.random() * 12) + 1;
		const randomYear = currentYear + 1 + Math.floor(Math.random() * 3); // Current year + 1 to + 3
		return {
			month: String(randomMonth).padStart(2, "0"),
			year: String(randomYear),
		};
	};

	const [formData, setFormData] = useState(() => {
		const expiry = generateRandomExpiry();
		return {
			email: "",
			firstName: "",
			lastName: "",
			phone: "",
			street: "123 Elm Street", // Pre-populated address
			city: "Seattle", // Pre-populated city
			state: "WA", // Pre-populated state for Seattle
			zipCode: "90210", // Pre-populated zip code
			cardNumber: "4111111111111111", // Pre-populated CC number
			expiryMonth: expiry.month, // Random expiry month
			expiryYear: expiry.year, // Random expiry year (current + 1 to + 3)
			cvv: "012", // Pre-populated CVV
			cardholderName: "", // Will be auto-populated from first + last name
		};
	});

	// Tax rate is always 5%
	const estimatedTax = totalPrice * 0.05;
	const estimatedTotal = totalPrice + estimatedTax;

	// Auto-populate cardholder name when first/last name changes
	useEffect(() => {
		const fullName = `${formData.firstName} ${formData.lastName}`.trim();
		if (fullName && fullName !== " ") {
			setFormData((prev) => ({ ...prev, cardholderName: fullName }));
		}
	}, [formData.firstName, formData.lastName]);

	const handleInputChange = (
		e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
	) => {
		const { name, value } = e.target;
		setFormData((prev) => ({ ...prev, [name]: value }));
	};

	// Generate random contact information
	const generateRandomContact = () => {
		const firstName = faker.person.firstName();
		const lastName = faker.person.lastName();
		const email = `${firstName.toLowerCase()}.${lastName.toLowerCase()}@email.com`;
		// Generate phone number with 555 area code
		const phoneNumber = `555-${faker.string.numeric(3)}-${faker.string.numeric(4)}`;

		setFormData((prev) => ({
			...prev,
			firstName,
			lastName,
			email,
			phone: phoneNumber,
		}));
	};

	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault();

		if (loading) return;

		setLoading(true);

		try {
			const checkoutData: CheckoutRequest = {
				user_id: userId,
				customer_info: {
					email: formData.email,
					first_name: formData.firstName,
					last_name: formData.lastName,
					phone: formData.phone,
					address: {
						street: formData.street,
						city: formData.city,
						state: formData.state,
						zip_code: formData.zipCode,
						country: "US",
					},
				},
				payment_method: {
					type: "credit_card",
					card_number: formData.cardNumber,
					expiry_month: formData.expiryMonth,
					expiry_year: formData.expiryYear,
					cvv: formData.cvv,
					cardholder_name: formData.cardholderName,
				},
				shipping_address: {
					street: formData.street,
					city: formData.city,
					state: formData.state,
					zip_code: formData.zipCode,
					country: "US",
				},
				billing_address: {
					street: formData.street,
					city: formData.city,
					state: formData.state,
					zip_code: formData.zipCode,
					country: "US",
				},
			};

			const result = await cartService.checkout(checkoutData);
			
			// TODO: Lab 4a.6 - Add dual flow support (sync vs async checkout)
			// Sync flow - show completion
			setOrderData(result);
			setOrderComplete(true);
			
		} catch (error) {
			console.error("Checkout failed:", error);
			if (showError) {
				showError("Checkout failed. Please try again.");
			} else {
				alert("Checkout failed. Please try again.");
			}
		} finally {
			setLoading(false);
		}
	};

	// Handle continue shopping
	const handleContinueShopping = () => {
		onCheckoutComplete();
		onClose();
	};

	const handleKeyDown = (event: React.KeyboardEvent, action: () => void) => {
		if (event.key === "Enter" || event.key === " ") {
			event.preventDefault();
			action();
		}
	};

	return (
		<div
			className="checkout-modal-overlay"
			onClick={onClose}
			onKeyDown={(e) => {
				if (e.key === "Escape") {
					onClose();
				}
			}}
			role="dialog"
			aria-modal="true"
			aria-labelledby="checkout-modal-title"
			tabIndex={-1}
		>
			<div
				className="checkout-modal"
				onClick={(e) => e.stopPropagation()}
				onKeyDown={(e) => {
					if (e.key === 'Enter' || e.key === ' ') {
						e.stopPropagation();
					}
				}}
				role="document"
			>
				<div className="modal-header">
					<h2 id="checkout-modal-title" className="modal-title">
						{orderComplete ? (
							<>
								<CheckCircle size={24} />
								Order Complete
							</>
						) : (
							<>
								<Lock size={24} />
								Secure Checkout
							</>
						)}
					</h2>
					<button
						type="button"
						className="close-btn"
						onClick={onClose}
						disabled={loading}
						onKeyDown={(e) => handleKeyDown(e, onClose)}
						aria-label="Close checkout modal"
					>
						<X size={24} />
					</button>
				</div>

				<div className="modal-content">
					{orderComplete ? (
						// Success View
						<div className="success-container">
							<div className="success-content">
								<div className="success-icon">
									<CheckCircle size={64} color="#10B981" />
								</div>
								<h3 className="success-title">Order Placed Successfully!</h3>
								<p className="success-message">
									Thank you for your purchase. Your order has been confirmed.
								</p>

								{orderData && (
									<div className="order-details">
										<div className="order-info">
											<div className="order-row">
												<span className="order-label">Order ID:</span>
												<span className="order-value">
													{orderData.order_id}
												</span>
											</div>
											<div className="order-row">
												<span className="order-label">Total Amount:</span>
												<span className="order-value">
													{formatCurrency(orderData.total_amount || totalPrice)}
												</span>
											</div>
											<div className="order-row">
												<span className="order-label">Status:</span>
												<span className="order-value status-complete">
													{orderData.status || "Completed"}
												</span>
											</div>
											{orderData.fulfillment_tracking && (
												<div className="order-row">
													<span className="order-label">Tracking:</span>
													<span className="order-value">
														{orderData.fulfillment_tracking}
													</span>
												</div>
											)}
										</div>
									</div>
								)}

								<button
									type="button"
									className="btn btn-primary btn-lg continue-shopping-btn"
									onClick={handleContinueShopping}
									onKeyDown={(e) => handleKeyDown(e, handleContinueShopping)}
									aria-label="Continue shopping"
								>
									<ShoppingBag size={20} />
									Continue Shopping
								</button>
							</div>
						</div>
					) : (
						// Checkout Form View
						<>
							<div className="checkout-form-container">
								<form onSubmit={handleSubmit} className="checkout-form">
									{/* Customer Information */}
									<div className="form-section">
										<div className="section-header">
											<h3 className="section-title">
												<User size={20} />
												Contact Information
											</h3>
											<button
												type="button"
												className="btn btn-secondary btn-sm generate-btn"
												onClick={generateRandomContact}
												onKeyDown={(e) =>
													handleKeyDown(e, generateRandomContact)
												}
												title="Generate random contact information"
												aria-label="Generate random contact information"
											>
												<Shuffle size={16} />
												Generate
											</button>
										</div>
										<div className="form-grid">
											<div className="form-group">
												<label htmlFor="email">Email Address *</label>
												<input
													type="email"
													id="email"
													name="email"
													value={formData.email}
													onChange={handleInputChange}
													required
												/>
											</div>
											<div className="form-group">
												<label htmlFor="phone">Phone Number</label>
												<input
													type="tel"
													id="phone"
													name="phone"
													value={formData.phone}
													onChange={handleInputChange}
												/>
											</div>
											<div className="form-group">
												<label htmlFor="firstName">First Name *</label>
												<input
													type="text"
													id="firstName"
													name="firstName"
													value={formData.firstName}
													onChange={handleInputChange}
													required
												/>
											</div>
											<div className="form-group">
												<label htmlFor="lastName">Last Name *</label>
												<input
													type="text"
													id="lastName"
													name="lastName"
													value={formData.lastName}
													onChange={handleInputChange}
													required
												/>
											</div>
										</div>
									</div>

									{/* Shipping Address */}
									<div className="form-section">
										<h3 className="section-title">
											<MapPin size={20} />
											Shipping Address
										</h3>
										<div className="form-grid">
											<div className="form-group full-width">
												<label htmlFor="street">Street Address *</label>
												<input
													type="text"
													id="street"
													name="street"
													value={formData.street}
													onChange={handleInputChange}
													required
												/>
											</div>
											<div className="form-group">
												<label htmlFor="city">City *</label>
												<input
													type="text"
													id="city"
													name="city"
													value={formData.city}
													onChange={handleInputChange}
													required
												/>
											</div>
											<div className="form-group">
												<label htmlFor="state">Province/State *</label>
												<input
													type="text"
													id="state"
													name="state"
													value={formData.state}
													onChange={handleInputChange}
													placeholder="Enter province or state"
													required
												/>
											</div>
											<div className="form-group">
												<label htmlFor="zipCode">ZIP Code *</label>
												<input
													type="text"
													id="zipCode"
													name="zipCode"
													value={formData.zipCode}
													onChange={handleInputChange}
													required
												/>
											</div>
										</div>
									</div>

									{/* Payment Information */}
									<div className="form-section">
										<h3 className="section-title">
											<CreditCard size={20} />
											Payment Information
										</h3>
										<div className="form-grid">
											<div className="form-group full-width">
												<label htmlFor="cardNumber">Card Number *</label>
												<input
													type="text"
													id="cardNumber"
													name="cardNumber"
													value={formData.cardNumber}
													onChange={handleInputChange}
													placeholder="1234 5678 9012 3456"
													required
												/>
											</div>
											<div className="form-group full-width">
												<label htmlFor="cardholderName">
													Cardholder Name *
												</label>
												<input
													type="text"
													id="cardholderName"
													name="cardholderName"
													value={formData.cardholderName}
													onChange={handleInputChange}
													required
													readOnly
													title="Auto-populated from contact information"
												/>
											</div>
											<div className="form-group">
												<label htmlFor="expiryMonth">Expiry Month *</label>
												<select
													id="expiryMonth"
													name="expiryMonth"
													value={formData.expiryMonth}
													onChange={handleInputChange}
													required
												>
													<option value="">Month</option>
													{Array.from({ length: 12 }, (_, i) => {
														const monthValue = String(i + 1).padStart(2, "0");
														return (
															<option
																key={`month-${monthValue}`}
																value={monthValue}
															>
																{monthValue}
															</option>
														);
													})}
												</select>
											</div>
											<div className="form-group">
												<label htmlFor="expiryYear">Expiry Year *</label>
												<select
													id="expiryYear"
													name="expiryYear"
													value={formData.expiryYear}
													onChange={handleInputChange}
													required
												>
													<option value="">Year</option>
													{Array.from({ length: 10 }, (_, i) => {
														const year = new Date().getFullYear() + i;
														return (
															<option key={year} value={String(year)}>
																{year}
															</option>
														);
													})}
												</select>
											</div>
											<div className="form-group">
												<label htmlFor="cvv">CVV *</label>
												<input
													type="text"
													id="cvv"
													name="cvv"
													value={formData.cvv}
													onChange={handleInputChange}
													placeholder="123"
													maxLength={4}
													required
												/>
											</div>
										</div>
									</div>

									<button
										type="submit"
										className="btn btn-success btn-lg place-order-btn"
										disabled={loading}
									>
										{loading ? (
											<>
												<span className="spinner"></span>
												Submitting...
											</>
										) : (
											<>
												<CreditCard size={20} />
												Place Order - {formatCurrency(estimatedTotal)}
											</>
										)}
									</button>
								</form>
							</div>

							<div className="order-summary">
								<h3>Order Summary</h3>

								<div className="summary-items">
									{items.map((item) => (
										<div key={item.product_id} className="summary-item">
											<img src={item.image} alt={item.name} />
											<div className="item-info">
												<div className="item-name">{item.name}</div>
												<div className="item-details">
													Qty: {item.quantity} × {formatCurrency(item.price)}
												</div>
											</div>
											<div className="item-total">
												{formatCurrency(item.price * item.quantity)}
											</div>
										</div>
									))}
								</div>

								<div className="summary-totals">
									<div className="summary-line">
										<span>Subtotal:</span>
										<span>{formatCurrency(totalPrice)}</span>
									</div>
									<div className="summary-line">
										<span>Tax (5%):</span>
										<span>{formatCurrency(estimatedTax)}</span>
									</div>
									<div className="summary-line summary-total">
										<span>Total:</span>
										<span>{formatCurrency(estimatedTotal)}</span>
									</div>
								</div>
							</div>
						</>
					)}
				</div>
			</div>
		</div>
	);
};

export default CheckoutModal;