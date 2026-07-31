package com.sc.pesticideknowledgemappingsystem.service;

import com.sc.pesticideknowledgemappingsystem.entity.node.*;
import com.sc.pesticideknowledgemappingsystem.entity.relationship.ContainRelationship;
import com.sc.pesticideknowledgemappingsystem.entity.relationship.ContainRelationship3;
import com.sc.pesticideknowledgemappingsystem.repository.node.*;
import com.sc.pesticideknowledgemappingsystem.repository.relationship.ContainRelationshipRepository;
import com.sc.pesticideknowledgemappingsystem.repository.relationship.ContainRelationshipRepository2;
import com.sc.pesticideknowledgemappingsystem.repository.relationship.ContainRelationshipRepository3;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.StringJoiner;
import java.util.stream.Collectors;

@Service
public class ClassifyService {
    @Autowired
    private ActiveSubstanceRepository activeSubstanceRepository;
    @Autowired
    private ModeOfActionRepository ModeOfActionRepository;
    @Autowired
    private ChemicalClassesRepository ChemicalClassesRepository;
    @Autowired
    private PesticideRepository PesticideRepository;
    @Autowired
    private ContainRelationshipRepository containRelationshipRepository;
    @Autowired
    private ContainRelationshipRepository2 containRelationshipRepository2;
    @Autowired
    private ContainRelationshipRepository3 containRelationshipRepository3;


    // 检索所有节点名称并拼接成字符串的方法
    //查找活性成分节点
    public String findAllActivaSubstances() {
        List<ActiveSubstance> activeSubstances = activeSubstanceRepository.findAll();

        StringBuilder text = new StringBuilder("There are many types of activeSubstances, for example:");

        for (int i = 0; i < activeSubstances.size(); i++) {
            String name = activeSubstances.get(i).getName();
            text.append((i + 1) + "." + name);
            if (i < activeSubstances.size() - 1) {
                text.append("，");
            }
        }

        return text.toString();
    }

    // 查询所有作用方式的方法
    public String findAllActionModes() {
        List<ModeOfAction> ModeOfActions = ModeOfActionRepository.findAll();

        StringBuilder text = new StringBuilder("There are many types of pesticides, for example:");

        for (int i = 0; i < ModeOfActions.size(); i++) {
            String name = ModeOfActions.get(i).getName();
            text.append((i + 1) + "." + name);
            if (i < ModeOfActions.size() - 1) {
                text.append("，");
            }
        }

        return text.toString();
    }

    // 查询所有结构类别节点的方法
    public String findAllChemicalClasses() {
        List<ChemicalClasses> ChemicalClassess = ChemicalClassesRepository.findAll();

        StringBuilder text = new StringBuilder("There are many types of pesticide structures, for example:");

        for (int i = 0; i < ChemicalClassess.size(); i++) {
            String name = ChemicalClassess.get(i).getName();
            text.append((i + 1)).append('.').append(name);
            if (i < ChemicalClassess.size() - 1) {
                text.append("，");
            }
        }

        return text.toString();
    }

    //根据指定的作用方式查找农药   看农药里面的属性
//    public String findByModeOfAction(String modeOfAction) {
//        List<Pesticide> PesticideList = PesticideRepository.findByModeOfAction(modeOfAction);
//
//        StringBuilder text = new StringBuilder();
//        for (int i = 0; i < PesticideList.size(); i++) {
//            text.append(i + 1).append(". ").append(PesticideList.get(i).getName());
//            if (i < PesticideList.size() - 1) {
//                text.append(", ");
//            }
//        }
//
//        if (PesticideList.isEmpty()) {
//            return "No pesticides found with the given mode of action.";
//        }
//
//        /*        return modeOfAction + "的农药有：" + text.toString();*/
//        return modeOfAction + " pesticides with mode of action: " + text.toString();
//    }

    //给定结构类别查找农药
    public String findByStructureCategory(String structureCategory) {
        List<Pesticide> PesticideList = PesticideRepository.findByPesticideCategory(structureCategory);

        StringBuilder text = new StringBuilder();
        for (int i = 0; i < PesticideList.size(); i++) {
            text.append(i + 1).append(". ").append(PesticideList.get(i).getName());
            if (i < PesticideList.size() - 1) {
                text.append(", ");
            }
        }

        if (PesticideList.isEmpty()) {
            return "Xiaozhi is still young and doesn't know what you're talking about~";
        }

        /*        return structureCategory + "结构类别的农药有：" + text.toString();*/
        return structureCategory + " pesticides of this structural category: " + text.toString();
    }

    //通过活性成分名称查找农药
    public String findPesticidesByActiveSubstance(String activeSubstanceName) {
        List<ContainRelationship3> containRelationships = containRelationshipRepository3.findRelationshipsByActiveSubstanceName(activeSubstanceName);

        if (containRelationships.isEmpty()) {
            return "There is no Pesticides by the activeSubstance~";
        }

        StringJoiner joiner = new StringJoiner(", ");
        for (int i = 0; i < containRelationships.size(); i++) {
            ContainRelationship3 relationship = containRelationships.get(i);
            joiner.add((i + 1) + "、" + relationship.getPesticide().getName());
        }

        /*        return formulationName + "剂型的农药有：" + joiner.toString();*/
        return "Pesticides under this fomulation of " + activeSubstanceName + " are:" + joiner.toString();
    }

    //通过农药类别查找所包含的结构类别
    public String findChemicalClassesByPesticideCategoryName(String PesticideCategoryName) {
        List<ContainRelationship> relationships = containRelationshipRepository.findRelationshipsPesticideCategoryName(PesticideCategoryName);
        List<String> categoryNames = relationships.stream()
                .map(ContainRelationship::getChemicalClasses)
                .map(ChemicalClasses::getName)
                .collect(Collectors.toList());
        /*        StringBuilder result = new StringBuilder(actionModeName + "所包含的结构类别有：");*/

        StringBuilder result = new StringBuilder("Structure categories included in " + PesticideCategoryName + ":");
        for (int i = 0; i < categoryNames.size(); i++) {
            result.append(i + 1).append("、").append(categoryNames.get(i));
            if (i < categoryNames.size() - 1) {
                result.append("，");
            }
        }
        return result.toString();
    }
}
