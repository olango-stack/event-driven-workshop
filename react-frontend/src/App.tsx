import { useCallback, useEffect, useState } from "react";

import { v4 as uuidv4 } from "uuid";

import CartSidebar from "./components/CartSidebar";
import CheckoutModal from "./components/CheckoutModal";
import ProductGrid from "./components/ProductGrid";
import QRCodeModal from "./components/QRCodeModal";
import ToastContainer from "./components/ToastContainer";
import { useToast } from "./hooks/useToast";
import { cartService } from "./services/cartService";
import type { CartItem, Product } from "./types";
import "./App.css";

// TODO: Lab 4a.5 - Import CheckoutProgressSidebar component
// TODO: Lab 4a.5 - Import ActiveOrder type for sidebar progress tracking



// 4 NEW magical unicorn products with AI-generated images
const PRODUCTS: Product[] = [
	{
		id: "5",
		name: "Starlight Unicorn Grooming Kit",
		price: 39.99,
		image: "/product-images/starlight-grooming-kit.png",
		rating: 4.9,
		reviews: 1523,
		description:
			"Professional grooming set with enchanted brushes, shimmering mane detangler, and magical hoof polish. Keeps your unicorn looking radiant and ready for any adventure.",
		category: "Pet Care & Grooming",
	},
	{
		id: "6",
		name: "Crystal Horn Protector Shield",
		price: 28.99,
		image: "/product-images/crystal-horn-protector.png",
		rating: 4.7,
		reviews: 967,
		description:
			"Protective crystal shield that fits perfectly over unicorn horns. Made from enchanted quartz that amplifies magical powers while preventing horn damage during play.",
		category: "Safety & Protection",
	},
	{
		id: "7",
		name: "Rainbow Bridge Feeding Bowl",
		price: 22.99,
		image: "/product-images/rainbow-feeding-bowl.png",
		rating: 4.6,
		reviews: 1234,
		description:
			"Magical feeding bowl that creates rainbow bridges when filled with unicorn treats. Made from celestial materials that keep food fresh and add nutritional sparkles.",
		category: "Feeding & Nutrition",
	},
	{
		id: "8",
		name: "Moonbeam Unicorn Blanket",
		price: 45.99,
		image: "/product-images/moonbeam-blanket.png",
		rating: 4.8,
		reviews: 1876,
		description:
			"Ultra-soft blanket woven from moonbeams and stardust. Provides warmth during cold nights and glows softly to comfort unicorns during thunderstorms.",
		category: "Comfort & Bedding",
	},
];

function App() {
	const [cartItems, setCartItems] = useState<CartItem[]>([]);
	const [showCheckout, setShowCheckout] = useState(false);
	const [showQRModal, setShowQRModal] = useState(false);
	const [userId] = useState<string>(() => {
		let id = localStorage.getItem("userId");
		if (!id) {
			id = uuidv4();
			localStorage.setItem("userId", id);
		}
		return id;
	});
	const [loading, setLoading] = useState(false);
	const { toasts, removeToast, showSuccess, showError } = useToast();

	// TODO: Lab 4a.5 - Add pending operations state for optimistic updates
	// TODO: Lab 4a.5 - Add active orders state for sidebar progress tracking
	// TODO: Lab 4a.5 - Add showProgressSidebar state
	


	const loadCart = useCallback(async () => {
		try {
			setLoading(true);
			const cart = await cartService.getCart(userId);
			setCartItems(cart.items || []);
		} catch (error) {
			console.error("Failed to load cart:", error);
			setCartItems([]);
		} finally {
			setLoading(false);
		}
	}, [userId]);

	// Load cart on component mount
	useEffect(() => {
		loadCart();
	}, [loadCart]);

	const addToCart = async (product: Product) => {
		const existingItem = cartItems.find(
			(item) => item.product_id === product.id,
		);

		try {
			setLoading(true);
			let updatedItems: CartItem[];
			if (existingItem) {
				updatedItems = cartItems.map((item) =>
					item.product_id === product.id
						? { ...item, quantity: item.quantity + 1 }
						: item,
				);
			} else {
				const newItem: CartItem = {
					product_id: product.id,
					name: product.name,
					price: product.price,
					quantity: 1,
					image: product.image,
				};
				updatedItems = [...cartItems, newItem];
			}

			await cartService.updateCart(userId, updatedItems);
			setCartItems(updatedItems);
			showSuccess(`${product.name} added to cart!`);
		} catch (error) {
			console.error("Failed to add to cart:", error);
			showError("Failed to add item to cart. Please try again.");
		} finally {
			setLoading(false);
		}
	};

	const updateCartItem = async (productId: string, quantity: number) => {
		try {
			setLoading(true);
			let updatedItems: CartItem[];
			if (quantity <= 0) {
				updatedItems = cartItems.filter(
					(item) => item.product_id !== productId,
				);
			} else {
				updatedItems = cartItems.map((item) =>
					item.product_id === productId
						? { ...item, quantity }
						: item,
				);
			}

			await cartService.updateCart(userId, updatedItems);
			setCartItems(updatedItems);
			showSuccess("Cart updated successfully!");
		} catch (error) {
			console.error("Failed to update cart:", error);
			showError("Failed to update cart. Please try again.");
		} finally {
			setLoading(false);
		}
	};

	const removeFromCart = async (productId: string) => {
		try {
			setLoading(true);
			const updatedItems = cartItems.filter(
				(item) => item.product_id !== productId,
			);
			await cartService.updateCart(userId, updatedItems);
			setCartItems(updatedItems);
			showSuccess("Item removed from cart!");
		} catch (error) {
			console.error("Failed to remove from cart:", error);
			showError("Failed to remove item from cart. Please try again.");
		} finally {
			setLoading(false);
		}
	};

	const clearCart = async () => {
		try {
			setLoading(true);
			await cartService.clearCart(userId);
			setCartItems([]);
			showSuccess("Cart cleared successfully!");
		} catch (error) {
			console.error("Failed to clear cart:", error);
			showError("Failed to clear cart. Please try again.");
		} finally {
			setLoading(false);
		}
	};

	const getTotalPrice = () => {
		return cartItems.reduce(
			(total, item) => total + item.price * item.quantity,
			0,
		);
	};



	const handleCheckoutComplete = () => {
		setCartItems([]);
		setShowCheckout(false);
	};

	// TODO: Lab 4a.5 - Add handleOrderSubmitted function for async checkout flow
	// TODO: Lab 4a.5 - Add pollOrderStatus function for progress tracking
	// TODO: Lab 4a.5 - Add getStatusMessage helper function
	// TODO: Lab 4a.5 - Add handleDismissOrder function for sidebar management

	return (
		<div className="app">
			<header className="app-header">
				<div className="container">
					<button
						type="button"
						className="logo clickable-title"
						onClick={() => setShowQRModal(true)}
						onKeyDown={(e) => {
							if (e.key === "Enter" || e.key === " ") {
								e.preventDefault();
								setShowQRModal(true);
							}
						}}
						title="Click to share this page"
					>
						CNS203: Unicorn Dreams Store
					</button>
					<p className="tagline">Where Magic Meets Shopping</p>
				</div>
			</header>

			<main className="app-main">
				<div className="container">
					<div className="main-content">
						<div className="products-section">
							<h2>Magical Unicorn Collection</h2>
							<ProductGrid
								products={PRODUCTS}
								onAddToCart={addToCart}
								loading={loading}
							/>
						</div>

						<CartSidebar
							items={cartItems}
							onUpdateQuantity={updateCartItem}
							onRemoveItem={removeFromCart}
							onClearCart={clearCart}
							onCheckout={() => setShowCheckout(true)}
							totalPrice={getTotalPrice()}
							loading={loading}
						/>
					</div>
				</div>
			</main>

			{/* TODO: Lab 4a.6 - Add onOrderSubmitted prop to CheckoutModal for async flow */}
			{showCheckout && (
				<CheckoutModal
					items={cartItems}
					totalPrice={getTotalPrice()}
					userId={userId}
					onClose={() => setShowCheckout(false)}
					onCheckoutComplete={handleCheckoutComplete}
					showError={showError}
				/>
			)}

			{/* TODO: Lab 4a.5 - Add CheckoutProgressSidebar component */}

			<QRCodeModal isOpen={showQRModal} onClose={() => setShowQRModal(false)} />

			<ToastContainer toasts={toasts} onRemoveToast={removeToast} />
		</div>
	);
}

export default App;
