package dev.training.elastic;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import java.io.IOException;
import java.util.List;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@Validated
@RestController
@RequestMapping("/api/products")
public class ProductSearchController {
    private final ProductSearchService searchService;

    ProductSearchController(ProductSearchService searchService) {
        this.searchService = searchService;
    }

    @GetMapping("/search")
    ProductSearchResponse search(
            @RequestParam @NotBlank @Size(max = 120) String q,
            @RequestParam(required = false) @Size(max = 40) String category,
            @RequestParam(defaultValue = "10") @Min(1) @Max(20) int size) throws IOException {
        return searchService.search(q.trim(), category, size);
    }

    @GetMapping("/suggest")
    List<ProductHit> suggest(
            @RequestParam @NotBlank @Size(max = 80) String q,
            @RequestParam(defaultValue = "5") @Min(1) @Max(10) int size) throws IOException {
        return searchService.suggest(q.trim(), size);
    }
}
