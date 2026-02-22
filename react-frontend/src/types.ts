export interface Product {
	id: string;
	name: string;
	price: number;
	image: string;
	rating: number;
	reviews: number;
	description: string;
	category: string;
}

export interface CartItem {
	product_id: string;
	name: string;
	price: number;
	quantity: number;
	image: string;
}

export interface Cart {
	user_id: string;
	items: CartItem[];
	total_amount: number;
	created_at: string;
	updated_at: string;
}

export interface Customer {
	customer_id: string;
	email: string;
	first_name: string;
	last_name: string;
	address: {
		street: string;
		city: string;
		state: string;
		zip_code: string;
		country: string;
	};
	phone?: string;
}

export interface Order {
	order_id: string;
	customer_id: string;
	items: CartItem[];
	total_amount: number;
	status: string;
	created_at: string;
	shipping_address: Customer["address"];
	billing_address: Customer["address"];
}

export interface OrderData {
	order_id: string;
	customer_id: string;
	total_amount: number;
	status: string;
	created_at?: string;
	fulfillment_tracking?: string;
	email_sent?: boolean;
}

export interface CheckoutRequest {
	user_id: string;
	customer_info: Omit<Customer, "customer_id">;
	payment_method: {
		type: "credit_card";
		card_number: string;
		expiry_month: string;
		expiry_year: string;
		cvv: string;
		cardholder_name: string;
	};
	billing_address: Customer["address"];
	shipping_address: Customer["address"];
}

// TODO: Lab 4a.2 - Add pending field to CartItem interface for optimistic updates
// TODO: Lab 4a.2 - Add CheckoutStatus interface for async checkout status tracking
// TODO: Lab 4a.2 - Add ActiveOrder interface for sidebar progress tracking

