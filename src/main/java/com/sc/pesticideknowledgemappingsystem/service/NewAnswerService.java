package com.sc.pesticideknowledgemappingsystem.service;

import com.sc.pesticideknowledgemappingsystem.Naive_Bayes;
import org.apache.poi.ss.usermodel.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ApplicationContext;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.io.InputStream;
import java.util.*;

@Service
public class NewAnswerService {
    @Autowired
    private PesticideService pesticideService;
    @Autowired
    private ActiveSubstanceService activeSubstanceService;
    @Autowired
    private DiseaseService diseaseService;

    private static final String BASE_PATH = "data/";
    private static Map<String, List<String>> abstractMap = new HashMap<>();

    private static final List<String> pesticideList;
    private static final List<String> pesticideCategoryList;
    private static final List<String> cropList;
    private static final List<String> diseaseList;
    private static final List<String> activeSubstanceList;
    private static final List<String> targetSiteList;
    private static final List<String> chemicalClassesList;
    private static final List<String> moaList;
    static List<String> attributeList = new ArrayList<>(Arrays.asList(
            "name","registration number","product name","date of registration",
            "company name","pesticide category","crop name","disease or pests",
            "active substance","unit","number of applications","application time",
            "application methods","application interval","concentration",
            "expiration date","registration type","alternate brand names",
            "status","status group","status date","latest label date",
            "company number","restricted use reason","pesticide type","use type",
            "use pattern","physical form","signal word","restricted use flag",
            "record view","transfer history","me-too flag","me-too references",
            "pm team","pm email","sort by reg","epa pc code/cas number",
            "admission type","last w encodings","end-of-life last w encoding",
            "delivery time last w-coding","use","use by application","dtg version",
            "application locations","growth stage","number of applications per 12 months",
            "maximum agent dose per crop season","water volume scale","safety term",
            "comments","map","maternal authorisation","minor application",
            "water volume depending on crop height","seed density at seed treatment (kg/ha)",
            "brand name","delivery mechanism of a medicine","up","hybrid",
            "overseas original manufacturer","note","labeling file","barcode",
            "quantitative","container material","dosage per hectare per application",
            "dilution factor","safe harvesting period","caveat","clarification",
            "date of approval","original registered manufacturer's name","nz agent name",
            "condition id"
    ));
    static List<String> chemicalPropertyList = new ArrayList<>(Arrays.asList(
            "name","the coding","iso common names","proposed chinese names","other names",
            "chemical names(iupac or cas)","chinese chemical names",
            "iupac international chemical identifier (unchi) v. 1.06",
            "iupac international chemical identification search code (inchi key) v. 1.06",
            "echa number","2d chemical structure",
            "3d chemical structure or crystal structure or the image 3d chemical structure or crystal structure or the image",
            "molecular or experimental formulas formul","relative molecular mass rmm","exact mass",
            "chemical classes(groups) or source","cas registry number","registration status",
            "cipac code numbers","use type","published agencies & versions","russian name",
            "chinese common name","french name","portuguese name nome em portugues","mode of action",
            "elemental analysis (calculated value calcd., %)",
            "china pesticide common name serial number gb 4839-2009 code numbers",
            "codex pesticide code numbers codex pesticide code numbers",
            "chinese customs commodity code numbers(2022)","technical and preparations",
            "main targets & applications","toxicity classification (class) and antidotes toxicity and antidotes",
            "hazard pictogram","toxicology & fate",
            "maximum residue limits (mrls) and related regulations (with attention to timeliness) mrls and texts",
            "manufacturer or distributor or registrant","chinese registered name","introduction",
            "physical & chemical properties","the way of action","resistance","history","remarks","other uses",
            "agents classified by the international agency for research on cancer (iarc) monographs",
            "phytotoxicity","limit value/guideline value in drinking-water (note the timeliness) guideline value in drinking-water",
            "isomeric smiles"
    ));
    static List<String> diseaseAttributeList = new ArrayList<>(Arrays.asList(
            "name","latin name","disease and pest alias",
            "disease and pest infestation images","symptoms of infestation","pathogen",
            "transmission routes and pathogenic conditions","regular pattern of occurrence",
            "morphological characteristics","geographic distribution","host",
            "methods of prevention and treatment","others"
    ));


    private static List<String> readDataFromInputStream(InputStream inputStream) throws IOException {
        try (Workbook workbook = WorkbookFactory.create(inputStream)) {
            Sheet sheet = workbook.getSheetAt(0); // Assuming data is in the first sheet
            List<String> dataList = new ArrayList<>();
            for (Row row : sheet) {
                Cell cell = row.getCell(0); // Assuming data is in the first column
                if (cell != null) {
                    dataList.add(cell.toString());
                }
            }
            return dataList;
        }
    }

    static {
        try {
            ClassLoader classLoader = Naive_Bayes.class.getClassLoader();
            pesticideCategoryList = readDataFromInputStream(classLoader.getResourceAsStream(BASE_PATH + "Pesticide Category.xlsx"));
            chemicalClassesList = readDataFromInputStream(classLoader.getResourceAsStream(BASE_PATH + "CHEMICAL OR BIOLOGICAL GROUP.xlsx"));
            targetSiteList = readDataFromInputStream(classLoader.getResourceAsStream(BASE_PATH + "TARGET SITE AND CODE.xlsx"));
            moaList = readDataFromInputStream(classLoader.getResourceAsStream(BASE_PATH + "MOA.xlsx"));
            activeSubstanceList = readDataFromInputStream(classLoader.getResourceAsStream(BASE_PATH + "Active Substance.xlsx"));
            pesticideList = readDataFromInputStream(classLoader.getResourceAsStream(BASE_PATH + "Product Name.xlsx"));
            cropList = readDataFromInputStream(classLoader.getResourceAsStream(BASE_PATH + "Crop Name.xlsx"));
            diseaseList = readDataFromInputStream(classLoader.getResourceAsStream(BASE_PATH + "Disease Or Pests.xlsx"));
        } catch (IOException e) {
            // 处理异常
            e.printStackTrace();
            throw new RuntimeException("Failed to load data from files");
        }
    }

    public String Bayes(String querySentence) {
        System.out.println("原问题："+ querySentence);
        String abstractStr = queryAbstract(querySentence);
        System.out.println("抽象后的语句："+ abstractStr);
        int index = -1;
        try {
            // 指定根目录路径
            String rootDirPath = java.nio.file.Paths
                .get(System.getProperty("user.dir"), "legacy-data", "naive-bayes")
                .toString() + java.io.File.separator;

            // 初始化NaiveBayes分类器
            Naive_Bayes naiveBayesClassifier = new Naive_Bayes(rootDirPath);

            // 分析句子
            index = (int) naiveBayesClassifier.analysis(abstractStr);


        } catch (Exception e) {
            e.printStackTrace();
            System.out.println("Error: " + e.getMessage());
        }
        switch (index){
            case 0: {
                if(!abstractMap.containsKey("PESTICIDE") || !abstractMap.containsKey("ATTRIBUTE"))
                    return "Xiaozhi is still young and doesn't know what you're talking about~";
                for(String pesticideName : abstractMap.get("PESTICIDE")){
                    for(String atttribute: abstractMap.get("ATTRIBUTE"))
                    return pesticideService.getPesticideProperty(pesticideName, atttribute);
                }
                break;
            }
            case 1:{
                if(!abstractMap.containsKey("PESTICIDE") || !abstractMap.containsKey("DISEASE"))
                    return "Xiaozhi is still young and doesn't know what you're talking about~";
                for(String pesticideName : abstractMap.get("PESTICIDE")){
                    for(String disease: abstractMap.get("DISEASE"))
                        return pesticideService.printPesticideAndDiseaseInfo(pesticideName, disease);
                }
                break;
            }
            case 2:{
                if(!abstractMap.containsKey("PESTICIDE") || !abstractMap.containsKey("DISEASE"))
                    return "Xiaozhi is still young and doesn't know what you're talking about~";
                for(String pesticideName : abstractMap.get("PESTICIDE")){
                    for(String disease: abstractMap.get("DISEASE")){
                        if(pesticideService.printPesticideAndDiseaseInfo(pesticideName, disease).equals("Xiaozhi is still young and doesn't know what you're talking about~"))
                            return String.format("The pesticide '%s' cannot be used to treat the disease '%s'.", pesticideName, disease);
                        else return String.format("The pesticide '%s' can be used to treat the disease '%s'.", pesticideName, disease);
                    }
                }
                break;
            }
            case 3:{
                if(!abstractMap.containsKey("PESTICIDE") || !abstractMap.containsKey("CROP"))
                    return "Xiaozhi is still young and doesn't know what you're talking about~";
                for(String pesticideName : abstractMap.get("PESTICIDE")){
                    for(String crop: abstractMap.get("CROP")){
                        if(pesticideService.printPesticideAndCropInfo(pesticideName, crop).equals("Xiaozhi is still young and doesn't know what you're talking about~"))
                            return String.format("The pesticide '%s' cannot be used to treat the crop '%s'.", pesticideName, crop);
                        else return String.format("The pesticide '%s' can be used to treat the crop '%s'.", pesticideName, crop);
                    }
                }
                break;
            }
            case 4:{
                if(!abstractMap.containsKey("PESTICIDE") || !abstractMap.containsKey("CROP"))
                if(abstractMap.get("PESTICIDE").isEmpty() || abstractMap.get("CROP").isEmpty())
                    return "Xiaozhi is still young and doesn't know what you're talking about~";
                for(String pesticideName : abstractMap.get("PESTICIDE")){
                    for(String crop: abstractMap.get("CROP")){
                        return pesticideService.printPesticideAndCropInfo(pesticideName, crop);
                    }
                }
                break;
            }
            case 5:{
                if(!abstractMap.containsKey("PESTICIDE"))
                    return "Xiaozhi is still young and doesn't know what you're talking about~";
                for(String pesticideName : abstractMap.get("PESTICIDE")){
                    return pesticideService.printPesticideApplicableForCropInfo(pesticideName);
                }
                break;
            }
            case 6:{
                if(!abstractMap.containsKey("PESTICIDE"))
                    return "Xiaozhi is still young and doesn't know what you're talking about~";
                for(String pesticideName : abstractMap.get("PESTICIDE")){
                    return pesticideService.printPesticidePreventsDiseaseInfo(pesticideName);
                }
                break;
            }
            case 7:{
                if(!abstractMap.containsKey("PESTICIDE"))
                    return "Xiaozhi is still young and doesn't know what you're talking about~";
                for(String pesticideName : abstractMap.get("PESTICIDE")){
                    return pesticideService.getPesticideProperty(pesticideName, "active substance");
                }
                break;
            }
            case 8:{
                if(!abstractMap.containsKey("DISEASE") || !abstractMap.containsKey("CROP"))
                    return "Xiaozhi is still young and doesn't know what you're talking about~";
                for(String crop: abstractMap.get("CROP")){
                    for(String disease: abstractMap.get("DISEASE")){
                        return pesticideService.getTreatmentForCropDisease(crop, disease);
                    }
                }
                break;
            }
            case 9:{
                if(!abstractMap.containsKey("CROP"))
                    return "Xiaozhi is still young and doesn't know what you're talking about~";
                for(String crop: abstractMap.get("CROP")){
                    return diseaseService.findDiseasesByCropName(crop);
                }
                break;
            }
            case 10:{
                if(!abstractMap.containsKey("DISEASE"))
                    return "Xiaozhi is still young and doesn't know what you're talking about~";
                for(String disease: abstractMap.get("DISEASE")){
                    return diseaseService.findPesticidesByDiseaseName(disease);
                }
                break;
            }
            case 11:{
                if(!abstractMap.containsKey("ACTIVESUBSTANCE"))
                    return "Xiaozhi is still young and doesn't know what you're talking about~";
                for(String activeSubstance: abstractMap.get("ACTIVESUBSTANCE")){
                    for(String chemical_property: abstractMap.get("CHEMICAL_PROPERTY")){
                        return activeSubstanceService.getActiveSubstanceProperty(activeSubstance, chemical_property);
                    }
                }
                break;
            }
            case 12:{
                if(!abstractMap.containsKey("DISEASE") || !abstractMap.containsKey("DISEASE_ATTRIBUTE"))
                    return "Xiaozhi is still young and doesn't know what you're talking about~";
                for(String disease: abstractMap.get("DISEASE")){
                    for(String disease_attribute: abstractMap.get("DISEASE_ATTRIBUTE")){
                        return diseaseService.getDiseaseProperty(disease, disease_attribute);
                    }
                }
                break;
            }
            default:
                return "Xiaozhi is still young and doesn't know what you're talking about~";
        }
        abstractMap.clear();
        return "Xiaozhi is still young and doesn't know what you're talking about~";
    }

    public String queryAbstract(String querySentence) {
        querySentence = replaceAndMap(querySentence, pesticideList, "PESTICIDE");
        querySentence = replaceAndMap(querySentence, diseaseList, "DISEASE");
        querySentence = replaceAndMap(querySentence, cropList, "CROP");
        querySentence = replaceAndMap(querySentence, activeSubstanceList, "ACTIVESUBSTANCE");
        querySentence = replaceAndMap(querySentence, attributeList, "ATTRIBUTE");
        querySentence = replaceAndMap(querySentence, chemicalPropertyList, "CHEMICAL_PROPERTY");
        querySentence = replaceAndMap(querySentence, diseaseAttributeList, "DISEASE_ATTRIBUTE");

        return querySentence;
    }

    private String replaceAndMap(String sentence, List<String> itemList, String placeholder) {
        for (String item : itemList) {
            if (sentence.contains(item)) {
                sentence = sentence.replace(item, placeholder);
                abstractMap.computeIfAbsent(placeholder, k -> new ArrayList<>()).add(item);
            }
        }
        return sentence;
    }
}