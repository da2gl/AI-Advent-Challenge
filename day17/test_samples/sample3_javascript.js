/**
 * Sample JavaScript code for testing
 * E-commerce shopping cart implementation
 */

class ShoppingCart {
    constructor() {
        this.items = [];
        this.total = 0;
        this.discountRate = 0;
    }

    addItem(product, quantity) {
        const existingItem = this.items.find(item => item.product.id === product.id);

        if (existingItem) {
            existingItem.quantity += quantity;
        } else {
            this.items.push({
                product: product,
                quantity: quantity,
                price: product.price
            });
        }

        this.calculateTotal();
    }

    removeItem(productId) {
        this.items = this.items.filter(item => item.product.id !== productId);
        this.calculateTotal();
    }

    updateQuantity(productId, newQuantity) {
        const item = this.items.find(item => item.product.id === productId);

        if (item) {
            if (newQuantity <= 0) {
                this.removeItem(productId);
            } else {
                item.quantity = newQuantity;
                this.calculateTotal();
            }
        }
    }

    applyDiscount(discountPercentage) {
        if (discountPercentage >= 0 && discountPercentage <= 100) {
            this.discountRate = discountPercentage / 100;
            this.calculateTotal();
        }
    }

    calculateTotal() {
        const subtotal = this.items.reduce((sum, item) => {
            return sum + (item.price * item.quantity);
        }, 0);

        this.total = subtotal * (1 - this.discountRate);
    }

    getItemCount() {
        return this.items.reduce((count, item) => count + item.quantity, 0);
    }

    clear() {
        this.items = [];
        this.total = 0;
        this.discountRate = 0;
    }

    toJSON() {
        return {
            items: this.items,
            total: this.total,
            discountRate: this.discountRate,
            itemCount: this.getItemCount()
        };
    }
}

const formatPrice = (price) => {
    return `$${price.toFixed(2)}`;
};

const calculateTax = (amount, taxRate = 0.08) => {
    return amount * taxRate;
};

// Example usage
const cart = new ShoppingCart();

const product1 = { id: 1, name: 'Laptop', price: 999.99 };
const product2 = { id: 2, name: 'Mouse', price: 29.99 };

cart.addItem(product1, 1);
cart.addItem(product2, 2);
cart.applyDiscount(10);

console.log('Cart total:', formatPrice(cart.total));
console.log('Items:', cart.getItemCount());
