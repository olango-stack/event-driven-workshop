import { Plus, Star } from "lucide-react";
import type React from "react";
import { formatCurrency } from "../services/cartService";
import type { Product } from "../types";
import "./ProductGrid.css";

interface ProductGridProps {
	products: Product[];
	onAddToCart: (product: Product) => void;
	loading: boolean;
}

const ProductGrid: React.FC<ProductGridProps> = ({
	products,
	onAddToCart,
	loading,
}) => {
	const handleAddToCart = (product: Product) => {
		onAddToCart(product);
	};

	const handleKeyDown = (event: React.KeyboardEvent, product: Product) => {
		if (event.key === "Enter" || event.key === " ") {
			event.preventDefault();
			handleAddToCart(product);
		}
	};

	const renderStars = (rating: number) => {
		const stars = [];
		const fullStars = Math.floor(rating);
		const hasHalfStar = rating % 1 !== 0;

		for (let i = 0; i < fullStars; i++) {
			stars.push(
				<Star key={i} size={16} fill="currentColor" className="star-filled" />,
			);
		}

		if (hasHalfStar) {
			stars.push(
				<Star key="half" size={16} fill="currentColor" className="star-half" />,
			);
		}

		const emptyStars = 5 - Math.ceil(rating);
		for (let i = 0; i < emptyStars; i++) {
			stars.push(<Star key={`empty-${i}`} size={16} className="star-empty" />);
		}

		return stars;
	};

	return (
		<div className="product-grid">
			{products.map((product) => (
				<div key={product.id} className="product-card">
					<div className="product-image-container">
						<img
							src={product.image}
							alt={product.name}
							className="product-image"
							loading="lazy"
						/>
						<button
							type="button"
							className="add-to-cart-overlay"
							onClick={() => handleAddToCart(product)}
							onKeyDown={(e) => handleKeyDown(e, product)}
							disabled={loading}
							aria-label={`Add ${product.name} to cart`}
						>
							<Plus size={20} />
							Add to Cart
						</button>
					</div>

					<div className="product-info">
						<div className="product-category">{product.category}</div>
						<h3 className="product-name">{product.name}</h3>
						<p className="product-description">{product.description}</p>

						<div className="product-rating">
							<div className="stars">{renderStars(product.rating)}</div>
							<span className="rating-text">
								{product.rating} ({product.reviews.toLocaleString()})
							</span>
						</div>

						<div className="product-footer">
							<div className="product-price">
								{formatCurrency(product.price)}
							</div>
							<button
								type="button"
								className="btn btn-primary btn-sm add-to-cart-btn"
								onClick={() => handleAddToCart(product)}
								onKeyDown={(e) => handleKeyDown(e, product)}
								disabled={loading}
								aria-label={`Add ${product.name} to cart`}
							>
								{loading ? (
									<span className="spinner"></span>
								) : (
									<Plus size={16} />
								)}
								Add to Cart
							</button>
						</div>
					</div>
				</div>
			))}
		</div>
	);
};

export default ProductGrid;
