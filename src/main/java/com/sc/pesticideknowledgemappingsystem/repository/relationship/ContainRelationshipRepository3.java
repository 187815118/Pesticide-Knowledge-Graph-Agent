package com.sc.pesticideknowledgemappingsystem.repository.relationship;


import com.sc.pesticideknowledgemappingsystem.entity.relationship.ContainRelationship3;
import org.springframework.data.neo4j.annotation.Query;
import org.springframework.data.neo4j.repository.Neo4jRepository;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ContainRelationshipRepository3 extends Neo4jRepository<ContainRelationship3, Long> {

    @Query("MATCH (n:ActiveSubstance {name: $activeSubstanceName})-[r:INCLUDES]->(m:Pesticide) RETURN n,m,r")
    List<ContainRelationship3> findRelationshipsByActiveSubstanceName(@Param("activeSubstanceName") String activeSubstanceName);

    /**
     * 根据剂型名查询关系3
     *
     * @param pesticideName 剂型名
     * @return 包含关系3的实体对象
     */
    @Query("MATCH p=()-[r:INCLUDES]->(pesticide:Pesticide {name: $pesticideName}) RETURN p LIMIT 25")
    List<ContainRelationship3> findRelationshipsByPesticideName(@Param("pesticideName") String pesticideName);

    @Query("MATCH (activeSubstance:ActiveSubstance {name: $activeSubstanceName})-[r:INCLUDES]->(pesticideName:Pesticide {name: $pesticideName}) " +
            "RETURN activeSubstance, pesticideName, r")
//        根据具体类型名和剂型名查询关系3
    ContainRelationship3 findRelationshipsByActiveSubstanceNameAndPesticideName(@Param("activeSubstanceName") String activeSubstanceName, @Param("pesticideName") String pesticideName);

}