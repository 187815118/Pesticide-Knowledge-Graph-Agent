package com.sc.pesticideknowledgemappingsystem.entity.relationship;

import com.sc.pesticideknowledgemappingsystem.entity.node.ActiveSubstance;
import com.sc.pesticideknowledgemappingsystem.entity.node.ChemicalClasses;
import lombok.Builder;
import lombok.Data;
import org.neo4j.ogm.annotation.*;

@RelationshipEntity(type = "INCLUDES")
@Data
@Builder
public class ContainRelationship2 {
    @Id
    @GeneratedValue
    private Long id;

    @StartNode
    private ChemicalClasses ChemicalClasses;//化学物质

    @EndNode
    private ActiveSubstance ActiveSubstance;//具体类型名称"无机铜生物杀剂"
}
