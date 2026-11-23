package dev.training.elastic;

import java.math.BigDecimal;
import java.util.List;

public record ProductHit(
        String id,
        String name,
        String brand,
        String category,
        BigDecimal price,
        Double score,
        List<String> highlights) {
}
