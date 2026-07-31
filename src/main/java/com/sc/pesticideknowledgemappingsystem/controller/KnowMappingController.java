package com.sc.pesticideknowledgemappingsystem.controller;

import com.sc.pesticideknowledgemappingsystem.entity.dto.PreventsDto;
import com.sc.pesticideknowledgemappingsystem.entity.node.Crop;
import com.sc.pesticideknowledgemappingsystem.entity.node.Disease;
import com.sc.pesticideknowledgemappingsystem.entity.node.Pesticide;
import com.sc.pesticideknowledgemappingsystem.entity.relationship.DiseaseRelationship;
import com.sc.pesticideknowledgemappingsystem.entity.relationship.PesticideCropRelationship;
import com.sc.pesticideknowledgemappingsystem.entity.relationship.PesticideCropRelationshipJapan;
import com.sc.pesticideknowledgemappingsystem.entity.relationship.PesticideDiseaseRelationship;
import com.sc.pesticideknowledgemappingsystem.repository.node.PesticideRepository;
import com.sc.pesticideknowledgemappingsystem.repository.relationship.DiseaseRelationshipRepository;
import com.sc.pesticideknowledgemappingsystem.repository.relationship.PesticideCropRelationshipRepository;
import com.sc.pesticideknowledgemappingsystem.repository.relationship.PesticideDiseaseRelationshipRepository;
import com.sc.pesticideknowledgemappingsystem.service.GraphService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;


import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Controller
@CrossOrigin(origins = "*")
public class KnowMappingController {

    @Autowired
    private GraphService graphService;

    @Autowired
    private PesticideCropRelationshipRepository pesticideCropRelationshipRepository;

    @Autowired
    private PesticideDiseaseRelationshipRepository pesticideDiseaseRelationshipRepository;

    @Autowired
    private PesticideRepository PesticideRepository;

    @Autowired
    private DiseaseRelationshipRepository diseaseRelationshipRepository;
    //@Autowired
    //private PesticideCropRelationshipJapanRepository pesticideCropRelationshipJapanRepository;


    @PostMapping("/apply")
    @ResponseBody
    public String getApplyGraph(@RequestParam("searchInput") String searchInput) {
        // 使用 URL 参数进行查询
        return "MATCH (p:Pesticide {name: '" + searchInput + "'})-[r:APPLICABLE_FOR]->(d:Crop) RETURN p, r, d";
    }

    //预防
    @PostMapping("/prevent")
    @ResponseBody
    public String getPreventGraph(@RequestParam("searchInput") String searchInput) {
        // 使用 URL 参数进行查询
        return "MATCH (p:Pesticide {name: '" + searchInput + "'})-[r:PREVENTS]->(d:Disease) RETURN p, r, d";
    }

    //疾病和作物
    @PostMapping("/disease")
    @ResponseBody
    public String getDiseaseGraph(@RequestParam("searchInput") String searchInput) {
        // 使用 URL 参数进行查询
        return "MATCH (p:Disease {name: '" + searchInput + "'})-[r:CAUSES_DISEASE]->(d:Crop) RETURN p, r, d";
    }


    //日本
    @PostMapping("/applyj")
    @ResponseBody
    public String getApplyGraph2(@RequestParam("searchInput") String searchInput) {
        // 使用 URL 参数进行查询
        return "MATCH (p:Pesticide {name: '" + searchInput + "'})-[r:係る]->(d:Crop) RETURN p, r, d";
    }

    @PostMapping("/preventj")
    @ResponseBody
    public String getPreventGraph2(@RequestParam("searchInput") String searchInput) {
        // 使用 URL 参数进行查询
        return "MATCH (p:Pesticide {name: '" + searchInput + "'})-[r:予防と治療]->(d:Disease) RETURN p, r, d";
    }

    @PostMapping("/diseasej")
    @ResponseBody
    public String getDiseaseGraph2(@RequestParam("searchInput") String searchInput) {
        // 使用 URL 参数进行查询
        return "MATCH (p:Disease {name: '" + searchInput + "'})-[r:いためる]->(d:Crop) RETURN p, r, d";
    }


    @PostMapping("/applyInformation/{pesticideName}")
    @ResponseBody
    public Map<String, Object> getApplyInformation(@PathVariable("pesticideName") String pesticideName) {
        //找出与农药有关的作物的关系
        List<PesticideCropRelationship> applyRelations = pesticideCropRelationshipRepository.findRelationshipsByPesticideName(pesticideName);
        Pesticide Pesticide = PesticideRepository.findByName(pesticideName);

        List<String> result = new ArrayList<>();
        //根据关系找出作物
        for (PesticideCropRelationship relation : applyRelations) {
            Crop Crop = relation.getCrop();
            if (Crop != null) {
                result.add(Crop.getName());
            }
        }

        Map<String, Object> response = new HashMap<>();
        response.put("result", result);
//        response.put("registrantInformation", Pesticide.getRegistrantInfo());
//        response.put("registrationTime", Pesticide.getRegistrationDate());
//        response.put("activeIngredient", Pesticide.getActiveIngredient());
//        response.put("otherComponents", Pesticide.getOtherIngredients());
//        response.put("structuralCategory", Pesticide.getStructureCategory());
//        response.put("specificTypes", Pesticide.getSpecificType());
//        response.put("modeOfAction", Pesticide.getModeOfAction());

        return response;
    }

    /*@PostMapping("/applyInformationJ/{pesticideName}")
    @ResponseBody
    public Map<String, Object> getApplyInformationJ(@PathVariable("pesticideName") String pesticideName) {
        List<PesticideCropRelationshipJapan> applyRelations = pesticideCropRelationshipJapanRepository.findRelationshipsByPesticideName(pesticideName);
        Pesticide Pesticide = PesticideRepository.findByName(pesticideName);

        List<String> result = new ArrayList<>();
        for (PesticideCropRelationshipJapan relation : applyRelations) {
            Crop Crop = relation.getCrop();
            if (Crop != null) {
                result.add(Crop.getName());
            }
        }

        Map<String, Object> response = new HashMap<>();
        response.put("result", result);
//        response.put("registrantInformation", Pesticide.getRegistrantInfo());
//        response.put("registrationTime", Pesticide.getRegistrationDate());
//        response.put("activeIngredient", Pesticide.getActiveIngredient());
//        response.put("otherComponents", Pesticide.getOtherIngredients());
//        response.put("structuralCategory", Pesticide.getStructureCategory());
//        response.put("specificTypes", Pesticide.getSpecificType());
//        response.put("modeOfAction", Pesticide.getModeOfAction());

        System.out.println(response);
        return response;
    }
*/
    @PostMapping("/preventInformation/{pesticideName}")
    @ResponseBody
    public Map<String, Object> getPreventInformation(@PathVariable("pesticideName") String pesticideName) {
        List<PesticideDiseaseRelationship> preventRelations = pesticideDiseaseRelationshipRepository.findRelationshipsByPesticideName(pesticideName);
        Pesticide Pesticide = PesticideRepository.findByName(pesticideName);

        List<String> result = new ArrayList<>();
        for (PesticideDiseaseRelationship relation : preventRelations) {
            Disease Disease = relation.getDisease();
            if (Disease != null) {
                result.add(Disease.getName());
            }
        }

        Map<String, Object> response = new HashMap<>();
        response.put("result", result);
//        response.put("registrantInformation", Pesticide.getRegistrantInfo());
//        response.put("registrationTime", Pesticide.getRegistrationDate());
//        response.put("activeIngredient", Pesticide.getActiveIngredient());
//        response.put("otherComponents", Pesticide.getOtherIngredients());
//        response.put("structuralCategory", Pesticide.getStructureCategory());
//        response.put("specificTypes", Pesticide.getSpecificType());
//        response.put("modeOfAction", Pesticide.getModeOfAction());

        return response;
    }


    //客户端传来一个疾病名称，返回与这个疾病有关作物以及作物对应的农药
    @PostMapping("/diseaseInformation/{diseaseName}")
    @ResponseBody
    public Map<String, Object> getDiseaseInformation(@PathVariable("diseaseName") String diseaseName) {
        //疾病和作物
        List<DiseaseRelationship> diseaseRelations = diseaseRelationshipRepository.findRelationshipsByDiseaseName(diseaseName);
        //疾病和农药
        List<PesticideDiseaseRelationship> preventRelations = pesticideDiseaseRelationshipRepository.findByDiseaseName(diseaseName);

        List<String> result = new ArrayList<>();
        for (DiseaseRelationship relation : diseaseRelations) {
            Crop Crop = relation.getCrop();
            if (Crop != null) {
                result.add(Crop.getName());
            }
        }

        List<String> pesticideInformations = new ArrayList<>();
        for (PesticideDiseaseRelationship relation : preventRelations) {
            Pesticide Pesticide = relation.getPesticide();
            if (Pesticide != null) {
                pesticideInformations.add(Pesticide.getName());
            }
        }

        StringBuilder stringBuilder = new StringBuilder();
        for (int i = 0; i < pesticideInformations.size(); i++) {
            String info = (i + 1) + "、" + pesticideInformations.get(i);
            if (stringBuilder.length() + info.length() <= 1150) {
                stringBuilder.append(info);
                if (i < pesticideInformations.size() - 1) {
                    stringBuilder.append(", ");
                }
            } else {
                break;
            }
        }

        // 获取最后一个元素的索引
        int lastIndex = pesticideInformations.size() - 1;
        // 将最后一个逗号替换为句号
        stringBuilder.replace(stringBuilder.lastIndexOf(", "), stringBuilder.length(), ".");

        String pesticideInformation = stringBuilder.toString();
        if (pesticideInformations.size() > 0 && pesticideInformation.length() > 1150) {
            pesticideInformation += "..";
        }


        Map<String, Object> response = new HashMap<>();
        response.put("result", result);//result里面装的是作物名
        response.put("pesticideInformation", pesticideInformation);//这个里面装的是农药信息

        return response;
    }

    @PostMapping("/node")
    @ResponseBody
    public Map<String, String> getNodeInfo(@RequestBody Map<String, String> requestBody) {
        // 从请求体中获取参数
        String nodeType = requestBody.get("nodeType");
        String nodeName = requestBody.get("nodeName");

        // 打印参数

        return graphService.getKnowledgeGraphByPesticideName(nodeName);
    }


    @PostMapping("/apply2")
    @ResponseBody
    public String findRelationshipsByPesticideName(@RequestBody Map<String, String> requestBody) {
        String searchInput = requestBody.get("searchInput");
        List<PesticideCropRelationship> pesticideCropRelationshipList = pesticideCropRelationshipRepository.findRelationshipsByPesticideName(searchInput);
        System.out.println(pesticideCropRelationshipList);
        return pesticideCropRelationshipList.toString();
    }


    @PostMapping("/prevent2")
    @ResponseBody
    public List<PreventsDto> findPesticideAndDiseaseRelationshipsByPesticideName(@RequestBody Map<String, String> requestBody) {
        String searchInput = requestBody.get("searchInput");
        List<PesticideDiseaseRelationship> pesticideDiseaseRelationshipList =
                pesticideDiseaseRelationshipRepository.findRelationshipsByPesticideName(searchInput);

        List<PreventsDto> preventsDtoList = new ArrayList<>();
        for (PesticideDiseaseRelationship relationship : pesticideDiseaseRelationshipList) {
            PreventsDto data = new PreventsDto();
            data.setPesticide(relationship.getPesticide());
            data.setRelationship("PREVENTS"); // 或者根据实际情况设置关系类型
            data.setDisease(relationship.getDisease());
            preventsDtoList.add(data);
        }
        return preventsDtoList;
    }

}
