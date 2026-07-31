package com.sc.pesticideknowledgemappingsystem.entity.relationship;

import com.sc.pesticideknowledgemappingsystem.entity.node.Crop;
import com.sc.pesticideknowledgemappingsystem.entity.node.Pesticide;
import lombok.Builder;
import lombok.Data;
import org.neo4j.ogm.annotation.*;

@RelationshipEntity(type = "係る")
@Data
@Builder
public class PesticideCropRelationshipJapan {
    @Id
    @GeneratedValue
    private Long id; // 关系节点的唯一标识符

    @StartNode
    private Pesticide Pesticide; // 农药节点

    @EndNode
    private Crop Crop; // 作物节点

}