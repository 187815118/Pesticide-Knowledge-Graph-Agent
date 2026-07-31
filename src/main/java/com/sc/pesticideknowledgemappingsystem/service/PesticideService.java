package com.sc.pesticideknowledgemappingsystem.service;

import com.sc.pesticideknowledgemappingsystem.entity.node.*;
import com.sc.pesticideknowledgemappingsystem.entity.relationship.*;
import com.sc.pesticideknowledgemappingsystem.repository.node.CropRepository;
import com.sc.pesticideknowledgemappingsystem.repository.node.PesticideRepository;
import com.sc.pesticideknowledgemappingsystem.repository.relationship.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;

@Service
@Transactional
public class PesticideService {
    @Autowired
    private PesticideRepository PesticideRepository;
    @Autowired
    private PesticideCropRelationshipRepository pesticideCropRelationshipRepository;
    @Autowired
    private DiseaseRelationshipRepository diseaseRelationshipRepository;
    @Autowired
    private PesticideDiseaseRelationshipRepository pesticideDiseaseRelationshipRepository;
    @Autowired
    private CropRepository CropRepository;

    @Autowired
    private ContainRelationshipRepository3 containRelationshipRepository3;

    @Autowired
    private ContainRelationshipRepository2 containRelationshipRepository2;

    @Autowired
    private ContainRelationshipRepository containRelationshipRepository;


    /**
     * 打印农药信息的方法，根据输入的农药名查询出最原始具体类型并打印相关信息
     * 打印基本信息
     *
     * @param pesticideName 农药名
     */
    public String printPesticideInfo(String pesticideName) {
        StringBuilder text = new StringBuilder(); // 用于存储最终的打印信息

        Pesticide Pesticide = PesticideRepository.findByName(pesticideName);

//        text.append(Pesticide.getName()).append(" is a pesticide with ")
//                .append(" formulation. It belongs to the category of ").append(Pesticide.getCategory()).append(", and its properties are ")
//                .append(Pesticide.getProperty()).append(". The registrant information is ").append(Pesticide.getRegistrantInfo())
//                .append(", with a registration date of ").append(Pesticide.getRegistrationDate()).append(". It has a toxicity level of ")
//                .append(Pesticide.getToxicity()).append(", with the active ingredient being ").append(Pesticide.getActiveIngredient())
//                .append(" and other ingredients including ").append(Pesticide.getOtherIngredients()).append(". It falls under the structure category of ")
//                .append(Pesticide.getStructureCategory()).append(" and belongs to the specific type of ").append(Pesticide.getSpecificType())
//                .append(". The mode of action is ").append(Pesticide.getModeOfAction());

        text.append(Pesticide.getName()).append(" is a pesticide with the product name ")
                .append(Pesticide.getProductName()).append(". It belongs to the category of ")
                .append(Pesticide.getPesticideCategory()).append(", targeting crops such as ")
                .append(Pesticide.getCropName()).append(" and addressing issues related to ")
                .append(Pesticide.getDiseaseOrPests()).append(". The registration number is ")
                .append(Pesticide.getRegistrationNumber()).append(", with a registration date of ")
                .append(Pesticide.getDateOfRegistration()).append(". This product is manufactured by ")
                .append(Pesticide.getCompanyName()).append(" and contains the active substance ")
                .append(Pesticide.getActiveSubstance()).append(".");

        return text.toString();
    }

    /*根据农药和病害返回信息*/
    public String printPesticideAndDiseaseInfo(String pesticideName, String diseaseName) {
        PesticideDiseaseRelationship pesticideDiseaseRelationship = pesticideDiseaseRelationshipRepository.findRelationshipsByPesticideNameAndDiseaseName(pesticideName, diseaseName);

        if (pesticideDiseaseRelationship != null) {
            Pesticide pesticide = pesticideDiseaseRelationship.getPesticide();
            Disease disease = pesticideDiseaseRelationship.getDisease();

            return String.format("%s pesticide can control %s diseases. The application time is: %s, the application methods is: %s, the application interval is: %s.",
                    pesticide.getName(), disease.getName(), pesticide.getApplicationTime(), pesticide.getApplicationMethods(), pesticide.getApplicationInterval());
        } else {
            return "The use of " + pesticideName + " is unrelated to the occurrence of " + diseaseName + ".";
        }
    }

    /*根据农药和作物返回信息*/
    public String printPesticideAndCropInfo(String pesticideName, String cropName) {
        List<PesticideDiseaseRelationship> pesticideDiseaseRelationships = pesticideDiseaseRelationshipRepository.findRelationshipsByPesticideName(pesticideName);

        List<PesticideCropRelationship> pesticideCropRelationships = pesticideCropRelationshipRepository.findRelationshipsBycropName(cropName);

        for (PesticideDiseaseRelationship pesticideDiseaseRelationship : pesticideDiseaseRelationships) {
            for (PesticideCropRelationship pesticideCropRelationship : pesticideCropRelationships) {
                if (pesticideDiseaseRelationship.getPesticide().getName().equals(pesticideCropRelationship.getPesticide().getName())) {
                    Pesticide Pesticide = pesticideDiseaseRelationship.getPesticide();
                    Disease Disease = pesticideDiseaseRelationship.getDisease();
                    Crop Crop = pesticideCropRelationship.getCrop();

                    return String.format("When pesticide %s is applied to crop %s, targeting the pathogenic disease %s.  The application time is: %s, the application methods is: %s, the application interval is: %s.",
                            Pesticide.getName(), Crop.getName(), Disease.getName(), Pesticide.getApplicationTime(), Pesticide.getApplicationMethods(), Pesticide.getApplicationInterval());
                }
            }
        }
        return pesticideName +" have no relation to "+cropName+".";
    }

    /*农药适用的作物*/
    public String printPesticideApplicableForCropInfo(String pesticideName) {
        List<PesticideCropRelationship> pesticideCropRelationshipList = pesticideCropRelationshipRepository.findRelationshipsByPesticideName(pesticideName);

        if (pesticideCropRelationshipList.isEmpty()) {
            return "Pesticide " + pesticideName + " does not have applicable crop information.";
        }

        StringBuilder textBuilder = new StringBuilder("Pesticide ").append(pesticideName).append(" is suitable for many crops, such as:");

        int index = 1;
        for (PesticideCropRelationship pesticideCropRelationship : pesticideCropRelationshipList) {
            String cropName = pesticideCropRelationship.getCrop().getName();
            textBuilder.append(index).append(".").append(cropName).append(", ");
            index++;
        }

        // 删除最后一个逗号和空格
        textBuilder.delete(textBuilder.length() - 2, textBuilder.length());

        return textBuilder.toString();
    }


    /*农药防治的病害*/
    public String printPesticidePreventsDiseaseInfo(String pesticideName) {
        List<PesticideDiseaseRelationship> pesticideDiseaseRelationshipList = pesticideDiseaseRelationshipRepository.findRelationshipsByPesticideName(pesticideName);

        if (pesticideDiseaseRelationshipList.isEmpty()) {
            return "Pesticide " + pesticideName + " has no disease prevention information.";
        }

        StringBuilder textBuilder = new StringBuilder("Pesticide ").append(pesticideName).append(" can prevent the following diseases:");
        int index = 1;
        for (PesticideDiseaseRelationship pesticideDiseaseRelationship : pesticideDiseaseRelationshipList) {
            String diseaseName = pesticideDiseaseRelationship.getDisease().getName();
            textBuilder.append(index).append(".").append(diseaseName).append(", ");
            index++;
        }
        // 删除最后一个逗号和空格
        textBuilder.delete(textBuilder.length() - 2, textBuilder.length());

        return textBuilder.toString();
    }


    //获取农药指定属性
    public String getPesticideProperty(String pesticideName, String propertyName) {
        Pesticide Pesticide = PesticideRepository.findByName(pesticideName);
        if (Pesticide == null) {
            return "The specified pesticide was not found.";
        }

        String propertyValue = null;
        switch (propertyName) {
            case "registration number":
                propertyValue = String.valueOf(Pesticide.getRegistrationNumber());
                break;
            case "product name":
                propertyValue = Pesticide.getProductName();
                break;
            case "date of registration":
                propertyValue = Pesticide.getDateOfRegistration();
                break;
            case "company name":
                propertyValue = Pesticide.getCompanyName();
                break;
            case "pesticide category":
                propertyValue = Pesticide.getPesticideCategory();
                break;
            case "crop name":
                propertyValue = Pesticide.getCropName();
                break;
            case "disease or pests":
                propertyValue = Pesticide.getDiseaseOrPests();
                break;
            case "active substance":
                propertyValue = Pesticide.getActiveSubstance();
                break;
            case "unit":
                propertyValue = Pesticide.getUnit();
                break;
            case "number of applications":
                propertyValue = Pesticide.getNumberOfApplications();
                break;
            case "application time":
                propertyValue = Pesticide.getApplicationTime();
                break;
            case "application methods":
                propertyValue = Pesticide.getApplicationMethods();
                break;
            case "application interval":
                propertyValue = Pesticide.getApplicationInterval();
                break;
            case "concentration":
                propertyValue = Pesticide.getConcentration();
                break;
            case "expirationdate":
                propertyValue = Pesticide.getExpirationDate();
                break;
            case "status":
                propertyValue = Pesticide.getStatus();
                break;
            case "status group":
                propertyValue = Pesticide.getStatusGroup();
                break;
            case "status date":
                propertyValue = Pesticide.getStatusDate();
                break;
            case "latest label date":
                propertyValue = Pesticide.getLatestLabelDate();
                break;
            case "company number":
                propertyValue = Pesticide.getCompanyNumber();
                break;
            case "restricted use reason":
                propertyValue = Pesticide.getRestrictedUseReason();
                break;
            case "pesticide type":
                propertyValue = Pesticide.getPesticideType();
                break;
            case "use type":
                propertyValue = Pesticide.getUseType();
                break;
            case "physical form":
                propertyValue = Pesticide.getPhysicalForm();
                break;
            case "signal word":
                propertyValue = Pesticide.getSignalWord();
                break;
            case "restricted use flag":
                propertyValue = Pesticide.getRestrictedUseFlag();
                break;
            case "record view":
                propertyValue = Pesticide.getRecordView();
                break;
            case "transfer history":
                propertyValue = Pesticide.getTransferHistory();
                break;
            case "me-too references":
                propertyValue = Pesticide.getMeTooReferences();
                break;
            case "pm team":
                propertyValue = Pesticide.getPmTeam();
                break;
            case "pm email":
                propertyValue = Pesticide.getPmEmail();
                break;
            case "sort by reg":
                propertyValue = Pesticide.getSortByRegNumber();
                break;
            case "epapccodecasnumber":
                propertyValue = Pesticide.getEpaPcCodeOrCasNumber();
                break;
            case "end-of-lifelastwencoding":
                propertyValue = Pesticide.getEndOfLifeLastWEncoding();
                break;
            case "deliverytimelastwcoding":
                propertyValue = Pesticide.getDeliveryTimeLastWEncoding();
                break;
            case "usebyapplication":
                propertyValue = Pesticide.getUseByApplication();
                break;
            case "dtgversion":
                propertyValue = Pesticide.getDtgVersion();
                break;
            case "applicationlocations":
                propertyValue = Pesticide.getApplicationLocations();
                break;
            case "growthstage":
                propertyValue = Pesticide.getGrowthStage();
                break;
            case "number of applications per 12 months":
                propertyValue = Pesticide.getNumberOfApplicationsPer12Months();
                break;
            case "maximum agent dose per crop season":
                propertyValue = Pesticide.getMaximumAgentDosePerCropSeason();
                break;
            case "water volume scale":
                propertyValue = Pesticide.getWaterVolumeScale();
                break;
            case "safety term":
                propertyValue = Pesticide.getSafetyTerm();
                break;
            case "comments":
                propertyValue = Pesticide.getComments();
                break;
            case "map":
                propertyValue = Pesticide.getMap();
                break;
            case "maternal authorisation":
                propertyValue = Pesticide.getMaternalAuthorisation();
                break;
            case "minor application":
                propertyValue = Pesticide.getMinorApplication();
                break;
            case "water volume depending on crop height":
                propertyValue = Pesticide.getWaterVolumeDependingOnCropHeight();
                break;
            case "seed density at seed treatment (kg/ha)":
                propertyValue = Pesticide.getSeedDensityAtSeedTreatment();
                break;
            case "up":
                propertyValue = Pesticide.getUp();
                break;
            case "overseas original manufacturer":
                propertyValue = Pesticide.getHybrid();
                break;
            case "note":
                propertyValue = Pesticide.getNote();
                break;
            case "labeling file":
                propertyValue = Pesticide.getLabelingFile();
                break;
            case "barcode":
                propertyValue =String.valueOf( Pesticide.getBarcode());
                break;
            case "quantitative":
                propertyValue = String.valueOf(Pesticide.getQuantitative());
                break;
            case "container material":
                propertyValue = Pesticide.getContainerMaterial();
                break;
            case "dilution factor":
                propertyValue = Pesticide.getDilutionFactor();
                break;
            case "safe harvesting period":
                propertyValue = Pesticide.getSafeHarvestingPeriod();
                break;
            case "caveat":
                propertyValue = Pesticide.getCaveat();
                break;
            case "date of approval":
                propertyValue = String.valueOf(Pesticide.getDateOfApproval());
                break;
            case "original registered manufacturer's name":
                propertyValue = Pesticide.getOriginalRegisteredManufacturerName();
                break;
            case "nz agent name":
                propertyValue = Pesticide.getNzAgentName();
                break;
            case "condition id":
                propertyValue = Pesticide.getConditionId();
                break;
            case "use":
                propertyValue = Pesticide.getUse();
                break;
            default:
                return "The property name is unknown.";
        }


        if (propertyValue .equals("-") || propertyValue.isEmpty()) {
            return "The property " + propertyName + " of " + pesticideName + " is empty.";
        }

        System.out.println("The " + propertyName + " of " + pesticideName + " is: " + propertyValue);
        return "The " + propertyName + " of " + pesticideName + " is: " + propertyValue;
    }

    //获取指定农药的类所包含的农药
    public String getPesticideNamesByPesticideCategory(String pesticideCategory) {
        List<Pesticide> Pesticides = PesticideRepository.findByPesticideCategory(pesticideCategory);

        if (Pesticides.isEmpty()) {
            return "No pesticides found for pesticide category: " + pesticideCategory;
        }

        StringBuilder textBuilder = new StringBuilder("Pesticides for pesticide category " + pesticideCategory + ":");

        int index = 1;
        for (Pesticide Pesticide : Pesticides) {
            String pesticideName = Pesticide.getName();
            textBuilder.append(index).append(".").append(pesticideName).append(", ");
            index++;
        }

        return textBuilder.toString();
    }

    //农药属性还没有确定
    public String getPesticidesByCategory(String category) {
        List<Pesticide> Pesticides = PesticideRepository.findByPesticideCategory(category);

        if (Pesticides.isEmpty()) {
            return "No pesticides found in category: " + category;
        }
        StringBuilder textBuilder = new StringBuilder("Pesticides belonging to category ").append(category).append(" are:");
        int index = 1;
        for (Pesticide pesticide : Pesticides) {
            textBuilder.append(index).append(".").append(pesticide.getName()).append(", ");
            index++;
        }
        return textBuilder.toString();
    }

    //通过农药找病害，看农药可以作用到哪些病害上
    public String getPesticideUsageInstructions(String pesticideName) {
        List<PesticideDiseaseRelationship> pesticideDiseaseRelationshipList = pesticideDiseaseRelationshipRepository.findRelationshipsByPesticideName(pesticideName);

        if (pesticideDiseaseRelationshipList.isEmpty()) {
            return "There is no usage information available for the pesticide: " + pesticideName;
        }

        StringBuilder textBuilder = new StringBuilder("The ").append(pesticideName).append(" has multiple ways to use. For example:");

        int index = 1;
        for (PesticideDiseaseRelationship relationship : pesticideDiseaseRelationshipList) {
            String diseaseName = relationship.getDisease().getName();
            textBuilder.append(",").append(index).append(". Preventing ").append(diseaseName);
            index++;
        }

        return textBuilder.toString();
    }

    /*返回XXX作物的XXX病用什么农药治，例如：XXX作物的XXX病可以这样治，使用XXX农药，稀释XX倍*/
    public String getTreatmentForCropDisease(String cropName, String diseaseName) {
        //作物找农药
        List<PesticideCropRelationship> pesticideCropRelationshipList = pesticideCropRelationshipRepository.findRelationshipsBycropName(cropName);
        //病害信息
        List<DiseaseRelationship> diseaseRelationshipList = diseaseRelationshipRepository.findRelationshipsByDiseaseName(diseaseName);

        List<String> instructionTexts = new ArrayList<>();


        for (PesticideCropRelationship pesticideCropRelationship : pesticideCropRelationshipList) {
            //获取作物和农药
            Pesticide Pesticide = pesticideCropRelationship.getPesticide();
            Crop Crop = pesticideCropRelationship.getCrop();

            //病害包含已有的作物，取出病害
            for (DiseaseRelationship diseaseRelationship : diseaseRelationshipList) {
                if (diseaseRelationship.getCrop().equals(Crop)) {
                    PesticideDiseaseRelationship pesticideDiseaseRelationship = pesticideDiseaseRelationshipRepository.findByPesticideNameAndDiseaseName(Pesticide.getName(), diseaseName);

                    if (pesticideDiseaseRelationship != null) {
                        String instructionText = cropName + " crops suffering from " + diseaseName + " can be treated with " + Pesticide.getName();
                        instructionTexts.add(instructionText);
                        return String.join("\n", instructionTexts);
                    }
                }
            }
        }

        return "No pesticide usage instructions available for the specified crop and disease.";

    }

}