package dev.training.elastic;

import java.util.List;

public record ProductSearchResponse(long total, List<ProductHit> products) {
}
