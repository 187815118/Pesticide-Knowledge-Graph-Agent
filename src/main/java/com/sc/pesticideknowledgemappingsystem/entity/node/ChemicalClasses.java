package com.sc.pesticideknowledgemappingsystem.entity.node;

import org.neo4j.ogm.annotation.NodeEntity;
import org.neo4j.ogm.annotation.GeneratedValue;
import org.neo4j.ogm.annotation.Id;
import lombok.Builder;
import lombok.Data;
import org.neo4j.ogm.annotation.Property;

@NodeEntity(label = "ChemicalClasses")
@Data
@Builder
public class ChemicalClasses {  //化学物质分类
    @Id
    @GeneratedValue
    private Long id;

    @Property(name = "name")// Neo4j 节点的属性"name"
    private String name; //这个字段在 Neo4j 中将被存储为 "name"
}
