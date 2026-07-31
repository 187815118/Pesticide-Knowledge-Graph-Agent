package com.sc.pesticideknowledgemappingsystem.entity.node;

import lombok.Builder;
import lombok.Data;
import org.neo4j.ogm.annotation.GeneratedValue;
import org.neo4j.ogm.annotation.Id;
import org.neo4j.ogm.annotation.NodeEntity;
import org.neo4j.ogm.annotation.Property;

@NodeEntity(label = "Disease")
@Data
@Builder
public class Disease {
    @Id
    @GeneratedValue
    private Long id; // 病害节点的唯一标识符

    @Property(name = "name")
    private String name;

    @Property(name = "latinname")
    private String LatinName;

    @Property(name = "Disease and Pest Alias")
    private String diseaseAndPestAlias; // 病害和害虫别名

    @Property(name = "Disease and Pest Infestation Images")
    private String diseaseAndPestInfestationImages; // 病害和害虫侵染图像

    @Property(name = "Symptoms of infestation")
    private String symptomsOfInfestation; // 侵染的症状

    @Property(name = "pathogen")
    private String pathogen; // 病原体

    @Property(name = "Transmission routes and pathogenic conditions")
    private String transmissionRoutesAndPathogenicConditions; // 传播途径和致病条件

    @Property(name = "regular pattern of occurrence")
    private String regularPatternOfOccurrence; // 发生的规律性

    @Property(name = "morphological characteristics")
    private String morphologicalCharacteristics; // 形态特征

    @Property(name = "geographic distribution")
    private String geographicDistribution; // 地理分布

    @Property(name = "host (of a parasite)")
    private String host; // 寄生虫的宿主

    @Property(name = "Methods of prevention and treatment")
    private String methodsOfPreventionAndTreatment; // 预防和治疗的方法

    @Property(name = "Others")
    private String others; // 其他信息


}

