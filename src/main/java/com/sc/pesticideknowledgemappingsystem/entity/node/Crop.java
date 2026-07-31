package com.sc.pesticideknowledgemappingsystem.entity.node;

import lombok.Builder;
import lombok.Data;
import org.neo4j.ogm.annotation.GeneratedValue;
import org.neo4j.ogm.annotation.Id;
import org.neo4j.ogm.annotation.NodeEntity;
import org.neo4j.ogm.annotation.Property;

@NodeEntity(label = "Crop")
@Data
@Builder
public class Crop {
    @Id
    @GeneratedValue
    private Long id; // 作物节点的唯一标识符

    @Property(name = "name")
    private String name; // 作物的名称
}

