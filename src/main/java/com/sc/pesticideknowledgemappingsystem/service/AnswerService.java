//package com.sc.pesticideknowledgemappingsystem.service;
//
//import org.apache.poi.ss.usermodel.*;
//import org.apache.xmlbeans.ResourceLoader;
//import org.springframework.beans.factory.annotation.Autowired;
//import org.springframework.stereotype.Service;
//
//import javax.annotation.Resource;
//import java.io.BufferedReader;
//import java.io.FileInputStream;
//import java.io.IOException;
//import java.io.InputStream;
//import java.util.ArrayList;
//import java.util.Arrays;
//import java.util.List;
//
//@Service
//public class AnswerService {
//
//    @Autowired
//    private PesticideService pesticideService;
//    @Autowired
//    private ClassifyService classifyService;
//    @Autowired
//    private DiseaseService diseaseService;
//
//    private static final String BASE_PATH = "data/";
//
//    private static final List<String> pesticideList;
//    private static final List<String> cropList;
//    private static final List<String> diseaseList;
//    private static final List<String> activeSubstanceList;
//    private static final List<String> pesticideCategoryList;
//    private static final List<String> structuralList;
//    private static final List<String> typeList;
//
//    static {
//        try {
//            ClassLoader classLoader = AnswerService.class.getClassLoader();
//            pesticideList = readDataFromInputStream(classLoader.getResourceAsStream(BASE_PATH + "pesticide.xlsx"));
//            cropList = readDataFromInputStream(classLoader.getResourceAsStream(BASE_PATH + "crop.xlsx"));
//            diseaseList = readDataFromInputStream(classLoader.getResourceAsStream(BASE_PATH + "disease.xlsx"));
//            activeSubstanceList = readDataFromInputStream(classLoader.getResourceAsStream(BASE_PATH + "activeSubstance.xlsx"));
//            pesticideCategoryList = readDataFromInputStream(classLoader.getResourceAsStream(BASE_PATH + "Mode of action.xlsx"));
//            structuralList = readDataFromInputStream(classLoader.getResourceAsStream(BASE_PATH + "Structural category.xlsx"));
//            typeList = readDataFromInputStream(classLoader.getResourceAsStream(BASE_PATH + "Type of Pesticide.xlsx"));
//        } catch (IOException e) {
//            // 处理异常
//            e.printStackTrace();
//            throw new RuntimeException("Failed to load data from files");
//        }
//    }
//
//    public String pipei(String text) throws IOException {
//        //text转小写进行匹配
//        text=text.toLowerCase();
//        //农药
//        List<String> featureWords_2 = new ArrayList<>(Arrays.asList(
//                "applicable", "防治", "use", "usage"
//        ));
//
//        //作物
//        List<String> featureWords_3 = new ArrayList<>(Arrays.asList(
//                "plant", "crop", "crops", "植物", "作物", "庄稼"
//        ));
//
//        List<String> featureWords_4 = new ArrayList<>(Arrays.asList(
//                "disease", "pest", "virus", "病害", "害虫", "病毒",
//                "damage", "侵害", "致病", "影响", "affect"
//        ));
//
//
//        //农药属性信息
//        List<String> featureWords_5 = new ArrayList<>(Arrays.asList(
//                "registrationnumber", "productname", "dateofregistration", "companyname",
//                "pesticidecategory", "cropname", "diseaseorpests", "activesubstance",
//                "unit", "numberofapplications", "applicationtime", "applicationmethods",
//                "applicationinterval", "concentration", "expirationdate", "status",
//                "status group", "status date", "latest label date", "company number",
//                "restricted use reason", "pesticide type", "use type", "physical form",
//                "signal word", "restricted use flag", "record view", "transfer history",
//                "me-too references", "pm team", "pm email", "sort by reg",
//                "epapccodecasnumber", "end-of-lifelastwencoding", "deliverytimelastwcoding",
//                "usebyapplication", "dtgversion", "applicationlocations", "growthstage",
//                "number of applications per 12 months", "maximum agent dose per crop season",
//                "water volume scale", "safety term", "comments", "map",
//                "maternal authorisation", "minor application", "water volume depending on crop height",
//                "seed density at seed treatment (kg/ha)", "up", "overseas original manufacturer",
//                "note", "labeling file", "barcode", "quantitative",
//                "container material", "dilution factor", "safe harvesting period",
//                "caveat", "date of approval", "original registered manufacturer's name",
//                "nz agent name", "condition id", "use"));
//
//        List<String> featureWords_6 = new ArrayList<>(Arrays.asList(
//                "prevent", "use to", "防治", "用于", "适用"
//        ));
//
//        /*若是农药相关*/
//        for (String pesticideName : pesticideList) {
//            if (text.contains(pesticideName)) {
//                /*某农药某属性的信息 √ */
//                for (String featureWords : featureWords_5) {
//                    if (text.contains(featureWords)) {
//                        return pesticideService.getPesticideProperty(pesticideName, featureWords);
//                    }
//                }
//
//                /*如果包含具体病害  农药和病害的连接 */
//                for (String diseaseName : diseaseList) {
//                    if (text.contains(diseaseName)) {
//                        return pesticideService.printPesticideAndDiseaseInfo(pesticideName, diseaseName);
//                    }
//                }
//
//                /*如果包含具体作物  农药和作物的连接，特指一个作物*/
//                for (String cropName : cropList) {
//                    if (text.contains(cropName)) {
//                        return pesticideService.printPesticideAndCropInfo(pesticideName, cropName);
//                    }
//
//                }
//
//                /*适用于哪些作物 多个作物*/
//                for (String featureWords : featureWords_3) {
//                    if (text.contains(featureWords)) {
//                        return pesticideService.printPesticideApplicableForCropInfo(pesticideName);
//                    }
//                }
//
//                /*防治哪些病害 ，多个病害*/
//                for (String featureWords : featureWords_4) {
//                    if (text.contains(featureWords)) {
//                        return pesticideService.printPesticidePreventsDiseaseInfo(pesticideName);
//                    }
//                }
//
//                //防治，查找一个农药治疗的disaese的关系的信息
//                for (String f : featureWords_2) {
//                    if (text.contains(f)) {
//                        return pesticideService.getPesticideUsageInstructions(pesticideName);
//                    }
//                }
//                return pesticideService.printPesticideInfo(pesticideName);
//            }
//        }
//
//        /*如果包含具体作物*/
//        for (String cropName : cropList) {
//            if (text.contains(cropName)) {
//                /*如果包含具体病害*/
//                for (String diseaseName : diseaseList) {
//                    if (text.contains(diseaseName)) {
//                        return pesticideService.getTreatmentForCropDisease(cropName, diseaseName);
//                    }
//                }
//            }
//
//        }
//
//        //查找作用模式
//        if (text.contains("action") || text.contains("作用") || text.contains("function")) {
//            return classifyService.findAllActionModes();
//        }
//
//        //查找所有的结构结构类别 ChemicalClasses
//        if (text.contains("structure") || text.contains("结构")) {
//            return classifyService.findAllChemicalClasses();
//        }
//
//        /*查询某剂型下的所有农药  活性成分下的所有农药*/
//        for (String activateSubstanceName : activeSubstanceList) {
//            if (text.contains(activateSubstanceName)) {
//                //return classifyService.findPesticidesByFormulation(formulationName);
//                return classifyService.findPesticidesByActiveSubstance(activateSubstanceName);
//            }
//        }
//
//        /*查看某结构  pesticideCategoryList是作用方式，如果要找结构类别应该有农药大类来决定  pesticideCategoryList->pesticideCategory*/
//        for (String pesticideCategory : pesticideCategoryList) {
//            if (text.contains(pesticideCategory)) {
//                if (text.contains("结构") || text.contains("PesticideCategory")) {
//                    //return classifyService.findStructuralCategoriesByActionModeName(action);
//                    return classifyService.findChemicalClassesByPesticideCategoryName(pesticideCategory);
//                }
//
//                //某个农药里包含杀虫剂这样的属性，就把该农药找出来 pesticideCategory
//                if (text.contains("pesticide") || text.contains("农药")) {
//                    return pesticideService.getPesticideNamesByPesticideCategory(pesticideCategory);
//                }
//            }
//        }
//
//        /*若是剂型相关，没有剂型*/
//        if (text.contains("active")) {
//            //return classifyService.findAllFormulationNodes();
//            return classifyService.findAllActionModes();
//        }
//
//        //病虫草害
//        for (String s : diseaseList) {
//
//            if (text.contains(s)) {
//                /*某种病害可以被什么农药防治*/
//                for (String featureWords : featureWords_6) {
//                    if (text.contains(featureWords)) {
//                        return diseaseService.findPesticidesByDiseaseName(s);
//                    }
//                }
//
//                /*某种病害可以致病哪些作物*/
//                for (String f2 : featureWords_3) {
//                    if (text.contains(f2)) {
//                        return diseaseService.findCropsByDiseaseName(s);
//                    }
//                }
//            }
//
//        }
//
//        //作物
//        for (String c : cropList) {
//            if (text.contains(c)) {
//                for (String f : featureWords_4) {
//                    if (text.contains(f)) {
//                        return diseaseService.findDiseasesByCropName(c);
//                    }
//                }
//            }
//        }
//
//        //根据农药大类查找，杀虫剂，杀菌剂这些
//        for (String t : typeList) {
//            if (text.contains(t)) {
//                return pesticideService.getPesticidesByCategory(t);
//            }
//        }
//
//        return "Xiaozhi is still young and doesn't know what you're talking about~";
//    }
//
//    private static List<String> readDataFromInputStream(InputStream inputStream) throws IOException {
//        try (Workbook workbook = WorkbookFactory.create(inputStream)) {
//            Sheet sheet = workbook.getSheetAt(0); // Assuming data is in the first sheet
//            List<String> dataList = new ArrayList<>();
//            for (Row row : sheet) {
//                Cell cell = row.getCell(0); // Assuming data is in the first column
//                if (cell != null) {
//                    dataList.add(cell.toString());
//                }
//            }
//            return dataList;
//        }
//    }
//
//}