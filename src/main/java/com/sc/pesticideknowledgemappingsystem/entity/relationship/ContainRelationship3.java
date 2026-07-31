package com.sc.pesticideknowledgemappingsystem.entity.relationship;

import com.sc.pesticideknowledgemappingsystem.entity.node.*;
import lombok.Builder;
import lombok.Data;
import org.neo4j.ogm.annotation.*;

@RelationshipEntity(type = "INCLUDES")
@Data
@Builder
public class ContainRelationship3 {
    @Id
    @GeneratedValue
    private Long id;

    @StartNode
    private ActiveSubstance ActiveSubstance;

    @EndNode
    private Pesticide Pesticide;
}
