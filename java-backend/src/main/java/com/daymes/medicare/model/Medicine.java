package com.daymes.medicare.model;

import jakarta.persistence.*;
import java.time.LocalDate;

/**
 * APP Project - Daymes Medicare Enterprise
 * Core Entity representing medical inventory item.
 */
@Entity
@Table(name = "medicines")
public class Medicine {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String name;

    @Column(nullable = false)
    private Integer stockQuantity;

    @Column(nullable = false)
    private Integer dailyUsage;

    private Boolean autoReordered = false;

    private String expirationDate;

    private String supplier;

    private String orderStatus = "none";

    private String expectedDelivery;

    private Double unitPrice = 15.0;

    private String category = "General";

    private String batchNumber;

    // Constructors
    public Medicine() {}

    public Medicine(String name, Integer stockQuantity, Integer dailyUsage, String supplier, String expirationDate) {
        this.name = name;
        this.stockQuantity = stockQuantity;
        this.dailyUsage = dailyUsage;
        this.supplier = supplier;
        this.expirationDate = expirationDate;
    }

    // Business Logic Methods
    public boolean isCriticallyLow() {
        if (dailyUsage == null || dailyUsage <= 0) return false;
        return (stockQuantity / dailyUsage) <= 3;
    }

    public void dispense(int units) {
        this.stockQuantity = Math.max(0, this.stockQuantity - units);
    }

    public void restock(int units) {
        this.stockQuantity += units;
        this.autoReordered = false;
        this.orderStatus = "none";
        this.expectedDelivery = null;
    }

    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public Integer getStockQuantity() { return stockQuantity; }
    public void setStockQuantity(Integer stockQuantity) { this.stockQuantity = stockQuantity; }

    public Integer getDailyUsage() { return dailyUsage; }
    public void setDailyUsage(Integer dailyUsage) { this.dailyUsage = dailyUsage; }

    public Boolean getAutoReordered() { return autoReordered; }
    public void setAutoReordered(Boolean autoReordered) { this.autoReordered = autoReordered; }

    public String getExpirationDate() { return expirationDate; }
    public void setExpirationDate(String expirationDate) { this.expirationDate = expirationDate; }

    public String getSupplier() { return supplier; }
    public void setSupplier(String supplier) { this.supplier = supplier; }

    public String getOrderStatus() { return orderStatus; }
    public void setOrderStatus(String orderStatus) { this.orderStatus = orderStatus; }

    public String getExpectedDelivery() { return expectedDelivery; }
    public void setExpectedDelivery(String expectedDelivery) { this.expectedDelivery = expectedDelivery; }

    public Double getUnitPrice() { return unitPrice; }
    public void setUnitPrice(Double unitPrice) { this.unitPrice = unitPrice; }

    public String getCategory() { return category; }
    public void setCategory(String category) { this.category = category; }

    public String getBatchNumber() { return batchNumber; }
    public void setBatchNumber(String batchNumber) { this.batchNumber = batchNumber; }
}
