package com.sc.pesticideknowledgemappingsystem.entity.node;

import org.neo4j.ogm.annotation.NodeEntity;
import org.neo4j.ogm.annotation.GeneratedValue;
import org.neo4j.ogm.annotation.Id;
import lombok.Builder;
import lombok.Data;
import org.neo4j.ogm.annotation.Property;

@NodeEntity(label = "ModeOfAction")
@Data
@Builder
public class ModeOfAction {
    @Id
    @GeneratedValue
    private Long id;

    @Property(name = "name")
    private String name; // 作用方式名称

    @Property(name = "MOA")
    private String moa; // 作用机制（Mode of Action）

    @Property(name = "TARGET SITE AND CODE")
    private String targetSiteAndCode; // 目标位点及代码

    @Property(name = "GROUP NAME")
    private String groupName; // 组名

    @Property(name = "CHEMICAL OR BIOLOGICAL GROUP")
    private String chemicalOrBiologicalGroup; // 化学或生物组
}
