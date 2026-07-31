package com.sc.pesticideknowledgemappingsystem.entity.relationship;

import com.sc.pesticideknowledgemappingsystem.entity.node.Crop;
import com.sc.pesticideknowledgemappingsystem.entity.node.Disease;
import lombok.Builder;
import lombok.Data;
import org.neo4j.ogm.annotation.*;

@RelationshipEntity(type = "INFECTS")
@Data
@Builder
public class DiseaseRelationship {
    @Id
    @GeneratedValue
    private Long id;

    @StartNode
    private Disease Disease;

    @EndNode
    private Crop Crop;
}

