package com.sc.pesticideknowledgemappingsystem.entity.node;

import org.neo4j.ogm.annotation.NodeEntity;
import org.neo4j.ogm.annotation.GeneratedValue;
import org.neo4j.ogm.annotation.Id;
import lombok.Builder;
import lombok.Data;
import org.neo4j.ogm.annotation.Property;

@NodeEntity(label = "ActiveSubstance")
@Data
@Builder
public class ActiveSubstance {
    @Id
    @GeneratedValue
    private Long id;

    @Property(name = "name")
    private String name; // 具体类型名称

    @Property(name = "The coding")
    private String theCoding; // 编码

    @Property(name = "International common or usual names")
    private String internationalCommonNames; // 国际通用名称

    @Property(name = "ISO common names")
    private String isoCommonNames; // ISO通用名称

    @Property(name = "Proposed Chinese names")
    private String proposedChineseNames; // 提议的中文名称

    @Property(name = "Other names")
    private String otherNames; // 其他名称

    @Property(name = "Chemical names(IUPAC or CAS)")
    private String chemicalNames; // 化学名称（IUPAC或CAS）

    @Property(name = "Chinese chemical names")
    private String chineseChemicalNames; // 中文化学名称

    @Property(name = "IUPAC International Chemical Identifier (InChi) V. 1.06")
    private String inChi; // IUPAC国际化学标识符

    @Property(name = "IUPAC International Chemical Identification Search Code (InChi Key) V. 1.06")
    private String inChiKey; // IUPAC国际化学识别搜索代码

    @Property(name = "ECHA number")
    private String echaNumber; // 欧洲化学品管理局（ECHA）编号

    @Property(name = "2D Chemical structure")
    private String chemicalStructure2D; // 2D化学结构

    @Property(name = "3D Chemical structure or crystal structure or the image")
    private String chemicalStructure3D; // 3D化学结构或晶体结构或图像

    @Property(name = "Molecular or Experimental Formulas")
    private String molecularFormulas; // 分子或实验公式

    @Property(name = "Relative Molecular Mass RMM")
    private String relativeMolecularMass; // 相对分子质量

    @Property(name = "Exact mass")
    private String exactMass; // 精确质量

    @Property(name = "Chemical classes(Groups) or source")
    private String chemicalClasses; // 化学类别（组）或来源

    @Property(name = "CAS registry number")
    private String casRegistryNumber; // CAS注册号

    @Property(name = "Registration Status")
    private String registrationStatus; // 注册状态

    @Property(name = "CIPAC code numbers")
    private String cipacCodeNumbers; // CIPAC代码

    @Property(name = "Use type")
    private String useType; // 使用类型

    @Property(name = "Published agencies & versions")
    private String publishedAgencies; // 发布机构及版本

    @Property(name = "Russian name Русское имя")
    private String russianName; // 俄文名称

    @Property(name = "Chinese common name")
    private String chineseCommonName; // 中文通用名称

    @Property(name = "French name Nom fran?ais")
    private String frenchName; // 法文名称

    @Property(name = "Portuguese Name Nome em portugues")
    private String portugueseName; // 葡萄牙文名称

    @Property(name = "Mode of action")
    private String modeOfAction; // 作用机制

    @Property(name = "Elemental analysis (calculated value Calcd., %)")
    private String elementalAnalysis; // 元素分析（计算值，%）

    @Property(name = "China pesticide common name serial number GB 4839-2009 code numbers")
    private String gb4839CodeNumbers; // 中国农药通用名称序列号

    @Property(name = "Codex pesticide code numbers")
    private String codexPesticideCodeNumbers; // Codex农药代码

    @Property(name = "Chinese Customs commodity code numbers(2022)")
    private String chineseCustomsCode; // 中国海关商品编码（2022）

    @Property(name = "Technical and Preparations")
    private String technicalAndPreparations; // 技术和制剂

    @Property(name = "Main targets & applications")
    private String mainTargets; // 主要目标和应用

    @Property(name = "Toxicity classification (class) and antidotes")
    private String toxicityClassification; // 毒性分类（类别）和解毒剂

    @Property(name = "Hazard pictogram")
    private String hazardPictogram; // 危害图标

    @Property(name = "Toxicology & Fate")
    private String toxicologyAndFate; // 毒理学与命运

    @Property(name = "Maximum Residue Limits (MRLs) and Related Regulations (with attention to timeliness)")
    private String mrlsAndRegulations; // 最大残留限量（MRLs）和相关法规

    @Property(name = "Manufacturer or Distributor or Registrant")
    private String manufacturer; // 制造商、分销商或注册人

    @Property(name = "Chinese registered name")
    private String chineseRegisteredName; // 中文注册名称

    @Property(name = "Introduction")
    private String introduction; // 介绍

    @Property(name = "Physical & chemical properties")
    private String physicalAndChemicalProperties; // 物理和化学性质

    @Property(name = "The way of action")
    private String wayOfAction; // 作用方式

    @Property(name = "Resistance")
    private String resistance; // 抵抗性

    @Property(name = "History")
    private String history; // 历史

    @Property(name = "Remarks")
    private String remarks; // 备注

    @Property(name = "Other uses")
    private String otherUses; // 其他用途

    @Property(name = "Agents Classified by the International Agency for Research on Cancer (IARC) Monographs")
    private String iarcMonographs; // 国际癌症研究机构（IARC）分类的代理

    @Property(name = "Phytotoxicity")
    private String phytotoxicity; // 植物毒性

    @Property(name = "Limit value/guideline value in drinking-water (note the timeliness)")
    private String guidelineValueInDrinkingWater; // 饮用水中的限值/指导值

    @Property(name = "Isomeric SMILES")
    private String isomericSmiles; // 立体异构体SMILES表示
}
