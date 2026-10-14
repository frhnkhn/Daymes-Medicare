package com.daymes.medicare.controller;

import com.daymes.medicare.model.Medicine;
import com.daymes.medicare.service.MedicineService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;

/**
 * REST Controller exposing Daymes Medicare API to Python Web & CLI clients.
 */
@RestController
@RequestMapping("/api/medicines")
@CrossOrigin(origins = "*")
public class MedicineController {

    private final MedicineService medicineService;

    public MedicineController(MedicineService medicineService) {
        this.medicineService = medicineService;
    }

    @GetMapping
    public List<Medicine> getAll() {
        return medicineService.getAllMedicines();
    }

    @PostMapping
    public ResponseEntity<Medicine> create(@RequestBody Medicine medicine) {
        return ResponseEntity.ok(medicineService.addMedicine(medicine));
    }

    @PostMapping("/{id}/take")
    public ResponseEntity<Medicine> dispense(@PathVariable Long id, @RequestBody(required = false) Map<String, Object> payload) {
        int count = payload != null && payload.containsKey("count") ? ((Number) payload.get("count")).intValue() : 1;
        return ResponseEntity.ok(medicineService.dispense(id, count));
    }

    @PostMapping("/{id}/restock")
    public ResponseEntity<Medicine> restock(@PathVariable Long id, @RequestBody(required = false) Map<String, Object> payload) {
        int qty = payload != null && payload.containsKey("quantity") ? ((Number) payload.get("quantity")).intValue() : 30;
        return ResponseEntity.ok(medicineService.restock(id, qty));
    }
}
