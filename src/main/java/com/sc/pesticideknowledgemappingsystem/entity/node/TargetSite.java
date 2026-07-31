package com.sc.pesticideknowledgemappingsystem.entity.node;

import org.neo4j.ogm.annotation.NodeEntity;
import org.neo4j.ogm.annotation.GeneratedValue;
import org.neo4j.ogm.annotation.Id;
import lombok.Builder;
import lombok.Data;
import org.neo4j.ogm.annotation.Property;

@NodeEntity(label = "TargetSite")
@Data
@Builder
public class TargetSite {
    @Id
    @GeneratedValue
    private Long id;

    @Property(name = "name")
    private String name; // 具体类型名称
}
