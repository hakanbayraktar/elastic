package dev.training.elastic;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.math.BigDecimal;
import java.util.List;

public record ProductDocument(
        @JsonProperty("product_id") String productId,
        String name,
        String description,
        String brand,
        String category,
        @JsonProperty("in_stock") Boolean inStock,
        BigDecimal price,
        String release_date,
        List<String> tags) {
}
