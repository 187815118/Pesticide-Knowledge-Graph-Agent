package com.sc.pesticideknowledgemappingsystem.service;

import com.sc.pesticideknowledgemappingsystem.entity.relationship.DiseaseRelationship;
import com.sc.pesticideknowledgemappingsystem.entity.relationship.PesticideCropRelationship;
import com.sc.pesticideknowledgemappingsystem.entity.relationship.PesticideDiseaseRelationship;
import com.sc.pesticideknowledgemappingsystem.repository.relationship.DiseaseRelationshipRepository;
import com.sc.pesticideknowledgemappingsystem.repository.relationship.PesticideCropRelationshipRepository;
import com.sc.pesticideknowledgemappingsystem.repository.relationship.PesticideDiseaseRelationshipRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.*;

@Service
public class NodeInfoService {
    @Autowired
    private PesticideCropRelationshipRepository pesticideCropRelationshipRepository;
    @Autowired
    private PesticideDiseaseRelationshipRepository pesticideDiseaseRelationshipRepository;
    @Autowired
    private DiseaseRelationshipRepository diseaseRelationshipRepository;

    public Map<String, String> getKnowledgeGraphByPesticideName(String pesticideName) {
        List<PesticideCropRelationship> pesticideCropRelationships = pesticideCropRelationshipRepository.findRelationshipsByPesticideName(pesticideName);
        List<PesticideDiseaseRelationship> pesticideDiseaseRelationships = pesticideDiseaseRelationshipRepository.findRelationshipsByPesticideName(pesticideName);

        Map<String, String> knowledgeGraph = new HashMap<>();
        Set<String> disease = new HashSet<>(); // Set 用于存储已经添加的键

        for (PesticideCropRelationship pesticideCropRelationship : pesticideCropRelationships) {
            String cropName = pesticideCropRelationship.getCrop().getName();

            for (PesticideDiseaseRelationship pesticideDiseaseRelationship : pesticideDiseaseRelationships) {
                List<DiseaseRelationship> diseaseRelationships = diseaseRelationshipRepository.findRelationshipsByDiseaseName(pesticideDiseaseRelationship.getDisease().getName());

                for (DiseaseRelationship diseaseRelationship : diseaseRelationships) {
                    if (diseaseRelationship.getCrop().getName().equals(cropName)) {
                        String diseaseName = diseaseRelationship.getDisease().getName();

                        // 检查键是否已经存在于 Set 中
                        if (!disease.contains(diseaseName)) {
                            knowledgeGraph.put(diseaseName, cropName);
                            // 将键添加到 Set 中
                            disease.add(diseaseName);
                        }

                        knowledgeGraph.put(diseaseName, cropName);
                    }
                }
            }
        }

        return knowledgeGraph;
    }


}
