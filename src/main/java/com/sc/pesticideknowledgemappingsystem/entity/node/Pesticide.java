package com.sc.pesticideknowledgemappingsystem.entity.node;

import lombok.Builder;
import lombok.Data;
import org.neo4j.ogm.annotation.GeneratedValue;
import org.neo4j.ogm.annotation.Id;
import org.neo4j.ogm.annotation.NodeEntity;
import org.neo4j.ogm.annotation.Property;

@NodeEntity(label = "Pesticide") //这个类在Neo4j图数据库中的节点（Node）的映射关系，这个类会映射到
@Data
@Builder
public class Pesticide {
    @Id
    @GeneratedValue
    private Long id; // 农药节点的唯一标识符

    @Property(name = "name")
    private String name; // 农药的名称

    @Property(name = "Registration Number")//登记号
    private String registrationNumber;

    @Property(name = "Product Name")//商品名
    private String productName;

    @Property(name = "Date Of Registration")//注册日期
    private String dateOfRegistration;

    @Property(name = "Company Name")//公司名
    private String companyName;

    @Property(name = "Pesticide Category") //农药种类 杀虫剂，杀菌剂，除草剂
    private String pesticideCategory;

    @Property(name = "Crop Name") //作物名称
    private String cropName;

    @Property(name = "Disease Or Pests") //病虫害
    private String diseaseOrPests;

    @Property(name = "Active Substance") //活性物质
    private String activeSubstance;

    //————————————————————————————————————————————————————————————————
    //查询与病虫害关系时，可以抽取这些信息回答
    @Property(name = "Unit") //单位
    private String unit;

    @Property(name = "Number Of Applications") //使用次数
    private String numberOfApplications;

    @Property(name = "Application Time") //使用时间
    private String applicationTime;

    @Property(name = "Application Methods") //使用方法
    private String applicationMethods;

    @Property(name = "Application Interval") //使用间隔
    private String applicationInterval;

    @Property(name = "Concentration") //浓度
    private String concentration;

    @Property(name = "Expiration Date")//有效期限
    private String expirationDate;

    //————————————————————————————————————————————————————————————

    //--------------------------------------------------------------
    /*美国*/
    @Property(name = "Registration Type")
    private String registrationType; // 注册类型

    @Property(name = "Alternate Brand Names")
    private String alternateBrandNames; // 替代品牌名称

    @Property(name = "Status")
    private String status; // 状态

    @Property(name = "Status Group")
    private String statusGroup; // 状态组

    @Property(name = "Status Date")
    private String statusDate; // 状态日期

    @Property(name = "Latest Label Date")
    private String latestLabelDate; // 最新标签日期

    @Property(name = "Company Number")
    private String companyNumber; // 公司编号

    @Property(name = "Restricted Use Reason")
    private String restrictedUseReason; // 限制使用原因

    @Property(name = "Pesticide Type")
    private String pesticideType; // 农药类型

    @Property(name = "Use Type")
    private String useType; // 使用类型

    @Property(name = "Use Pattern")
    private String usePattern; // 使用模式

    @Property(name = "Physical Form")
    private String physicalForm; // 物理形态

    @Property(name = "Signal Word")
    private String signalWord; // 信号词

    @Property(name = "Restricted Use Flag")
    private String restrictedUseFlag; // 限制使用标志

    @Property(name = "Record View")
    private String recordView; // 记录视图

    @Property(name = "Transfer History")
    private String transferHistory; // 转移历史

    @Property(name = "Me-Too Flag")
    private String meTooFlag; // Me-Too标志

    @Property(name = "Me-Too References")
    private String meTooReferences; // Me-Too参考

    @Property(name = "PM Team")
    private String pmTeam; // 项目管理团队

    @Property(name = "PM Email")
    private String pmEmail; // 项目管理电子邮件

    @Property(name = "Sort by Reg #")
    private String sortByRegNumber; // 按注册号排序

    @Property(name = "EPA PC Code/CAS Number")
    private String epaPcCodeOrCasNumber; // EPA PC代码或CAS编号

    //----------------------------------------------------------------
    /*荷兰*/
    @Property(name = "Admission type")
    private String admissionType; // 申请类型

    @Property(name = "Last w encodings")
    private String lastWEncodings; // 最近的W编码

    @Property(name = "End-of-life last W encoding")
    private String endOfLifeLastWEncoding; // 终止生命周期的最后W编码

    @Property(name = "Delivery time last w-coding")
    private String deliveryTimeLastWEncoding; // 最近的W编码的交付时间

    @Property(name = "Use")
    private String use; // 使用方式

    @Property(name = "Use by application")
    private String useByApplication; // 按应用程序使用

    @Property(name = "DTG Version")
    private String dtgVersion; // DTG版本

    @Property(name = "Application Locations")
    private String applicationLocations; // 应用程序位置

    @Property(name = "Growth stage")
    private String growthStage; // 生长阶段

    @Property(name = "Number of applications per 12 months")
    private String numberOfApplicationsPer12Months; // 每12个月的申请次数

    @Property(name = "Maximum agent dose per crop season")
    private String maximumAgentDosePerCropSeason; // 每个作物季节的最大剂量

    @Property(name = "Water volume scale")
    private String waterVolumeScale; // 水量规模

    @Property(name = "Safety term")
    private String safetyTerm; // 安全术语

    @Property(name = "Comments")
    private String comments; // 注释

    @Property(name = "MAP")
    private String map; // MAP

    @Property(name = "Maternal authorisation")
    private String maternalAuthorisation; // 母体授权

    @Property(name = "Minor application")
    private String minorApplication; // 次要应用

    @Property(name = "Water volume depending on crop height")
    private String waterVolumeDependingOnCropHeight; // 根据作物高度的水量

    @Property(name = "Seed density at seed treatment (kg/ha)")
    private String seedDensityAtSeedTreatment; // 种子处理时的种子密度（kg/ha）

    //-------------------------------------------------------------------------------
    /*台湾*/
    @Property(name = "Brand name") // 品牌名称
    private String brandName;

    @Property(name = "delivery mechanism of a medicine") // 药物递送机制
    private String deliveryMechanism;

    @Property(name = "UP") // UP
    private String up;

    @Property(name = "hybrid") // 杂交
    private String hybrid;

    @Property(name = "Overseas Original Manufacturer") // 海外原始制造商
    private String overseasOriginalManufacturer;

    @Property(name = "note") // 备注
    private String note;

    @Property(name = "labeling file") // 标签文件
    private String labelingFile;

    @Property(name = "barcode") // 条形码
    private String barcode;

    @Property(name = "quantitative") // 定量
    private String quantitative;

    @Property(name = "Container material") // 容器材料
    private String containerMaterial;

    @Property(name = "Dosage per hectare per application") // 每公顷每次应用剂量
    private String dosagePerHectare;

    @Property(name = "dilution factor") // 稀释因子
    private String dilutionFactor;

    @Property(name = "Safe Harvesting Period") // 安全采收期
    private String safeHarvestingPeriod;

    @Property(name = "caveat") // 警告
    private String caveat;

    @Property(name = "clarification") // 澄清
    private String clarification;

    @Property(name = "Date of approval") // 批准日期
    private String dateOfApproval;

    @Property(name = "Original registered manufacturer's name") // 原注册制造商名称
    private String originalRegisteredManufacturerName;


    //-----------------------------------------------------------------------------
    /*新西兰*/
    @Property(name = "NZ Agent Name") // 新西兰代理名称
    private String nzAgentName;

    @Property(name = "Condition ID") // 条件 ID
    private String conditionId;



}

