package dev.training.elastic;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.math.BigDecimal;
import java.util.List;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Import;
import org.springframework.context.annotation.Primary;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(ProductSearchController.class)
@Import(ProductSearchControllerTest.StubConfiguration.class)
class ProductSearchControllerTest {
    @Autowired MockMvc mvc;

    @Test
    void searchReturnsTheTypedProductResults() throws Exception {
        mvc.perform(get("/api/products/search")
                        .param("q", "kulaklık")
                        .param("category", "electronics")
                        .param("size", "5"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.total").value(1))
                .andExpect(jsonPath("$.products[0].id").value("p-100"))
                .andExpect(jsonPath("$.products[0].highlights[0]").value("<em>Kulaklık</em> Pro"));
    }

    @Test
    void rejectsBlankQueriesAndOversizedPageSizes() throws Exception {
        mvc.perform(get("/api/products/search").param("q", " "))
                .andExpect(status().isBadRequest());
        mvc.perform(get("/api/products/search").param("q", "telefon").param("size", "21"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void suggestReturnsTheCompletionMatches() throws Exception {
        mvc.perform(get("/api/products/suggest").param("q", "akıl").param("size", "3"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].id").value("p-101"))
                .andExpect(jsonPath("$[0].name").value("Akıllı Saat Active"));
    }

    @TestConfiguration
    static class StubConfiguration {
        @Bean
        @Primary
        ProductSearchService productSearchService() {
            return new ProductSearchService(null, "products-v1") {
                @Override
                ProductSearchResponse search(String query, String category, int size) {
                    return new ProductSearchResponse(1, List.of(new ProductHit(
                            "p-100", "Kablosuz Kulaklık Pro", "NovaSound", "electronics",
                            new BigDecimal("2499.90"), 4.2, List.of("<em>Kulaklık</em> Pro"))));
                }

                @Override
                List<ProductHit> suggest(String prefix, int size) {
                    return List.of(new ProductHit("p-101", "Akıllı Saat Active", "NovaTech",
                            "electronics", new BigDecimal("3299.00"), 2.1, List.of()));
                }
            };
        }
    }
}
