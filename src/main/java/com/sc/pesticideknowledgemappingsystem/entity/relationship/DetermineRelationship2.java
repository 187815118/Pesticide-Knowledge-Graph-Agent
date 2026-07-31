package com.sc.pesticideknowledgemappingsystem.entity.relationship;

import com.sc.pesticideknowledgemappingsystem.entity.node.ChemicalClasses;
import com.sc.pesticideknowledgemappingsystem.entity.node.*;
import lombok.Builder;
import lombok.Data;
import org.neo4j.ogm.annotation.*;


@RelationshipEntity(type = "DETERMINES")
@Data
@Builder
public class DetermineRelationship2 {
    @Id
    @GeneratedValue
    private Long id;

    @StartNode
    private ChemicalClasses TargetSite;

    @EndNode
    private ModeOfAction ModeOfAction;
}
