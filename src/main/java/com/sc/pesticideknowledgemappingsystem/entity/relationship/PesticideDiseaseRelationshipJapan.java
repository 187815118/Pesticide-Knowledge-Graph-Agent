package com.sc.pesticideknowledgemappingsystem.entity.relationship;

import com.sc.pesticideknowledgemappingsystem.entity.node.Disease;
import com.sc.pesticideknowledgemappingsystem.entity.node.Pesticide;
import lombok.Builder;
import lombok.Data;
import org.neo4j.ogm.annotation.*;

@RelationshipEntity(type = "予防と治療")
@Data
@Builder
public class PesticideDiseaseRelationshipJapan {
    @Id
    @GeneratedValue
    private Long id; // 关系节点的唯一标识符

    @StartNode
    private Pesticide Pesticide; // 农药节点

    @EndNode
    private Disease Disease; // 病害节点

//    @Property(name = "dilutionRatio")
//    private String dilutionRatio; // 稀释倍数
//
//    @Property(name = "applicationVolume")
//    private String applicationVolume; // 使用液量
//
//    @Property(name = "applicationPeriod")
//    private String applicationPeriod; // 使用时期
//
//    @Property(name = "usageCount")
//    private String usageCount; // 本剂的使用回数
//
//    @Property(name = "applicationMethod")
//    private String applicationMethod; // 使用方法
//
//    @Property(name = "totalUsageCount")
//    private String totalUsageCount; // 农药的总使用回数

}