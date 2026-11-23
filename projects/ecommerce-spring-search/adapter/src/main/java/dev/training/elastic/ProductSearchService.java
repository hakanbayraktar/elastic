package dev.training.elastic;

import co.elastic.clients.elasticsearch.ElasticsearchClient;
import co.elastic.clients.elasticsearch._types.query_dsl.Query;
import co.elastic.clients.elasticsearch._types.query_dsl.TextQueryType;
import co.elastic.clients.elasticsearch.core.SearchResponse;
import co.elastic.clients.elasticsearch.core.search.HighlightField;
import co.elastic.clients.elasticsearch.core.search.Hit;
import co.elastic.clients.util.NamedValue;
import java.io.IOException;
import java.util.List;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class ProductSearchService {
    private final ElasticsearchClient client;
    private final String index;

    ProductSearchService(ElasticsearchClient client,
                         @Value("${app.elasticsearch.product-index:ecommerce-products-v1}") String index) {
        this.client = client;
        this.index = index;
    }

    ProductSearchResponse search(String text, String category, int size) throws IOException {
        Query query = Query.of(q -> q.bool(b -> {
            b.must(m -> m.multiMatch(mm -> mm
                    .query(text)
                    .fields("name^3", "description")
                    .fuzziness("AUTO")));
            b.filter(f -> f.term(t -> t.field("in_stock").value(true)));
            if (category != null && !category.isBlank()) {
                b.filter(f -> f.term(t -> t.field("category").value(category)));
            }
            return b;
        }));

        SearchResponse<ProductDocument> response = client.search(s -> s
                        .index(index)
                        .size(size)
                        .timeout("2s")
                        .query(query)
                        .highlight(h -> h.fields(NamedValue.of("name", HighlightField.of(field -> field)))),
                ProductDocument.class);
        if (response.timedOut()) {
            throw new IOException("Product search timed out");
        }
        List<ProductHit> products = response.hits().hits().stream()
                .map(ProductSearchService::toHit)
                .toList();
        long total = response.hits().total() == null
                ? products.size()
                : response.hits().total().value();
        return new ProductSearchResponse(total, products);
    }

    List<ProductHit> suggest(String prefix, int size) throws IOException {
        Query query = Query.of(q -> q.multiMatch(m -> m
                .query(prefix)
                .type(TextQueryType.BoolPrefix)
                .fields("name")));
        SearchResponse<ProductDocument> response = client.search(s -> s
                        .index(index)
                        .size(size)
                        .timeout("2s")
                        .query(q -> q.bool(b -> b
                                .must(query)
                                .filter(f -> f.term(t -> t.field("in_stock").value(true))))),
                ProductDocument.class);
        if (response.timedOut()) {
            throw new IOException("Product suggestions timed out");
        }
        return response.hits().hits().stream().map(ProductSearchService::toHit).toList();
    }

    private static ProductHit toHit(Hit<ProductDocument> hit) {
        ProductDocument product = hit.source();
        List<String> highlights = hit.highlight().getOrDefault("name", List.of());
        if (product == null) {
            return new ProductHit(hit.id(), null, null, null, null, hit.score(), highlights);
        }
        return new ProductHit(hit.id(), product.name(), product.brand(), product.category(),
                product.price(), hit.score(), highlights);
    }
}
