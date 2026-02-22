import { CreditCard, Minus, Plus, ShoppingCart, Trash2 } from "lucide-react";
import type React from "react";
import { formatCurrency } from "../services/cartService";
import type { CartItem } from "../types";
import "./CartSidebar.css";

// TODO: Lab 4a.7 - Add visual feedback for pending cart operations
// TODO: Lab 4a.7 - Add rollback functionality for failed operations
// TODO: Lab 4a.7 - Show loading spinners for individual items during updates

interface CartSidebarProps {
	items: CartItem[];
	onUpdateQuantity: (productId: string, quantity: number) => void;
	onRemoveItem: (productId: string) => void;
	onClearCart: () => void;
	onCheckout: () => void;
	totalPrice: number;
	loading: boolean;
}

const CartSidebar: React.FC<CartSidebarProps> = ({
	items,
	onUpdateQuantity,
	onRemoveItem,
	onClearCart,
	onCheckout,
	totalPrice,
	loading,
}) => {
	const totalItems = items.reduce((sum, item) => sum + item.quantity, 0);
	const estimatedTax = totalPrice * 0.08;
	const estimatedTotal = totalPrice + estimatedTax;

	const handleKeyDown = (event: React.KeyboardEvent, action: () => void) => {
		if (event.key === "Enter" || event.key === " ") {
			event.preventDefault();
			action();
		}
	};

	return (
		<div className="cart-sidebar">
			<div className="cart-header">
				<div className="cart-title">
					<ShoppingCart size={20} />
					<span>Your Cart</span>
					{totalItems > 0 && <span className="cart-count">{totalItems}</span>}
				</div>
				{items.length > 0 && (
					<button
						type="button"
						className="btn btn-secondary btn-sm clear-cart-btn"
						onClick={onClearCart}
						onKeyDown={(e) => handleKeyDown(e, onClearCart)}
						disabled={loading}
						aria-label="Clear all items from cart"
					>
						Clear All
					</button>
				)}
			</div>

			<div className="cart-content">
				{items.length === 0 ? (
					<div className="empty-cart">
						<ShoppingCart size={48} className="empty-cart-icon" />
						<p className="empty-cart-text">Your cart is empty</p>
						<p className="empty-cart-subtext">
							Add some products to get started!
						</p>
					</div>
				) : (
					<>
						<div className="cart-items">
							{/* TODO: Lab 4a.7 - Add pending state styling to cart items */}
							{items.map((item) => (
								<div key={item.product_id} className="cart-item">
									<div className="item-image">
										<img src={item.image} alt={item.name} />
									</div>

									<div className="item-details">
										<h4 className="item-name">{item.name}</h4>
										<div className="item-price">
											{formatCurrency(item.price)}
										</div>

										<div className="item-controls">
											<div className="quantity-controls">
												<button
													type="button"
													className="quantity-btn"
													onClick={() =>
														onUpdateQuantity(item.product_id, item.quantity - 1)
													}
													onKeyDown={(e) =>
														handleKeyDown(e, () =>
															onUpdateQuantity(
																item.product_id,
																item.quantity - 1,
															),
														)
													}
													disabled={loading || item.quantity <= 1}
													aria-label={`Decrease quantity of ${item.name}`}
												>
													<Minus size={14} />
												</button>
												<span className="quantity-display">
													{item.quantity}
												</span>
												<button
													type="button"
													className="quantity-btn"
													onClick={() =>
														onUpdateQuantity(item.product_id, item.quantity + 1)
													}
													onKeyDown={(e) =>
														handleKeyDown(e, () =>
															onUpdateQuantity(
																item.product_id,
																item.quantity + 1,
															),
														)
													}
													disabled={loading}
													aria-label={`Increase quantity of ${item.name}`}
												>
													<Plus size={14} />
												</button>
											</div>

											<button
												type="button"
												className="remove-btn"
												onClick={() => onRemoveItem(item.product_id)}
												onKeyDown={(e) =>
													handleKeyDown(e, () => onRemoveItem(item.product_id))
												}
												disabled={loading}
												title="Remove item"
												aria-label={`Remove ${item.name} from cart`}
											>
												<Trash2 size={16} />
											</button>
											{/* TODO: Lab 4a.7 - Add pending indicator for processing items */}

										</div>
									</div>

									<div className="item-total">
										{formatCurrency(item.price * item.quantity)}
									</div>
								</div>
							))}
						</div>

						<div className="cart-summary">
							<div className="summary-line">
								<span>Subtotal:</span>
								<span>{formatCurrency(totalPrice)}</span>
							</div>
							<div className="summary-line">
								<span>Tax (8%):</span>
								<span>{formatCurrency(estimatedTax)}</span>
							</div>
							<div className="summary-line summary-total">
								<span>Total:</span>
								<span>{formatCurrency(estimatedTotal)}</span>
							</div>

							<button
								type="button"
								className="btn btn-success btn-lg checkout-btn"
								onClick={onCheckout}
								onKeyDown={(e) => handleKeyDown(e, onCheckout)}
								disabled={loading || items.length === 0}
								aria-label={`Proceed to checkout with total ${formatCurrency(estimatedTotal)}`}
							>
								{loading ? (
									<span className="spinner"></span>
								) : (
									<CreditCard size={20} />
								)}
								Checkout {formatCurrency(estimatedTotal)}
							</button>
						</div>
					</>
				)}
			</div>
		</div>
	);
};

export default CartSidebar;
