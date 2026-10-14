package com.daymes.medicare.service;

import com.daymes.medicare.model.Medicine;
import org.springframework.stereotype.Service;
import java.time.LocalDate;
import java.util.*;

/**
 * Service handling inventory threshold calculations and auto-procurement logic.
 */
@Service
public class MedicineService {

    private final Map<Long, Medicine> repository = new HashMap<>();

    public List<Medicine> getAllMedicines() {
        return new ArrayList<>(repository.values());
    }

    public Medicine addMedicine(Medicine med) {
        if (med.getId() == null) {
            med.setId((long) (repository.size() + 1));
        }
        repository.put(med.getId(), med);
        return med;
    }

    /**
     * Dispenses units and evaluates the 3-day critical buffer threshold.
     * Triggers automated supply order if stock falls below critical level.
     */
    public Medicine dispense(Long id, int count) {
        Medicine med = repository.get(id);
        if (med == null) throw new RuntimeException("Medicine not found with id: " + id);

        med.dispense(count);

        // Core APP Algorithm: Critical Buffer Trigger
        if (med.isCriticallyLow() && !med.getAutoReordered()) {
            med.setAutoReordered(true);
            med.setOrderStatus("ordered");
            med.setExpectedDelivery(LocalDate.now().plusDays(2).toString());
        }

        return med;
    }

    public Medicine restock(Long id, int quantity) {
        Medicine med = repository.get(id);
        if (med == null) throw new RuntimeException("Medicine not found with id: " + id);
        med.restock(quantity);
        return med;
    }
}
