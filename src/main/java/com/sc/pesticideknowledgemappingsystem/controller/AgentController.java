package com.sc.pesticideknowledgemappingsystem.controller;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;

@Controller
public class AgentController {

    private static final int CONNECT_TIMEOUT_MS = 5000;
    private static final int READ_TIMEOUT_MS = 90000;

    @Value("${agent.api.base-url:${AGENT_API_BASE_URL:http://127.0.0.1:8001}}")
    private String agentApiBaseUrl;

    @PostMapping("/api/agent/query")
    @ResponseBody
    public ResponseEntity<Map<String, Object>> queryAgent(@RequestBody Map<String, Object> requestBody) {
        if (requestBody == null) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse("question must be a non-empty string"));
        }

        Object rawQuestion = requestBody.get("question");
        if (!(rawQuestion instanceof String) || ((String) rawQuestion).trim().isEmpty()) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse("question must be a non-empty string"));
        }

        Map<String, Object> agentRequest = new HashMap<>();
        agentRequest.put("question", ((String) rawQuestion).trim());

        try {
            ResponseEntity<Map> agentResponse = restTemplate().postForEntity(
                    agentApiBaseUrl + "/agent/query",
                    agentRequest,
                    Map.class
            );
            Map<String, Object> responseBody = new HashMap<>();
            if (agentResponse.getBody() != null) {
                responseBody.putAll(agentResponse.getBody());
            }
            return ResponseEntity.status(agentResponse.getStatusCode()).body(responseBody);
        } catch (HttpStatusCodeException exc) {
            return ResponseEntity.status(HttpStatus.BAD_GATEWAY).body(errorResponse("Agent service unavailable"));
        } catch (ResourceAccessException exc) {
            return ResponseEntity.status(HttpStatus.BAD_GATEWAY).body(errorResponse("Agent service unavailable"));
        } catch (RestClientException exc) {
            return ResponseEntity.status(HttpStatus.BAD_GATEWAY).body(errorResponse("Agent service unavailable"));
        }
    }

    private RestTemplate restTemplate() {
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout(CONNECT_TIMEOUT_MS);
        requestFactory.setReadTimeout(READ_TIMEOUT_MS);
        return new RestTemplate(requestFactory);
    }

    private Map<String, Object> errorResponse(String message) {
        Map<String, Object> response = new HashMap<>();
        response.put("error", message);
        return response;
    }
}
