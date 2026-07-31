package com.sc.pesticideknowledgemappingsystem.service;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
public class NewAnswerServiceTest {

    @Autowired
    private NewAnswerService newAnswerService;

    @Autowired
    private PesticideService pesticideService;
    @Autowired
    private ActiveSubstanceService activeSubstanceService;
    @Autowired
    private DiseaseService diseaseService;

    @BeforeEach
    public void setup() {
        // Ensure that all services are properly configured and can be accessed
        // You can optionally add any setup or initialization code here if needed
    }

    @Test
    public void testBayes() {
        // Define test case with input sentence
        String querySentence1 = "I need to know the methods of prevention and treatment of brown spot.";

        // Test the Bayes method with the input
        String result1 = newAnswerService.Bayes(querySentence1);

        // Print the result to see the actual output
        System.out.println("问题答案："+result1);

        // You can optionally add assertions if you know the expected result
        // assertEquals("Expected Result", result1);
    }
}
