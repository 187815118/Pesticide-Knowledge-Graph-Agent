package com.sc.pesticideknowledgemappingsystem.entity.relationship;

import com.sc.pesticideknowledgemappingsystem.entity.node.ModeOfAction;
import com.sc.pesticideknowledgemappingsystem.entity.node.ChemicalClasses;
import com.sc.pesticideknowledgemappingsystem.entity.node.PesticideCategory;
import lombok.Builder;
import lombok.Data;
import org.neo4j.ogm.annotation.*;

@RelationshipEntity(type = "INCLUDES")//注解，表示这个类是一个关系类。关系的名称是 "contain_1"。
@Data
@Builder
public class ContainRelationship {
    @Id
    @GeneratedValue
    private Long id;

    @StartNode
    private PesticideCategory PesticideCategory;//作用功能，保护性杀菌剂、系统性杀菌剂

    @EndNode
    private ChemicalClasses ChemicalClasses;//化学物质
}
