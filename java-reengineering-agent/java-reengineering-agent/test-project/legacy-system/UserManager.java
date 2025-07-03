package com.example.legacy;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

/**
 * God Class - handles everything related to users
 * This is a classic example of what needs reengineering
 */
public class UserManager {
    
    private Connection connection;
    private List<User> users = new ArrayList<>();
    
    // Database connection handling
    public void connectToDatabase() throws SQLException {
        connection = DriverManager.getConnection(
            "jdbc:mysql://localhost:3306/legacy_db", 
            "user", 
            "password"
        );
    }
    
    // User CRUD operations
    public void createUser(String name, String email, String password) {
        // Validation logic mixed with business logic
        if (name == null || name.isEmpty()) {
            throw new IllegalArgumentException("Name cannot be empty");
        }
        
        if (!email.contains("@")) {
            throw new IllegalArgumentException("Invalid email");
        }
        
        // Password hashing (insecure)
        String hashedPassword = password + "_hashed";
        
        User user = new User(name, email, hashedPassword);
        users.add(user);
        
        // Send email notification (tight coupling)
        sendWelcomeEmail(email);
        
        // Log audit trail
        System.out.println("User created: " + name);
    }
    
    public User findUser(String email) {
        for (User user : users) {
            if (user.getEmail().equals(email)) {
                return user;
            }
        }
        return null;
    }
    
    public void updateUser(String email, String newName) {
        User user = findUser(email);
        if (user != null) {
            user.setName(newName);
            System.out.println("User updated: " + email);
        }
    }
    
    public void deleteUser(String email) {
        User user = findUser(email);
        if (user != null) {
            users.remove(user);
            System.out.println("User deleted: " + email);
        }
    }
    
    // Email service (should be separate)
    private void sendWelcomeEmail(String email) {
        System.out.println("Sending welcome email to: " + email);
        // Complex email logic here...
    }
    
    // Payment processing (wrong place!)
    public void processPayment(String userEmail, double amount) {
        User user = findUser(userEmail);
        if (user != null) {
            // Payment logic
            System.out.println("Processing payment of $" + amount + " for " + userEmail);
            
            // Update user balance
            user.setBalance(user.getBalance() + amount);
        }
    }
    
    // Report generation (also wrong place!)
    public void generateUserReport() {
        System.out.println("=== USER REPORT ===");
        for (User user : users) {
            System.out.println(user.getName() + " - " + user.getEmail() + " - $" + user.getBalance());
        }
    }
    
    // Static class for User
    public static class User {
        private String name;
        private String email;
        private String password;
        private double balance;
        
        public User(String name, String email, String password) {
            this.name = name;
            this.email = email;
            this.password = password;
            this.balance = 0.0;
        }
        
        // Getters and setters
        public String getName() { return name; }
        public void setName(String name) { this.name = name; }
        
        public String getEmail() { return email; }
        public void setEmail(String email) { this.email = email; }
        
        public String getPassword() { return password; }
        public void setPassword(String password) { this.password = password; }
        
        public double getBalance() { return balance; }
        public void setBalance(double balance) { this.balance = balance; }
    }
}
