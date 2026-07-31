package com.sc.pesticideknowledgemappingsystem.service;

import com.sc.pesticideknowledgemappingsystem.entity.node.Disease;
import com.sc.pesticideknowledgemappingsystem.entity.relationship.DiseaseRelationship;
import com.sc.pesticideknowledgemappingsystem.entity.relationship.PesticideDiseaseRelationship;
import com.sc.pesticideknowledgemappingsystem.repository.node.DiseaseRepository;
import com.sc.pesticideknowledgemappingsystem.repository.relationship.DiseaseRelationshipRepository;
import com.sc.pesticideknowledgemappingsystem.repository.relationship.PesticideDiseaseRelationshipRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class DiseaseService {
    @Autowired
    private PesticideDiseaseRelationshipRepository pesticideDiseaseRelationshipRepository;
    @Autowired
    private DiseaseRelationshipRepository diseaseRelationshipRepository;
    @Autowired
    private DiseaseRepository diseaseRepository;

    //从农药查找对应的病害
    public String findPesticidesByDiseaseName(String diseaseName) {
        List<PesticideDiseaseRelationship> relationships = pesticideDiseaseRelationshipRepository.findByDiseaseName(diseaseName);
        if (relationships.isEmpty()) {
            return "No pesticides found for disease: " + diseaseName;
        } else {
            StringBuilder result = new StringBuilder("Pesticides that can prevent " + diseaseName + ": ");
            for (int i = 0; i < relationships.size(); i++) {
                result.append(i + 1).append("、").append(relationships.get(i).getPesticide().getName());
                if (i < relationships.size() - 1) {
                    result.append(", ");
                }
            }
            return result.toString();
        }
    }

    public String findCropsByDiseaseName(String diseaseName) {
        List<DiseaseRelationship> relationships = diseaseRelationshipRepository.findRelationshipsByDiseaseName(diseaseName);
        if (relationships.isEmpty()) {
            return "No crops found for disease: " + diseaseName;
        } else {
            StringBuilder result = new StringBuilder("Crops that can be infect for " + diseaseName + ": ");
            for (int i = 0; i < relationships.size(); i++) {
                result.append(i + 1).append("、").append(relationships.get(i).getCrop().getName());
                if (i < relationships.size() - 1) {
                    result.append(", ");
                }
            }
            return result.toString();
        }
    }


    public String findDiseasesByCropName(String cropName) {
        List<DiseaseRelationship> relationships = diseaseRelationshipRepository.findRelationshipsByCropName(cropName);
        if (relationships.isEmpty()) {
            return "No diseases found that can affect " + cropName;
        } else {
            StringBuilder result = new StringBuilder(cropName + " may be affected by the following diseases: ");
            for (int i = 0; i < relationships.size(); i++) {
                result.append(i + 1).append("、").append(relationships.get(i).getDisease().getName());
                if (i < relationships.size() - 1) {
                    result.append(", ");
                }
            }
            return result.toString();
        }
    }

    //获取病虫害指定属性
    public String getDiseaseProperty(String diseaseName, String propertyName) {
        List<Disease> diseases = diseaseRepository.findByName(diseaseName);
        if (diseases.isEmpty()) {
            return "The specified disease or pest was not found.";
        }
        Disease Disease = diseases.get(0);
        String propertyValue = null;
        switch (propertyName) {
            case "name":
                propertyValue = Disease.getName();
                break;
            case "latin name":
                propertyValue = Disease.getLatinName();
                break;
            case "disease and pest alias":
                propertyValue = Disease.getDiseaseAndPestAlias();
                break;
            case "disease and pest infestation images":
                propertyValue = Disease.getDiseaseAndPestInfestationImages();
                break;
            case "symptoms of infestation":
                propertyValue = Disease.getSymptomsOfInfestation();
                break;
            case "pathogen":
                propertyValue = Disease.getPathogen();
                break;
            case "transmission routes and pathogenic conditions":
                propertyValue = Disease.getTransmissionRoutesAndPathogenicConditions();
                break;
            case "regular pattern of occurrence":
                propertyValue = Disease.getRegularPatternOfOccurrence();
                break;
            case "morphological characteristics":
                propertyValue = Disease.getMorphologicalCharacteristics();
                break;
            case "geographic distribution":
                propertyValue = Disease.getGeographicDistribution();
                break;
            case "host":
                propertyValue = Disease.getHost();
                break;
            case "methods of prevention and treatment":
                propertyValue = Disease.getMethodsOfPreventionAndTreatment();
                break;
            case "others":
                propertyValue = Disease.getOthers();
                break;
            default:
                return "Invalid property name.";
        }
        return propertyValue;
    }

}
