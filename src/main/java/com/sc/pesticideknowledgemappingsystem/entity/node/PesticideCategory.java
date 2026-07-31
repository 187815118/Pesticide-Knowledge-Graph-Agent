package com.sc.pesticideknowledgemappingsystem.entity.node;

import lombok.Builder;
import lombok.Data;
import org.neo4j.ogm.annotation.GeneratedValue;
import org.neo4j.ogm.annotation.Id;
import org.neo4j.ogm.annotation.NodeEntity;
import org.neo4j.ogm.annotation.Property;

@NodeEntity(label = "PesticideCategory")
@Data
@Builder
public class PesticideCategory {
    @Id
    @GeneratedValue
    private Long id; // 农药大类节点的唯一标识符

    @Property(name = "name")
    private String name;
}

