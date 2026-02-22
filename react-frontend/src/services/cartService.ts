import axios from "axios";
import type { Cart, CartItem, CheckoutRequest, OrderData } from "../types";

// Use relative API path - CloudFront will route /api/* to API Gateway
const API_BASE_URL = "/api";

const api = axios.create({
	baseURL: API_BASE_URL,
	headers: {
		"Content-Type": "application/json",
	},
});

export const cartService = {
	// Get user's cart
	async getCart(userId: string): Promise<Cart> {
		const response = await api.get("/cart", {
			headers: {
				"x-user-id": userId,
			},
		});
		return response.data;
	},

	// Create a new cart
	async createCart(userId: string, items: CartItem[] = []): Promise<Cart> {
		const response = await api.post(
			"/cart",
			{ items },
			{
				headers: {
					"x-user-id": userId,
				},
			},
		);
		return response.data;
	},

	// Update cart contents
	async updateCart(userId: string, items: CartItem[]): Promise<Cart> {
		const response = await api.put(
			"/cart",
			{ items },
			{
				headers: {
					"x-user-id": userId,
				},
			},
		);
		return response.data;
	},

	// Clear cart
	async clearCart(userId: string): Promise<void> {
		await api.delete("/cart", {
			headers: {
				"x-user-id": userId,
			},
		});
	},

	// Process checkout - returns full order data for sync flow
	async checkout(checkoutData: CheckoutRequest): Promise<OrderData> {
		const response = await api.post("/checkout", checkoutData, {
			headers: {
				"x-user-id": checkoutData.user_id,
			},
		});
		return response.data;
	},

	// TODO: Lab 4a.3 - Add getCheckoutStatus method for polling async checkout progress


};

// Helper function to format currency
export const formatCurrency = (amount: number): string => {
	return new Intl.NumberFormat("en-US", {
		style: "currency",
		currency: "USD",
	}).format(amount);
};

// Helper function to calculate cart total
export const calculateCartTotal = (items: CartItem[]): number => {
	return items.reduce((total, item) => total + item.price * item.quantity, 0);
};