package com.sc.pesticideknowledgemappingsystem.service;

import com.sc.pesticideknowledgemappingsystem.entity.node.ActiveSubstance;
import com.sc.pesticideknowledgemappingsystem.repository.node.ActiveSubstanceRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class ActiveSubstanceService {
    @Autowired
    private ActiveSubstanceRepository activeSubstanceRepository;

    // 获取活性物质指定属性
    public String getActiveSubstanceProperty(String activeSubstanceName, String propertyName) {
        ActiveSubstance activeSubstance = activeSubstanceRepository.findByName(activeSubstanceName);
        if (activeSubstance == null) {
            return "The specified active substance was not found.";
        }

        String propertyValue = null;
        switch (propertyName.toLowerCase()) {
            case "name":
                propertyValue = activeSubstance.getName();
                break;
            case "the coding":
                propertyValue = activeSubstance.getTheCoding();
                break;
            case "iso common names":
                propertyValue = activeSubstance.getIsoCommonNames();
                break;
            case "proposed chinese names":
                propertyValue = activeSubstance.getProposedChineseNames();
                break;
            case "other names":
                propertyValue = activeSubstance.getOtherNames();
                break;
            case "chemical names(iupac or cas)":
                propertyValue = activeSubstance.getChemicalNames();
                break;
            case "chinese chemical names":
                propertyValue = activeSubstance.getChineseChemicalNames();
                break;
            case "iupac international chemical identifier (unchi) v. 1.06":
                propertyValue = activeSubstance.getInChi();
                break;
            case "iupac international chemical identification search code (inchi key) v. 1.06":
                propertyValue = activeSubstance.getInChiKey();
                break;
            case "echa number":
                propertyValue = activeSubstance.getEchaNumber();
                break;
            case "2d chemical structure":
                propertyValue = activeSubstance.getChemicalStructure2D();
                break;
            case "3d chemical structure or crystal structure or the image 3d chemical structure or crystal structure or the image":
                propertyValue = activeSubstance.getChemicalStructure3D();
                break;
            case "molecular or experimental formulas formul":
                propertyValue = activeSubstance.getMolecularFormulas();
                break;
            case "relative molecular mass rmm":
                propertyValue = activeSubstance.getRelativeMolecularMass();
                break;
            case "exact mass":
                propertyValue = activeSubstance.getExactMass();
                break;
            case "chemical classes(groups) or source":
                propertyValue = activeSubstance.getChemicalClasses();
                break;
            case "cas registry number":
                propertyValue = activeSubstance.getCasRegistryNumber();
                break;
            case "registration status":
                propertyValue = activeSubstance.getRegistrationStatus();
                break;
            case "cipac code numbers":
                propertyValue = activeSubstance.getCipacCodeNumbers();
                break;
            case "use type":
                propertyValue = activeSubstance.getUseType();
                break;
            case "published agencies & versions":
                propertyValue = activeSubstance.getPublishedAgencies();
                break;
            case "russian name":
                propertyValue = activeSubstance.getRussianName();
                break;
            case "chinese common name":
                propertyValue = activeSubstance.getChineseCommonName();
                break;
            case "french name":
                propertyValue = activeSubstance.getFrenchName();
                break;
            case "portuguese name nome em portugues":
                propertyValue = activeSubstance.getPortugueseName();
                break;
            case "mode of action":
                propertyValue = activeSubstance.getModeOfAction();
                break;
            case "elemental analysis (calculated value calcd., %)":
                propertyValue = activeSubstance.getElementalAnalysis();
                break;
            case "china pesticide common name serial number gb 4839-2009 code numbers":
                propertyValue = activeSubstance.getGb4839CodeNumbers();
                break;
            case "codex pesticide code numbers codex pesticide code numbers":
                propertyValue = activeSubstance.getCodexPesticideCodeNumbers();
                break;
            case "chinese customs commodity code numbers(2022)":
                propertyValue = activeSubstance.getChineseCustomsCode();
                break;
            case "technical and preparations":
                propertyValue = activeSubstance.getTechnicalAndPreparations();
                break;
            case "main targets & applications":
                propertyValue = activeSubstance.getMainTargets();
                break;
            case "toxicity classification (class) and antidotes toxicity and antidotes":
                propertyValue = activeSubstance.getToxicityClassification();
                break;
            case "hazard pictogram":
                propertyValue = activeSubstance.getHazardPictogram();
                break;
            case "toxicology & fate":
                propertyValue = activeSubstance.getToxicologyAndFate();
                break;
            case "maximum residue limits (mrls) and related regulations (with attention to timeliness) mrls and texts":
                propertyValue = activeSubstance.getMrlsAndRegulations();
                break;
            case "manufacturer or distributor or registrant":
                propertyValue = activeSubstance.getManufacturer();
                break;
            case "chinese registered name":
                propertyValue = activeSubstance.getChineseRegisteredName();
                break;
            case "introduction":
                propertyValue = activeSubstance.getIntroduction();
                break;
            case "physical & chemical properties":
                propertyValue = activeSubstance.getPhysicalAndChemicalProperties();
                break;
            case "the way of action":
                propertyValue = activeSubstance.getWayOfAction();
                break;
            case "resistance":
                propertyValue = activeSubstance.getResistance();
                break;
            case "history":
                propertyValue = activeSubstance.getHistory();
                break;
            case "remarks":
                propertyValue = activeSubstance.getRemarks();
                break;
            case "other uses":
                propertyValue = activeSubstance.getOtherUses();
                break;
            case "agents classified by the international agency for research on cancer (iarc) monographs":
                propertyValue = activeSubstance.getIarcMonographs();
                break;
            case "phytotoxicity":
                propertyValue = activeSubstance.getPhytotoxicity();
                break;
            case "limit value/guideline value in drinking-water (note the timeliness) guideline value in drinking-water":
                propertyValue = activeSubstance.getGuidelineValueInDrinkingWater();
                break;
            case "isomeric smiles":
                propertyValue = activeSubstance.getIsomericSmiles();
                break;
            default:
                propertyValue = "Unknown property";
                break;
        }
        return propertyValue;
    }


}
