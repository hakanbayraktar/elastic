package dev.training.elastic;

import co.elastic.clients.elasticsearch.ElasticsearchClient;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class ElasticsearchConfiguration {
    @Bean
    ElasticsearchClient elasticsearchClient(
            @Value("${app.elasticsearch.url:http://localhost:9200}") String url,
            @Value("${app.elasticsearch.api-key:}") String apiKey) {
        return ElasticsearchClient.of(builder -> {
            builder.host(url);
            if (!apiKey.isBlank()) {
                builder.apiKey(apiKey);
            }
            return builder;
        });
    }
}
