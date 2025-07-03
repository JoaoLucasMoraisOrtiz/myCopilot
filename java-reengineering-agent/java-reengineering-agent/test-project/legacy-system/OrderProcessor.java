package com.example.legacy;

import java.util.List;
import java.util.ArrayList;

/**
 * Another problematic class with mixed responsibilities
 */
public class OrderProcessor {
    
    private UserManager userManager;
    private List<Order> orders = new ArrayList<>();
    
    public OrderProcessor(UserManager userManager) {
        this.userManager = userManager;
    }
    
    // Order processing with business logic scattered
    public void processOrder(String userEmail, String product, double price) {
        // Validation
        if (price < 0) {
            throw new IllegalArgumentException("Price cannot be negative");
        }
        
        // Find user (tight coupling)
        UserManager.User user = userManager.findUser(userEmail);
        if (user == null) {
            throw new IllegalArgumentException("User not found");
        }
        
        // Check balance (business rule)
        if (user.getBalance() < price) {
            throw new IllegalStateException("Insufficient balance");
        }
        
        // Create order
        Order order = new Order(userEmail, product, price);
        orders.add(order);
        
        // Update user balance (should be in a transaction)
        user.setBalance(user.getBalance() - price);
        
        // Send confirmation (mixed responsibility)
        sendOrderConfirmation(userEmail, order);
        
        // Update inventory (tight coupling)
        updateInventory(product);
        
        // Generate invoice (wrong place)
        generateInvoice(order);
    }
    
    private void sendOrderConfirmation(String email, Order order) {
        System.out.println("Order confirmation sent to: " + email);
    }
    
    private void updateInventory(String product) {
        System.out.println("Inventory updated for: " + product);
    }
    
    private void generateInvoice(Order order) {
        System.out.println("Invoice generated for order: " + order.getId());
    }
    
    // Simple Order class
    public static class Order {
        private static int nextId = 1;
        private int id;
        private String userEmail;
        private String product;
        private double price;
        
        public Order(String userEmail, String product, double price) {
            this.id = nextId++;
            this.userEmail = userEmail;
            this.product = product;
            this.price = price;
        }
        
        public int getId() { return id; }
        public String getUserEmail() { return userEmail; }
        public String getProduct() { return product; }
        public double getPrice() { return price; }
    }
}
